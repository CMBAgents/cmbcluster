import asyncio
import structlog
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple
from database import get_database
from models import Environment, SubscriptionTier, PodStatus
from config import settings

logger = structlog.get_logger()

class AutoShutdownManager:
    """Manages automatic shutdown of environments based on uptime and subscription tiers"""
    
    def __init__(self):
        self.db = get_database()
        self.shutdown_warnings: Dict[str, datetime] = {}  # env_id -> warning_sent_time
    
    async def check_environments_for_shutdown(self) -> Dict[str, int]:
        """
        Check all running environments for auto-shutdown based on uptime and subscription
        Returns dict with shutdown statistics
        """
        logger.info("Running auto-shutdown check")
        
        stats = {
            "checked": 0,
            "warned": 0,
            "shutdown": 0,
            "skipped_subscribed": 0,
            "errors": 0
        }
        
        try:
            # Get all running environments
            running_environments = await self._get_running_environments()
            stats["checked"] = len(running_environments)
            
            logger.info("Found running environments for shutdown check", count=len(running_environments))
            
            for env_id, environment, user, uptime_minutes in running_environments:
                try:
                    action = await self._process_environment_for_shutdown(environment, user, uptime_minutes)
                    
                    if action == "shutdown":
                        stats["shutdown"] += 1
                    elif action == "warned":
                        stats["warned"] += 1
                    elif action == "skipped_subscribed":
                        stats["skipped_subscribed"] += 1
                        
                except Exception as e:
                    logger.error("Error processing environment for shutdown", 
                               env_id=env_id, 
                               user_id=environment.user_id,
                               error=str(e))
                    stats["errors"] += 1
            
            logger.info("Auto-shutdown check completed", stats=stats)
            return stats
            
        except Exception as e:
            logger.error("Error during auto-shutdown check", error=str(e))
            stats["errors"] += 1
            return stats
    
    async def _get_running_environments(self) -> List[Tuple[str, Environment, object, int]]:
        """Get all running environments with their users and uptime"""
        environments_data = []
        
        try:
            # We need to get environments by querying all users
            # Since we don't have a direct "get all environments" method,
            # we'll implement a basic version here
            
            # For now, let's create a method to get all environments
            # This is a temporary solution - in production you'd want a more efficient approach
            all_environments = await self.db.get_all_running_environments()
            
            for environment in all_environments:
                # Get user data
                user = await self.db.get_user(environment.user_id)
                if not user:
                    logger.warning("User not found for environment", 
                                 env_id=environment.env_id, 
                                 user_id=environment.user_id)
                    continue
                
                # Calculate uptime
                uptime_minutes = self._calculate_uptime_minutes(environment)
                
                environments_data.append((environment.env_id, environment, user, uptime_minutes))
            
            return environments_data
            
        except Exception as e:
            logger.error("Error getting running environments", error=str(e))
            return []
    
    async def _process_environment_for_shutdown(self, environment: Environment, user, uptime_minutes: int) -> str:
        """
        Process a single environment for potential shutdown
        Returns: 'shutdown', 'warned', 'skipped_subscribed', or 'no_action'
        """
        env_id = environment.env_id
        user_id = environment.user_id
        
        # Check if user is subscribed (exempt from auto-shutdown)
        if not self._should_auto_shutdown(user):
            logger.debug("Skipping auto-shutdown for subscribed user", 
                        user_id=user_id, 
                        env_id=env_id,
                        subscription_tier=getattr(user, 'subscription_tier', 'unknown'))
            return "skipped_subscribed"
        
        # Get user's max uptime limit
        max_uptime = self._get_max_uptime_minutes(user)
        
        # Check if environment should be shut down
        if uptime_minutes >= max_uptime:
            # Check if we already sent a warning
            warning_time = self.shutdown_warnings.get(env_id)
            
            if warning_time:
                # Warning was sent, check if grace period has passed
                grace_period_passed = datetime.utcnow() - warning_time >= timedelta(minutes=settings.grace_period_minutes)
                
                if grace_period_passed:
                    # Grace period passed, perform shutdown
                    await self._perform_shutdown(environment, user, uptime_minutes, "uptime_limit_exceeded")
                    # Clean up warning tracking
                    self.shutdown_warnings.pop(env_id, None)
                    return "shutdown"
                else:
                    logger.debug("Grace period not yet passed for environment", 
                               env_id=env_id, 
                               warning_sent=warning_time)
                    return "no_action"
            else:
                # No warning sent yet, send warning
                await self._send_shutdown_warning(environment, user, uptime_minutes, max_uptime)
                self.shutdown_warnings[env_id] = datetime.utcnow()
                return "warned"
        
        # Check if we should send an early warning
        elif uptime_minutes >= (max_uptime - settings.shutdown_warning_minutes):
            if env_id not in self.shutdown_warnings:
                await self._send_shutdown_warning(environment, user, uptime_minutes, max_uptime)
                self.shutdown_warnings[env_id] = datetime.utcnow()
                return "warned"
        
        return "no_action"
    
    def _should_auto_shutdown(self, user) -> bool:
        """Determine if user's environments should be subject to auto-shutdown"""
        subscription_tier = getattr(user, 'subscription_tier', 'free')
        auto_shutdown_enabled = getattr(user, 'auto_shutdown_enabled', True)
        
        # Subscribed users are exempt from auto-shutdown
        if subscription_tier != 'free':
            return False
        
        # User can disable auto-shutdown (future feature)
        if not auto_shutdown_enabled:
            return False
        
        return True
    
    def _get_max_uptime_minutes(self, user) -> int:
        """Get the maximum uptime allowed for a user"""
        # Check user-specific limit first
        max_uptime = getattr(user, 'max_uptime_minutes', None)
        if max_uptime is not None:
            return max_uptime
        
        # Fall back to subscription tier defaults
        subscription_tier = getattr(user, 'subscription_tier', 'free')
        
        if subscription_tier == 'free':
            return settings.free_tier_max_uptime_minutes
        else:
            # Subscribed users get unlimited uptime (represented as a very large number)
            return 24 * 60 * 365  # 1 year in minutes
    
    def _calculate_uptime_minutes(self, environment: Environment) -> int:
        """Calculate environment uptime in minutes"""
        if not environment.created_at:
            return 0
        
        uptime_delta = datetime.utcnow() - environment.created_at
        return int(uptime_delta.total_seconds() / 60)
    
    async def _send_shutdown_warning(self, environment: Environment, user, uptime_minutes: int, max_uptime: int):
        """Send warning about upcoming shutdown"""
        remaining_minutes = max_uptime - uptime_minutes
        
        logger.info("Sending shutdown warning", 
                   env_id=environment.env_id,
                   user_id=environment.user_id,
                   uptime_minutes=uptime_minutes,
                   max_uptime=max_uptime,
                   remaining_minutes=remaining_minutes)
        
        # Log the warning activity
        await self._log_shutdown_activity(
            environment.user_id,
            "shutdown_warning_sent",
            f"Environment {environment.env_id} will be shut down in {remaining_minutes} minutes (uptime: {uptime_minutes}min)"
        )
        
        # TODO: In the future, you could send actual notifications here
        # - WebSocket notification to frontend
        # - Email notification
        # - Slack notification
        # - Store warning in database for frontend to display
    
    async def _perform_shutdown(self, environment: Environment, user, uptime_minutes: int, reason: str):
        """Perform graceful shutdown of environment"""
        logger.info("Performing auto-shutdown", 
                   env_id=environment.env_id,
                   user_id=environment.user_id,
                   uptime_minutes=uptime_minutes,
                   reason=reason)
        
        try:
            # Import here to avoid circular imports
            import sys
            if 'main' in sys.modules:
                main_module = sys.modules['main']
                pod_manager = main_module.app_state.get("pod_manager")
            else:
                logger.error("Main module not available for auto-shutdown", env_id=environment.env_id)
                return
            
            if not pod_manager:
                logger.error("Pod manager not available for auto-shutdown", env_id=environment.env_id)
                return
            
            # Perform the shutdown
            await pod_manager.delete_user_environment(
                environment.user_id, 
                environment.user_email, 
                environment.env_id
            )
            
            # Log the shutdown activity
            await self._log_shutdown_activity(
                environment.user_id,
                "environment_auto_shutdown",
                f"Environment {environment.env_id} automatically shut down after {uptime_minutes} minutes (reason: {reason})"
            )
            
            logger.info("Auto-shutdown completed successfully", 
                       env_id=environment.env_id,
                       user_id=environment.user_id,
                       uptime_minutes=uptime_minutes)
            
        except Exception as e:
            logger.error("Failed to perform auto-shutdown", 
                        env_id=environment.env_id,
                        user_id=environment.user_id,
                        error=str(e))
            
            # Log the failure
            await self._log_shutdown_activity(
                environment.user_id,
                "environment_auto_shutdown_failed",
                f"Failed to auto-shutdown environment {environment.env_id}: {str(e)}"
            )
            raise
    
    async def _log_shutdown_activity(self, user_id: str, action: str, details: str):
        """Log shutdown-related activity"""
        try:
            # Import here to avoid circular imports
            import sys
            if 'main' in sys.modules:
                main_module = sys.modules['main']
                await main_module.log_activity(user_id, action, details)
            else:
                # Fallback: log directly to database
                from models import ActivityLog
                import time
                import uuid
                
                activity = ActivityLog(
                    id=f"{user_id}_{int(time.time())}_{uuid.uuid4().hex[:8]}",
                    user_id=user_id,
                    action=action,
                    details=details,
                    timestamp=datetime.utcnow(),
                    status="success"
                )
                
                await self.db.log_activity(activity)
                
        except Exception as e:
            logger.error("Failed to log shutdown activity", 
                        user_id=user_id, 
                        action=action,
                        error=str(e))
    
    def cleanup_warning_tracking(self):
        """Clean up old warning tracking data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=2)
        
        old_warnings = [env_id for env_id, warning_time in self.shutdown_warnings.items() 
                       if warning_time < cutoff_time]
        
        for env_id in old_warnings:
            self.shutdown_warnings.pop(env_id, None)
        
        if old_warnings:
            logger.debug("Cleaned up old shutdown warnings", count=len(old_warnings))

# Global instance
auto_shutdown_manager = None

def get_auto_shutdown_manager() -> AutoShutdownManager:
    """Get the global auto-shutdown manager instance"""
    global auto_shutdown_manager
    if auto_shutdown_manager is None:
        auto_shutdown_manager = AutoShutdownManager()
    return auto_shutdown_manager
