import streamlit as st
from datetime import datetime
import time

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth
from components.api_client import api_client

# Page configuration
st.set_page_config(
    page_title="Dashboard - CMBCluster",
    page_icon="🏠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
        margin: 0.5rem 0;
    }
    .status-active {
        background: linear-gradient(135deg, #56ab2f 0%, #a8e6cf 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
    .status-inactive {
        background: linear-gradient(135deg, #ff4b4b 0%, #ff9999 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

@require_auth
def main():
    """Main dashboard page"""
    
    # Clear only specific page-related session state (preserve auth and config)
    page_keys_to_clear = ['dashboard_temp_data']
    for key in page_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.empty()
    
    # Header
    st.markdown("# 🏠 Dashboard")
    st.markdown("Your CMBCluster research environment overview")
    
    # Auto-refresh setup
    auto_refresh = st.checkbox("Auto-refresh (30s)", value=False, key="dashboard_auto_refresh")
    if auto_refresh:
        # Auto-refresh mechanism using session state
        last_refresh = st.session_state.get("dashboard_last_refresh", 0)
        current_time = time.time()
        if current_time - last_refresh > 30:
            st.session_state.dashboard_last_refresh = current_time
            st.rerun()
    
    # Get environment status
    status_data = get_environment_status()
    user_info = st.session_state.get("user_info", {})
    
    # Overview metrics row
    show_overview_metrics(status_data, user_info)
    
    st.divider()
    
    # Main content - simplified layout
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_environment_status(status_data)
    
    with col2:
        show_quick_actions(status_data)

def show_overview_metrics(status_data, user_info):
    """Display overview metrics cards"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        env_active = status_data.get("active", False)
        status_text = "🟢 Active" if env_active else "🔴 Inactive"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Environment Status</h3>
            <h2>{status_text}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        if env_active:
            env_info = status_data.get("environment", {})
            created_at = env_info.get('created_at')
            if created_at:
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    uptime = datetime.now() - created_time.replace(tzinfo=None)
                    uptime_str = f"{uptime.days}d {uptime.seconds//3600}h"
                except:
                    uptime_str = "Unknown"
            else:
                uptime_str = "Unknown"
        else:
            uptime_str = "N/A"
            
        st.markdown(f"""
        <div class="metric-card">
            <h3>Uptime</h3>
            <h2>{uptime_str}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        user_name = user_info.get("name", "User")
        st.markdown(f"""
        <div class="metric-card">
            <h3>Welcome</h3>
            <h2>{user_name}</h2>
        </div>
        """, unsafe_allow_html=True)

def show_environment_status(status_data):
    """Display detailed environment status"""
    st.markdown("### 🚀 Environment Status")
    
    if status_data.get("active"):
        env_info = status_data.get("environment", {})
        
        st.markdown("""
        <div class="status-active">
            <h3>✅ Your Environment is Running</h3>
            <p>Your research environment is active and ready to use</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Environment details
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Environment Details:**")
            st.write(f"**Pod Name:** `{env_info.get('pod_name', 'Unknown')}`")
            st.write(f"**Status:** {env_info.get('status', 'Unknown').title()}")
            st.write(f"**Created:** {env_info.get('created_at', 'Unknown')}")
        
        with col2:
            env_url = env_info.get('url')
            if env_url:
                st.markdown("**Quick Access:**")
                if st.button("🔗 Open Environment", type="primary", key="dashboard_open_env"):
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', 
                               unsafe_allow_html=True)
                st.markdown(f"[Direct Link]({env_url})")
        
    else:
        st.markdown("""
        <div class="status-inactive">
            <h3>❌ No Active Environment</h3>
            <p>Launch your environment to start working</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚀 Ready to start your research? Launch your environment to access pre-configured cosmology tools and persistent workspace.")

def show_quick_actions(status_data):
    """Display quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    env_active = status_data.get("active", False)
    
    if not env_active:
        if st.button("🚀 Launch Environment", type="primary", key="launch_env", use_container_width=True):
            launch_environment()
    else:
        if st.button("🔄 Restart Environment", key="restart_env", use_container_width=True):
            restart_environment()
        
        if st.button("⏹️ Stop Environment", key="stop_env", use_container_width=True):
            delete_environment()
        
        env_url = status_data.get("environment", {}).get("url")
        if env_url:
            if st.button("🔗 Open Environment", key="open_env", use_container_width=True):
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', 
                           unsafe_allow_html=True)

# Helper functions
def get_environment_status():
    """Get environment status"""
    try:
        return api_client.get_environment_status()
    except Exception as e:
        return {"active": False, "environment": None}

def launch_environment():
    """Launch new environment"""
    with st.spinner("🚀 Launching environment..."):
        try:
            result = api_client.create_environment()
            
            if result.get("status") in ["created", "existing"]:
                st.success(f"✅ Environment {result['status']}!")
                env_url = result.get("environment", {}).get("url")
                if env_url:
                    st.info(f"🔗 Access your environment: {env_url}")
                
                time.sleep(2)
                st.rerun()
            else:
                st.error("Failed to launch environment")
        
        except Exception as e:
            st.error(f"Error launching environment: {str(e)}")

def restart_environment():
    """Restart environment"""
    with st.spinner("🔄 Restarting environment..."):
        try:
            # Delete then create
            api_client.delete_environment()
            time.sleep(3)
            result = api_client.create_environment()
            
            if result.get("status") == "created":
                st.success("✅ Environment restarted successfully!")
                st.rerun()
        
        except Exception as e:
            st.error(f"Error restarting environment: {str(e)}")

def delete_environment():
    """Delete environment with confirmation"""
    if st.session_state.get("confirm_delete_dashboard"):
        with st.spinner("🗑️ Stopping environment..."):
            try:
                result = api_client.delete_environment()
                st.success("✅ Environment stopped successfully!")
                
                st.session_state.confirm_delete_dashboard = False
                time.sleep(1)
                st.rerun()
            
            except Exception as e:
                st.error(f"Error stopping environment: {str(e)}")
    else:
        st.warning("⚠️ This will stop your environment. Your data will be preserved.")
        if st.button("🗑️ Confirm Stop", key="dashboard_confirm_stop"):
            st.session_state.confirm_delete_dashboard = True
            st.rerun()

if __name__ == "__main__":
    if not check_authentication():
        show_login_screen()
    else:
        main()
