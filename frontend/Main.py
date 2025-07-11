import streamlit as st
import time
from datetime import datetime

from config import settings
from components.auth import check_authentication, show_login_screen, show_user_info, require_auth, update_activity
from components.api_client import api_client
import ssl
import requests
import urllib3

# Disable all SSL warnings
urllib3.disable_warnings()

# Create unverified context
ssl._create_default_https_context = ssl._create_unverified_context

# Set environment variables
import os
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

CAMBRIDGE_LOGO_URL = "./media/cambridge-logo.png"
INFOSYS_LOGO_URL = "./media/infosys-logo.png"

# Page configuration
st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout=settings.layout,
    initial_sidebar_state=settings.sidebar_state,
    menu_items={
        'Get Help': None,
        'Report a bug': None,
        'About': f"# {settings.app_title}\nYour gateway to cosmology research environments"
    }
)

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.image(CAMBRIDGE_LOGO_URL, width=120)

with col3:
    st.image(INFOSYS_LOGO_URL, width=120) 

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        margin-bottom: 2rem;
    }
    .welcome-card {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        padding: 2rem;
        border-radius: 1rem;
        color: white;
        text-align: center;
        margin: 2rem 0;
    }
    .nav-info {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    
    /* Fix for main page name in sidebar */
    .css-pkbazv {
        display: none;
    }
    
    /* Style sidebar navigation */
    .css-1d391kg {
        padding-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main page - Landing/Welcome page for multi-page app"""
    # Check authentication 
    if not check_authentication():
        show_login_screen()
        return
    
    # Show authenticated interface
    show_main_page()

@require_auth
def show_main_page():
    """Main landing page for the multi-page application"""
    # Clear only specific page-related session state (preserve auth and config)
    page_keys_to_clear = ['main_temp_data']
    for key in page_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.empty()
    
    # Update activity timestamp
    update_activity()
    
    # Send heartbeat to keep session alive (every 5 minutes)
    last_heartbeat = st.session_state.get("last_heartbeat", 0)
    if time.time() - last_heartbeat > 300:  # 5 minutes
        send_heartbeat()
    
    # Header
    st.markdown(f"""
    <div class="main-header">
        <h1>{settings.app_icon} {settings.app_title}</h1>
        <p>Multi-tenant Streamlit Platform for Cosmology Research</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Sidebar with user info
    show_user_info()
    
    # Auto-refresh mechanism
    setup_auto_refresh()
    
    # Main content for landing page
    show_welcome_content()

def setup_auto_refresh():
    """Setup auto-refresh functionality with proper caching"""
    with st.sidebar:
        st.markdown("---")
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=False)
        
        if auto_refresh and "last_refresh" not in st.session_state:
            st.session_state.last_refresh = time.time()
        
        if auto_refresh:
            current_time = time.time()
            if current_time - st.session_state.get("last_refresh", 0) > 30:
                st.session_state.last_refresh = current_time
                # Clear cache to prevent data stacking
                clear_all_cache()
                st.rerun()

def clear_all_cache():
    """Clear all cached data to prevent stacking"""
    # Clear any cached functions if they exist
    cache_keys = [key for key in st.session_state.keys() if key.startswith('cache_')]
    for key in cache_keys:
        del st.session_state[key]

def send_heartbeat():
    """Send heartbeat to keep session alive"""
    try:
        if st.session_state.get("authenticated"):
            api_client.send_heartbeat()
            st.session_state.last_heartbeat = time.time()
    except Exception:
        pass  # Silently fail to avoid disrupting UI

def show_welcome_content():
    """Main welcome/landing page content"""
    # Welcome section
    st.markdown("""
    <div class="welcome-card">
        <h2>CMBAgent</h2>
        <p>Your gateway to cosmology research environments</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Quick navigation info
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="nav-info">
            <h4>📊 Dashboard</h4>
            <p>View your environment overview, metrics, and quick stats</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="nav-info">
            <h4>🚀 Environment</h4>
            <p>Manage your research environments, launch new instances</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="nav-info">
            <h4>⚙️ Settings</h4>
            <p>Configure your profile, preferences, and system settings</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Quick actions
    st.markdown("### 🚀 Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("📊 Go to Dashboard", type="primary", use_container_width=True, key="main_go_dashboard"):
            st.switch_page("pages/Dashboard.py")
    
    with col2:
        if st.button("🚀 Manage Environments", use_container_width=True, key="main_go_environment"):
            st.switch_page("pages/Environment.py")
    
    with col3:
        if st.button("⚙️ Open Settings", use_container_width=True, key="main_go_settings"):
            st.switch_page("pages/Settings.py")
    
    with col4:
        if st.button("🔍 Diagnostics", use_container_width=True, key="main_go_diagnostics"):
            st.switch_page("pages/Diagnostics.py")
    
    # System status
    st.markdown("### 📈 System Status")
    
    try:
        # Get basic status without detailed caching
        status_data = api_client.get_environment_status()
        
        col1, col2 = st.columns(2)
        
        with col1:
            if status_data.get("active"):
                st.success("✅ Environment Active")
                st.info("You have an active research environment running")
            else:
                st.warning("❌ No Active Environment")
                st.info("Launch an environment to get started")
        
        with col2:
            # Quick stats
           
            if status_data.get("active"):
                st.metric("Environment Status", "Running")
            else:
                st.metric("Environment Status", "Inactive")
                
    except Exception as e:
        st.error("Unable to fetch system status")
    
    # Recent activity placeholder
    st.markdown("### 📋 Recent Activity")
    st.info("Navigate to Dashboard for detailed activity logs and metrics")

if __name__ == "__main__":
    main()
