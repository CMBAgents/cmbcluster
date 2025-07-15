import sqlite3
import asyncio
import threading
import structlog
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
from contextlib import asynccontextmanager
from pathlib import Path

from models import User, Environment, ActivityLog, UserRole, PodStatus
from config import settings

logger = structlog.get_logger()

class DatabaseManager:
    """SQLite database manager for CMBCluster with thread-safe operations"""
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or settings.database_path
        self._lock = threading.RLock()
        self._initialized = False
        self._init_database()
    
    def _init_database(self):
        """Initialize database with required tables"""
        if self._initialized:
            return
            
        # Ensure directory exists
        db_dir = Path(self.db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)
        
        with self._lock:
            try:
                conn = sqlite3.connect(self.db_path, timeout=30.0)
                conn.execute("PRAGMA journal_mode=WAL")  # Enable WAL mode for better concurrency
                conn.execute("PRAGMA synchronous=NORMAL")  # Balance between safety and performance
                conn.execute("PRAGMA temp_store=memory")  # Store temp tables in memory
                conn.execute("PRAGMA mmap_size=268435456")  # 256MB memory map
                
                # Create users table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS users (
                        id TEXT PRIMARY KEY,
                        email TEXT UNIQUE NOT NULL,
                        name TEXT NOT NULL,
                        role TEXT NOT NULL DEFAULT 'user',
                        created_at TIMESTAMP NOT NULL,
                        last_login TIMESTAMP,
                        is_active BOOLEAN NOT NULL DEFAULT 1,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create environments table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS environments (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        user_email TEXT NOT NULL,
                        env_id TEXT NOT NULL,
                        pod_name TEXT NOT NULL,
                        status TEXT NOT NULL,
                        url TEXT,
                        created_at TIMESTAMP NOT NULL,
                        last_activity TIMESTAMP,
                        resource_config TEXT,  -- JSON string
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create activity_logs table
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS activity_logs (
                        id TEXT PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        action TEXT NOT NULL,
                        details TEXT,
                        timestamp TIMESTAMP NOT NULL,
                        status TEXT NOT NULL DEFAULT 'success',
                        ip_address TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (user_id) REFERENCES users (id)
                    )
                """)
                
                # Create indexes for better query performance
                conn.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users (email)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_user_id ON environments (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_env_id ON environments (env_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_environments_status ON environments (status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_user_id ON activity_logs (user_id)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_activity_logs_timestamp ON activity_logs (timestamp)")
                
                conn.commit()
                conn.close()
                
                self._initialized = True
                logger.info("Database initialized successfully", db_path=self.db_path)
                
            except Exception as e:
                logger.error("Failed to initialize database", error=str(e), db_path=self.db_path)
                raise
    
    @asynccontextmanager
    async def get_connection(self):
        """Get a database connection with proper resource management"""
        conn = None
        try:
            # Create connection in the executor thread to avoid SQLite threading issues
            def create_connection():
                connection = sqlite3.connect(self.db_path, timeout=30.0, check_same_thread=False)
                connection.row_factory = sqlite3.Row  # Enable named column access
                return connection
            
            conn = await asyncio.get_event_loop().run_in_executor(None, create_connection)
            yield conn
        except Exception as e:
            logger.error("Database connection error", error=str(e))
            raise
        finally:
            if conn:
                await asyncio.get_event_loop().run_in_executor(None, conn.close)
    
    # User management methods
    async def create_user(self, user: User) -> User:
        """Create a new user"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT OR REPLACE INTO users 
                    (id, email, name, role, created_at, last_login, is_active, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (user.id, user.email, user.name, user.role.value, 
                     user.created_at.isoformat(), 
                     user.last_login.isoformat() if user.last_login else None,
                     user.is_active)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info("User created/updated", user_id=user.id, email=user.email)
            return user
    
    async def get_user(self, user_id: str) -> Optional[User]:
        """Get user by ID"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM users WHERE id = ?", (user_id,)
                ).fetchone()
            )
            
            if row:
                return User(
                    id=row['id'],
                    email=row['email'],
                    name=row['name'],
                    role=UserRole(row['role']),
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_login=datetime.fromisoformat(row['last_login']) if row['last_login'] else None,
                    is_active=bool(row['is_active'])
                )
            return None
    
    async def update_user_login(self, user_id: str) -> None:
        """Update user's last login timestamp"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE users SET last_login = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (datetime.utcnow().isoformat(), user_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    # Environment management methods
    async def create_environment(self, environment: Environment) -> Environment:
        """Create a new environment"""
        async with self.get_connection() as conn:
            resource_config_json = json.dumps(environment.resource_config) if environment.resource_config else None
            
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO environments 
                    (id, user_id, user_email, env_id, pod_name, status, url, 
                     created_at, last_activity, resource_config, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (environment.id, environment.user_id, environment.user_email,
                     environment.env_id, environment.pod_name, environment.status.value,
                     environment.url, environment.created_at.isoformat(),
                     environment.last_activity.isoformat() if environment.last_activity else None,
                     resource_config_json)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            logger.info("Environment created", env_id=environment.id, user_id=environment.user_id)
            return environment
    
    async def get_user_environments(self, user_id: str) -> List[Environment]:
        """Get all environments for a user"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM environments WHERE user_id = ? ORDER BY created_at DESC",
                    (user_id,)
                ).fetchall()
            )
            
            environments = []
            for row in rows:
                resource_config = json.loads(row['resource_config']) if row['resource_config'] else {}
                env = Environment(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_email=row['user_email'],
                    env_id=row['env_id'],
                    pod_name=row['pod_name'],
                    status=PodStatus(row['status']),
                    url=row['url'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                    resource_config=resource_config
                )
                environments.append(env)
            
            return environments
    
    async def get_environment(self, user_id: str, env_id: str) -> Optional[Environment]:
        """Get specific environment by user_id and env_id"""
        async with self.get_connection() as conn:
            row = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "SELECT * FROM environments WHERE user_id = ? AND env_id = ?",
                    (user_id, env_id)
                ).fetchone()
            )
            
            if row:
                resource_config = json.loads(row['resource_config']) if row['resource_config'] else {}
                return Environment(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_email=row['user_email'],
                    env_id=row['env_id'],
                    pod_name=row['pod_name'],
                    status=PodStatus(row['status']),
                    url=row['url'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                    resource_config=resource_config
                )
            return None
    
    async def update_environment_status(self, env_id: str, status: PodStatus) -> None:
        """Update environment status"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE environments SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE env_id = ?",
                    (status.value, env_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def update_environment_activity(self, user_id: str) -> None:
        """Update last activity for all user environments"""
        async with self.get_connection() as conn:
            now = datetime.utcnow().isoformat()
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "UPDATE environments SET last_activity = ?, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?",
                    (now, user_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def delete_environment(self, user_id: str, env_id: str) -> bool:
        """Delete environment"""
        async with self.get_connection() as conn:
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM environments WHERE user_id = ? AND env_id = ?",
                    (user_id, env_id)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            deleted = cursor.rowcount > 0
            if deleted:
                logger.info("Environment deleted", user_id=user_id, env_id=env_id)
            return deleted
    
    async def get_stale_environments(self, max_inactive_hours: int) -> List[Environment]:
        """Get environments that have been inactive for too long"""
        async with self.get_connection() as conn:
            cutoff_time = datetime.utcnow().timestamp() - (max_inactive_hours * 3600)
            
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    SELECT * FROM environments 
                    WHERE last_activity < ? AND status IN ('running', 'pending')
                    """,
                    (datetime.fromtimestamp(cutoff_time).isoformat(),)
                ).fetchall()
            )
            
            environments = []
            for row in rows:
                resource_config = json.loads(row['resource_config']) if row['resource_config'] else {}
                env = Environment(
                    id=row['id'],
                    user_id=row['user_id'],
                    user_email=row['user_email'],
                    env_id=row['env_id'],
                    pod_name=row['pod_name'],
                    status=PodStatus(row['status']),
                    url=row['url'],
                    created_at=datetime.fromisoformat(row['created_at']),
                    last_activity=datetime.fromisoformat(row['last_activity']) if row['last_activity'] else None,
                    resource_config=resource_config
                )
                environments.append(env)
            
            return environments
    
    # Activity logging methods
    async def log_activity(self, activity: ActivityLog) -> None:
        """Log user activity"""
        async with self.get_connection() as conn:
            await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    INSERT INTO activity_logs 
                    (id, user_id, action, details, timestamp, status, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (activity.id, activity.user_id, activity.action, activity.details,
                     activity.timestamp.isoformat(), activity.status, activity.ip_address)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
    
    async def get_user_activity(self, user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get user activity log"""
        async with self.get_connection() as conn:
            rows = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    """
                    SELECT action, details, timestamp, status 
                    FROM activity_logs 
                    WHERE user_id = ? 
                    ORDER BY timestamp DESC 
                    LIMIT ?
                    """,
                    (user_id, limit)
                ).fetchall()
            )
            
            return [
                {
                    "action": row['action'],
                    "details": row['details'],
                    "timestamp": row['timestamp'],
                    "status": row['status']
                }
                for row in rows
            ]
    
    async def cleanup_old_logs(self, days: int = 30) -> None:
        """Clean up old activity logs"""
        async with self.get_connection() as conn:
            cutoff_date = datetime.utcnow().timestamp() - (days * 24 * 3600)
            
            cursor = await asyncio.get_event_loop().run_in_executor(
                None,
                lambda: conn.execute(
                    "DELETE FROM activity_logs WHERE timestamp < ?",
                    (datetime.fromtimestamp(cutoff_date).isoformat(),)
                )
            )
            await asyncio.get_event_loop().run_in_executor(None, conn.commit)
            
            deleted_count = cursor.rowcount
            if deleted_count > 0:
                logger.info("Cleaned up old activity logs", deleted_count=deleted_count)

# Global database instance
db_manager: Optional[DatabaseManager] = None

def get_database() -> DatabaseManager:
    """Get the global database manager instance"""
    global db_manager
    if db_manager is None:
        db_manager = DatabaseManager()
    return db_manager
