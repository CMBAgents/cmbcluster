import streamlit as st
import jwt
import time
from datetime import datetime
from typing import Optional, Dict
from ..config import settings

def check_authentication() -> bool:
    """Check if user is authenticated"""
    # Check for token in URL params (OAuth callback)
    query_params = st.query_params
    if "token" in query_params:
        token = query_params["token"]
        if validate_and_store_token(token):
            # Clear the token from URL
            st.query_params.clear()
            st.rerun()
    
    # Check existing session
    return st.session_state.get("authenticated", False)

def validate_and_store_token(token: str) -> bool:
    """Validate JWT token and store user info"""
    try:
        if settings.dev_mode:
            # Development mode - accept any token
            st.session_state.user_info = {
                "name": "Dev User",
                "email": "dev@cmbcluster.local",
                "sub": "dev-user-123"
            }
            st.session_state.access_token = token
            st.session_state.authenticated = True
            return True
        
        # Decode JWT token (skip signature verification for now)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check expiration
        if payload.get("exp") and payload["exp"] < time.time():
            return False
        
        # Store user info and token
        st.session_state.user_info = {
            "name": payload.get("name", "Unknown User"),
            "email": payload.get("email", "unknown@example.com"),
            "sub": payload.get("sub", "unknown")
        }
        st.session_state.access_token = token
        st.session_state.authenticated = True
        
        return True
        
    except Exception as e:
        st.error(f"Authentication error: {str(e)}")
        return False

def get_auth_headers() -> Dict[str, str]:
    """Get authentication headers for API requests"""
    token = st.session_state.get("access_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def logout():
    """Clear authentication session"""
    keys_to_clear = [
        "authenticated", "access_token", "user_info", 
        "environment_status", "activity_log"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]

def require_auth(func):
    """Decorator to require authentication"""
    def wrapper(*args, **kwargs):
        if not check_authentication():
            show_login_screen()
            st.stop()
        return func(*args, **kwargs)
    return wrapper

def show_login_screen():
    """Display login interface"""
    st.markdown("""
    <div style="text-align: center; padding: 2rem;">
        <h1>🚀 CMBCluster</h1>
        <h3>Multi-tenant Streamlit Platform</h3>
        <p>Please authenticate to access your research environment</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns([1, 2, 1])
    
    with col2:
        if st.button("🔐 Login with Google", type="primary", use_container_width=True):
            login_url = settings.auth_login_url
            st.markdown(f'<meta http-equiv="refresh" content="0;URL={login_url}">', 
                       unsafe_allow_html=True)
        
        # Development mode token input
        if settings.dev_mode:
            st.markdown("---")
            st.markdown("**Development Mode**")
            with st.expander("Manual Token Input"):
                dev_token = st.text_input("Access Token", type="password")
                if st.button("Authenticate") and dev_token:
                    if validate_and_store_token(dev_token):
                        st.success("Authentication successful!")
                        st.rerun()
                    else:
                        st.error("Invalid token")

def show_user_info():
    """Display user information in sidebar"""
    user_info = st.session_state.get("user_info", {})
    
    with st.sidebar:
        st.markdown("### 👤 User Profile")
        st.write(f"**Name:** {user_info.get('name', 'Unknown')}")
        st.write(f"**Email:** {user_info.get('email', 'Unknown')}")
        
        if st.button("🚪 Logout", use_container_width=True):
            logout()
            st.rerun()
