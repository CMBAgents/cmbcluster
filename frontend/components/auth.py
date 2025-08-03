import streamlit as st
import jwt
import time
from datetime import datetime, timedelta
from typing import Optional, Dict
from config import settings


def check_authentication() -> bool:
    """Check if user is authenticated with session timeout handling"""
    # Check for token in URL params (OAuth callback)
    query_params = st.query_params
    if "token" in query_params:
        token = query_params["token"]
        if validate_and_store_token(token):
            # Clear the token from URL
            st.query_params.clear()
            st.rerun()
    
    # Check existing session and token expiry
    if st.session_state.get("authenticated", False):
        # Check if token is still valid
        token_exp = st.session_state.get("token_expiry")
        if token_exp and datetime.now() > token_exp:
            st.warning("Session expired. Please login again.")
            logout()
            return False
        
        # Refresh token if needed (within 5 minutes of expiry)
        if token_exp and (token_exp - datetime.now()).total_seconds() < 300:
            try:
                refresh_token()
            except Exception:
                pass  # If refresh fails, continue with existing token
    
    return st.session_state.get("authenticated", False)

def validate_and_store_token(token: str) -> bool:
    """Validate JWT token and store user info with expiry tracking"""
    try:
        if settings.dev_mode:
            # Development mode - accept any token with long expiry
            st.session_state.user_info = {
                "name": "Dev User",
                "email": "dev@cmbcluster.local",
                "sub": "dev-user-123"
            }
            st.session_state.access_token = token
            st.session_state.authenticated = True
            st.session_state.token_expiry = datetime.now() + timedelta(hours=8)  # 8 hour session
            st.session_state.last_activity = datetime.now()
            return True
        
        # Decode JWT token (skip signature verification for now)
        payload = jwt.decode(token, options={"verify_signature": False})
        
        # Check expiration
        exp_timestamp = payload.get("exp")
        if exp_timestamp:
            exp_datetime = datetime.fromtimestamp(exp_timestamp)
            if exp_datetime < datetime.now():
                st.error("Token has expired. Please login again.")
                return False
            st.session_state.token_expiry = exp_datetime
        else:
            # No expiry in token, set default 8 hours
            st.session_state.token_expiry = datetime.now() + timedelta(hours=8)
        
        # Store user info and token
        st.session_state.user_info = {
            "name": payload.get("name", "Unknown User"),
            "email": payload.get("email", "unknown@example.com"),
            "sub": payload.get("sub", "unknown")
        }
        st.session_state.access_token = token
        st.session_state.authenticated = True
        st.session_state.last_activity = datetime.now()
        
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
    """Clear authentication session and all cached data"""
    keys_to_clear = [
        "authenticated", "access_token", "user_info", "token_expiry",
        "last_activity", "environment_status", "activity_log",
        "confirm_delete", "confirm_stop", "confirm_restart"
    ]
    for key in keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any cached data keys
    cache_keys = [key for key in st.session_state.keys() if key.startswith('cache_')]
    for key in cache_keys:
        del st.session_state[key]

def refresh_token():
    """Refresh authentication token to extend session"""
    try:
        # In a real implementation, this would call a refresh endpoint
        # For now, just extend the current session
        current_expiry = st.session_state.get("token_expiry")
        if current_expiry:
            st.session_state.token_expiry = current_expiry + timedelta(hours=2)
            st.session_state.last_activity = datetime.now()
    except Exception as e:
        # If refresh fails, don't interrupt the user experience
        pass

def update_activity():
    """Update last activity timestamp"""
    st.session_state.last_activity = datetime.now()

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
    # Completely clear the page and replace with login screen
    
    # Create a clean container that replaces all content
    container = st.container()
    
    with container:
        # Add CSS to ensure clean display and logo styling
        st.markdown("""
        <style>
        .main .block-container {
            padding: 2rem 1rem;
        }
        /* Make Cambridge logo text white by targeting the custom container */
        .cambridge-logo-container img {
            filter: invert(1) brightness(2.5) contrast(2) saturate(0) hue-rotate(180deg) !important;
            -webkit-filter: invert(1) brightness(2.5) contrast(2) saturate(0) hue-rotate(180deg) !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Logo section with better alignment (same as other pages)
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        
        with col1:
            # Add a custom class to identify Cambridge logo
            st.markdown('<div class="cambridge-logo-container">', unsafe_allow_html=True)
            st.image("./media/cambridge-logo.png", width=120)
            st.markdown('</div>', unsafe_allow_html=True)

        with col5:
            st.image("./media/infosys-logo.png", width=120)
        
        # Main login content
        st.markdown(f"""
        <div style="text-align: center; padding: 3rem 0;">
            <h1 style="color: #FFFFFF; margin-bottom: 1rem;">{settings.app_title}</h1>
            <h3 style="color: #B8B8B8; margin-bottom: 2rem;">{settings.app_tagline}</h3>
            <p style="color: #B8B8B8;">Coming soon</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Login button
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("Login with Google", type="primary", use_container_width=True, icon=":material/login:"):
                login_url = settings.auth_login_url
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={login_url}">', 
                           unsafe_allow_html=True)
            
            # Development mode token input
            if settings.dev_mode:
                st.markdown("---")
                st.markdown("**Development Mode**", help="For testing purposes only")
                with st.expander("Manual Token Input", icon=":material/code:"):
                    dev_token = st.text_input("Access Token", type="password")
                    if st.button("Authenticate", icon=":material/verified_user:") and dev_token:
                        if validate_and_store_token(dev_token):
                            st.success("Authentication successful!")
                            st.rerun()
                        else:
                            st.error("Invalid token")

def show_user_info():
    """Display user information in sidebar with session info"""
    user_info = st.session_state.get("user_info", {})
    
    with st.sidebar:
        st.markdown("### User Profile")
        st.write(f"**Name:** {user_info.get('name', 'Unknown')}")
        st.write(f"**Email:** {user_info.get('email', 'Unknown')}")
        
        # Show session info
        token_expiry = st.session_state.get("token_expiry")
        if token_expiry:
            time_left = token_expiry - datetime.now()
            if time_left.total_seconds() > 0:
                hours_left = int(time_left.total_seconds() // 3600)
                minutes_left = int((time_left.total_seconds() % 3600) // 60)
                
            else:
                st.caption("Session expired")
        
        # Extend session button if close to expiry
        if token_expiry and (token_expiry - datetime.now()).total_seconds() < 1800:  # 30 minutes
            if st.button("Extend Session", use_container_width=True, icon=":material/restart_alt:"):
                refresh_token()
                st.success("Session extended!")
                st.rerun()
        
        if st.button("Logout", use_container_width=True, icon=":material/logout:"):
            logout()
            st.rerun()
