import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from config import settings

class CMBClusterAPIClient:
    """API client for CMBCluster backend"""
    
    def __init__(self, base_url: str = None):
        self.base_url = (base_url or settings.api_url).rstrip('/')
        self.session = requests.Session()
        # Add timeout to prevent hanging requests
        self.session.timeout = 10
    
    def _get_headers(self) -> Dict[str, str]:
        """Get headers with authentication token"""
        headers = {"Content-Type": "application/json"}
        token = st.session_state.get("access_token")
        if token:
            headers["Authorization"] = f"Bearer {token}"
        return headers
    
    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """Handle API response and errors"""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            if response.status_code == 401:
                st.error("Authentication failed. Please login again.")
                st.session_state.authenticated = False
                raise e
            elif response.status_code == 403:
                st.error("Access denied. Insufficient permissions.")
                raise e
            elif response.status_code == 404:
                # For 404, return error response instead of empty response
                try:
                    error_data = response.json()
                    return {"status": "error", "message": error_data.get("detail", "Not found")}
                except:
                    return {"status": "error", "message": "Resource not found"}
            elif response.status_code == 500:
                try:
                    error_data = response.json()
                    return {"status": "error", "message": error_data.get("detail", "Server error")}
                except:
                    return {"status": "error", "message": "Server error. Please try again later."}
            else:
                try:
                    error_data = response.json()
                    return {"status": "error", "message": error_data.get("detail", f"API error: {response.status_code}")}
                except:
                    return {"status": "error", "message": f"API error: {response.status_code}"}
        except requests.exceptions.Timeout:
            return {"status": "error", "message": "Request timeout. Please check your connection."}
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Connection error. Please check if the backend is running."}
        except requests.exceptions.RequestException as e:
            return {"status": "error", "message": f"Network error: {str(e)}"}
    
    def create_environment(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new user environment"""
        url = f"{self.base_url}/environments"
        
        # Default config
        data = {
            "cpu_limit": 1.0,
            "memory_limit": "2Gi",
            "storage_size": "10Gi"  # Kept for backward compatibility
        }
        
        if config:
            data.update(config)
            
            # Handle storage selection conversion
            if 'storage' in config:
                storage_info = config['storage']
                
                if storage_info.get('selection_type') == 'existing':
                    # Use existing storage
                    data['storage_id'] = storage_info.get('storage_id')
                    data['create_new_storage'] = False
                elif storage_info.get('selection_type') == 'create_new':
                    # Create new storage
                    data['storage_id'] = None
                    data['create_new_storage'] = True
                    if 'storage_class' in storage_info:
                        data['storage_class'] = storage_info['storage_class']
                else:
                    # Default behavior - let backend handle it
                    data['storage_id'] = None
                    data['create_new_storage'] = False
                
                # Remove the frontend 'storage' key
                del data['storage']
        
        response = self.session.post(url, json=data, headers=self._get_headers(), timeout=30)
        return self._handle_response(response)
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get current environment status"""
        url = f"{self.base_url}/environments"
        response = self.session.get(url, headers=self._get_headers(), timeout=10)
        return self._handle_response(response)
    

    def delete_environment(self, env_id: str = None) -> Dict[str, Any]:
        """Delete user environment. If env_id is provided, delete that environment."""
        url = f"{self.base_url}/environments"
        params = {"env_id": env_id} if env_id else None
        
        response = self.session.delete(url, headers=self._get_headers(), params=params, timeout=20)
        return self._handle_response(response)
    
    def send_heartbeat(self) -> Dict[str, Any]:
        """Send heartbeat to keep environment alive"""
        url = f"{self.base_url}/environments/heartbeat"
        response = self.session.post(url, headers=self._get_headers(), timeout=5)
        return self._handle_response(response)
    
    def get_activity_log(self, limit: int = 50) -> Dict[str, Any]:
        """Get user activity log"""
        url = f"{self.base_url}/activity"
        params = {"limit": limit}
        response = self.session.get(url, params=params, headers=self._get_headers())
        return self._handle_response(response)
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        url = f"{self.base_url}/health"
        response = self.session.get(url)
        return self._handle_response(response)

    def list_environments(self) -> Dict[str, Any]:
        """List all environments for the current user"""
        url = f"{self.base_url}/environments/list"
        response = self.session.get(url, headers=self._get_headers())
        return self._handle_response(response)

    def get_environment_by_id(self, env_id: str) -> Dict[str, Any]:
        """Get specific environment status by ID"""
        environments = self.list_environments()
        if environments and "environments" in environments:
            for env in environments["environments"]:
                if env.get("id") == env_id or env.get("env_id") == env_id:
                    return {"active": True, "environment": env}
        return {"active": False, "environment": None}


    def stop_environment(self, env_id: str = None) -> Dict[str, Any]:
        """Stop user environment (graceful shutdown). If env_id is provided, stop that environment."""
        try:
            result = self.delete_environment(env_id=env_id)
            if result.get("status") == "deleted":
                return {"status": "success", "message": "Environment stopped successfully"}
            else:
                return {"status": "error", "message": f"Failed to stop environment: {result.get('message', 'Unknown error')}"}
        except Exception as e:
            return {"status": "error", "message": f"Error stopping environment: {str(e)}"}
    

    def restart_environment(self, env_id: str = None, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Restart user environment. If env_id is provided, restart that environment."""
        try:
            # First, try to stop the environment
            delete_result = self.delete_environment(env_id=env_id)
            if delete_result.get("status") != "deleted":
                return {"status": "error", "message": f"Failed to stop environment for restart: {delete_result.get('message', 'Unknown error')}"}
            
            # Wait a bit for cleanup
            import time
            time.sleep(3)  # Longer pause for proper cleanup
            
            # Create new environment
            create_result = self.create_environment(config)
            if create_result.get("status") in ["created", "existing"]:
                return {"status": "success", "message": "Environment restarted successfully", "environment": create_result}
            else:
                return {"status": "error", "message": f"Failed to create new environment: {create_result.get('message', 'Unknown error')}"}
                
        except Exception as e:
            return {"status": "error", "message": f"Error restarting environment: {str(e)}"}
    
    # Storage Management Methods
    def list_user_storages(self) -> Dict[str, Any]:
        """List all storage buckets for the current user"""
        try:
            response = self.session.get(
                f"{self.base_url}/storage/list",
                headers=self._get_headers(),
                verify=False
            )
            return self._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": f"Error listing storages: {str(e)}"}
    
    def get_storage_details(self, storage_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific storage bucket"""
        try:
            response = self.session.get(
                f"{self.base_url}/storage/{storage_id}",
                headers=self._get_headers(),
                verify=False
            )
            return self._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": f"Error getting storage details: {str(e)}"}
    
    def create_storage(self, storage_class: str = "STANDARD", custom_name: str = None) -> Dict[str, Any]:
        """Create a new storage bucket"""
        try:
            data = {"storage_class": storage_class}
            if custom_name:
                data["custom_name"] = custom_name
            
            response = self.session.post(
                f"{self.base_url}/storage/create",
                json=data,
                headers=self._get_headers(),
                verify=False
            )
            return self._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": f"Error creating storage: {str(e)}"}
    
    def delete_storage(self, storage_id: str, force: bool = False) -> Dict[str, Any]:
        """Delete a storage bucket"""
        try:
            body = {"operation": "delete", "force": force}
            response = self.session.request(
                method="DELETE",
                url=f"{self.base_url}/storage/{storage_id}",
                json=body,
                headers=self._get_headers(),
                verify=False
            )
            return self._handle_response(response)
        except Exception as e:
            return {"status": "error", "message": f"Error deleting storage: {str(e)}"}

# Global API client instance
api_client = CMBClusterAPIClient()
