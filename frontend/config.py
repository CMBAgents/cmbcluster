import os
from dataclasses import dataclass

@dataclass
class Settings:
    """Frontend configuration settings"""
    api_url: str = os.getenv("API_URL", "http://localhost:8000")
    dev_mode: bool = os.getenv("DEV_MODE", "false").lower() == "true"
    base_domain: str = os.getenv("BASE_DOMAIN", "cmbcluster.local")
    app_title: str = "CMBCluster"
    app_icon: str = "🚀"
    
    # UI Settings
    sidebar_state: str = "expanded"
    layout: str = "wide"
    
    # API Endpoints
    @property
    def auth_login_url(self) -> str:
        return f"{self.api_url}/auth/login"
    
    @property
    def environments_url(self) -> str:
        return f"{self.api_url}/environments"
    
    @property
    def activity_url(self) -> str:
        return f"{self.api_url}/activity"
    
    @property
    def heartbeat_url(self) -> str:
        return f"{self.api_url}/environments/heartbeat"

settings = Settings()
