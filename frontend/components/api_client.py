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
            elif response.status_code == 403:
                st.error("Access denied. Insufficient permissions.")
            elif response.status_code == 404:
                # Don't show error for 404, just return empty response
                return {"active": False, "environment": None}
            elif response.status_code == 500:
                st.error("Server error. Please try again later.")
            else:
                st.error(f"API error: {response.status_code}")
            raise e
        except requests.exceptions.Timeout:
            st.error("Request timeout. Please check your connection.")
            raise
        except requests.exceptions.ConnectionError:
            st.error("Connection error. Please check if the backend is running.")
            raise
        except requests.exceptions.RequestException as e:
            st.error(f"Network error: {str(e)}")
            raise e
    
    def create_environment(self, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Create a new user environment"""
        url = f"{self.base_url}/environments"
        data = config or {
            "cpu_limit": 1.0,
            "memory_limit": "2Gi",
            "storage_size": "10Gi"
        }
        
        # Debug logging
        print(f"DEBUG: create_environment called with config={config}")
        print(f"DEBUG: URL={url}, data={data}")
        print(f"DEBUG: Headers={self._get_headers()}")
        
        try:
            response = self.session.post(url, json=data, headers=self._get_headers(), timeout=30)
            print(f"DEBUG: Response status={response.status_code}")
            print(f"DEBUG: Response text={response.text}")
            return self._handle_response(response)
        except Exception as e:
            print(f"DEBUG: Exception in create_environment: {type(e).__name__}: {str(e)}")
            raise
    
    def get_environment_status(self) -> Dict[str, Any]:
        """Get current environment status"""
        url = f"{self.base_url}/environments"
        response = self.session.get(url, headers=self._get_headers(), timeout=10)
        return self._handle_response(response)
    

    def delete_environment(self, env_id: str = None) -> Dict[str, Any]:
        """Delete user environment. If env_id is provided, delete that environment."""
        url = f"{self.base_url}/environments"
        params = {"env_id": env_id} if env_id else None
        
        # Debug logging
        print(f"DEBUG: delete_environment called with env_id={env_id}")
        print(f"DEBUG: URL={url}, params={params}")
        print(f"DEBUG: Headers={self._get_headers()}")
        
        try:
            response = self.session.delete(url, headers=self._get_headers(), params=params, timeout=20)
            print(f"DEBUG: Response status={response.status_code}")
            print(f"DEBUG: Response text={response.text}")
            return self._handle_response(response)
        except Exception as e:
            print(f"DEBUG: Exception in delete_environment: {type(e).__name__}: {str(e)}")
            raise
    
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


    def stop_environment(self, env_id: str = None) -> Dict[str, Any]:
        """Stop user environment (graceful shutdown). If env_id is provided, stop that environment."""
        return self.delete_environment(env_id=env_id)
    

    def restart_environment(self, env_id: str = None, config: Optional[Dict] = None) -> Dict[str, Any]:
        """Restart user environment. If env_id is provided, restart that environment."""
        try:
            self.delete_environment(env_id=env_id)
            import time
            time.sleep(2)  # Brief pause between delete and create
            return self.create_environment(config)
        except Exception as e:
            return self.create_environment(config)

# Global API client instance
api_client = CMBClusterAPIClient()
