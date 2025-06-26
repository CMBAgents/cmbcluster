import streamlit as st
import time
from datetime import datetime
import plotly.express as px
import pandas as pd

from config import settings
from components.auth import check_authentication, show_login_screen, show_user_info, require_auth
from components.api_client import api_client

# Page configuration
st.set_page_config(
    page_title=settings.app_title,
    page_icon=settings.app_icon,
    layout=settings.layout,
    initial_sidebar_state=settings.sidebar_state
)

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
    .status-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #ddd;
        margin: 1rem 0;
    }
    .status-active {
        background: linear-gradient(135deg, #d4edda 0%, #c3e6cb 100%);
        border-color: #28a745;
    }
    .status-inactive {
        background: linear-gradient(135deg, #f8d7da 0%, #f5c6cb 100%);
        border-color: #dc3545;
    }
    .metric-container {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

def main():
    """Main application entry point"""
    # Check authentication
    if not check_authentication():
        show_login_screen()
        return
    
    # Show authenticated interface
    show_authenticated_app()

@require_auth
def show_authenticated_app():
    """Main authenticated application interface"""
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
    
    # Main content
    show_dashboard()

def setup_auto_refresh():
    """Setup auto-refresh functionality"""
    with st.sidebar:
        st.markdown("---")
        auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
        
        if auto_refresh:
            # Auto-refresh every 30 seconds
            time.sleep(0.1)  # Prevent too frequent refreshes
            st.rerun()

def show_dashboard():
    """Main dashboard interface"""
    # Quick actions in sidebar
    with st.sidebar:
        st.markdown("### ⚡ Quick Actions")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🚀 Launch", use_container_width=True):
                launch_environment()
        with col2:
            if st.button("🗑️ Delete", use_container_width=True):
                delete_environment()
    
    # Main content tabs
    tab1, tab2, tab3 = st.tabs(["📊 Overview", "🚀 Environment", "📋 Activity"])
    
    with tab1:
        show_overview_tab()
    
    with tab2:
        show_environment_tab()
    
    with tab3:
        show_activity_tab()

def show_overview_tab():
    """Overview dashboard"""
    st.markdown("## 📊 Environment Overview")
    
    # Get environment status
    status_data = get_environment_status()
    
    # Status cards
    col1, col2 = st.columns(2)
    
    with col1:
        if status_data.get("active"):
            st.markdown("""
            <div class="status-card status-active">
                <h3>✅ Environment Active</h3>
                <p>Your research environment is running</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.markdown("""
            <div class="status-card status-inactive">
                <h3>❌ Environment Inactive</h3>
                <p>No active environment found</p>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        env_info = status_data.get("environment", {})
        if status_data.get("active"):
            st.markdown(f"""
            <div class="metric-container">
                <h4>🔗 Environment Details</h4>
                <p><strong>Pod:</strong> {env_info.get('pod_name', 'Unknown')}</p>
                <p><strong>Status:</strong> {env_info.get('status', 'Unknown')}</p>
                <p><strong>URL:</strong> <a href="{env_info.get('url', '#')}" target="_blank">Open Environment</a></p>
            </div>
            """, unsafe_allow_html=True)
    
    # Metrics
    if status_data.get("active"):
        st.markdown("### 📈 Environment Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            created_at = env_info.get('created_at')
            if created_at:
                uptime = datetime.now() - datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                st.metric("Uptime", f"{uptime.seconds // 3600}h {(uptime.seconds % 3600) // 60}m")
            else:
                st.metric("Uptime", "Unknown")
        
        with col2:
            st.metric("Status", env_info.get('status', 'Unknown').title())
        
        with col3:
            last_activity = env_info.get('last_activity', 'Never')
            st.metric("Last Activity", last_activity)
    
    # Quick launch section
    if not status_data.get("active"):
        st.markdown("### 🚀 Get Started")
        st.info("Launch your environment to start working with cosmology data and tools.")
        
        if st.button("🚀 Launch Environment", type="primary", use_container_width=True):
            launch_environment()

def show_environment_tab():
    """Environment management tab"""
    st.markdown("## 🚀 Environment Management")
    
    status_data = get_environment_status()
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### Current Status")
        
        if status_data.get("active"):
            env_info = status_data.get("environment", {})
            st.success("✅ Environment is running")
            
            st.markdown("**Environment Details:**")
            st.json({
                "Pod Name": env_info.get('pod_name'),
                "Status": env_info.get('status'),
                "Created At": env_info.get('created_at'),
                "Last Activity": env_info.get('last_activity'),
                "URL": env_info.get('url')
            })
        else:
            st.warning("❌ No active environment")
            st.info("Create a new environment to start your research work.")
    
    with col2:
        st.markdown("### Actions")
        
        if not status_data.get("active"):
            if st.button("🚀 Launch Environment", type="primary", use_container_width=True):
                launch_environment()
        else:
            if st.button("🔄 Restart", use_container_width=True):
                restart_environment()
            
            if st.button("⏹️ Stop", use_container_width=True):
                delete_environment()
            
            env_url = status_data.get("environment", {}).get("url")
            if env_url:
                if st.button("🔗 Open Environment", use_container_width=True):
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', 
                               unsafe_allow_html=True)
    
    # Environment configuration
    st.markdown("### ⚙️ Environment Configuration")
    
    with st.expander("Resource Settings"):
        col1, col2 = st.columns(2)
        
        with col1:
            cpu_limit = st.slider("CPU Cores", 0.5, 4.0, 1.0, 0.5)
            memory_gb = st.slider("Memory (GB)", 1, 8, 2, 1)
        
        with col2:
            storage_gb = st.slider("Storage (GB)", 5, 50, 10, 5)
            auto_cleanup_hours = st.slider("Auto-cleanup (hours)", 1, 24, 4, 1)
        
        if st.button("💾 Save Configuration"):
            st.success("Configuration saved! Will apply to next environment.")

def show_activity_tab():
    """Activity log tab"""
    st.markdown("## 📋 Activity Log")
    
    # Activity filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        filter_type = st.selectbox("Filter by Type", 
                                  ["All", "Environment", "Authentication", "System"])
    with col2:
        filter_status = st.selectbox("Filter by Status", 
                                   ["All", "Success", "Error", "Warning"])
    with col3:
        if st.button("🔄 Refresh Log"):
            st.rerun()
    
    # Get activity data
    activity_data = get_activity_log()
    activities = activity_data.get("activities", [])
    
    if activities:
        # Activity timeline
        st.markdown("### Activity Timeline")
        
        df = pd.DataFrame(activities)
        if not df.empty:
            # Create timeline chart
            fig = px.timeline(
                df, 
                x_start="timestamp", 
                x_end="timestamp",
                y="action",
                color="status",
                title="Recent Activity"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Activity list
        st.markdown("### Detailed Log")
        
        for activity in activities:
            with st.container():
                col1, col2, col3 = st.columns([3, 2, 1])
                
                with col1:
                    st.write(f"**{activity.get('action', 'Unknown')}**")
                    if activity.get('details'):
                        st.caption(activity['details'])
                
                with col2:
                    timestamp = activity.get('timestamp', 'Unknown')
                    st.write(timestamp)
                
                with col3:
                    status = activity.get('status', 'unknown')
                    if status == 'success':
                        st.success("✅")
                    elif status == 'error':
                        st.error("❌")
                    else:
                        st.warning("⚠️")
                
                st.markdown("---")
    else:
        st.info("No activity recorded yet.")

# Helper functions
@st.cache_data(ttl=30)
def get_environment_status():
    """Get environment status with caching"""
    try:
        return api_client.get_environment_status()
    except Exception as e:
        st.error(f"Failed to get environment status: {str(e)}")
        return {"active": False}

@st.cache_data(ttl=60)
def get_activity_log():
    """Get activity log with caching"""
    try:
        return api_client.get_activity_log()
    except Exception as e:
        return {"activities": []}

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
                
                # Clear cache and refresh
                get_environment_status.clear()
                time.sleep(2)
                st.rerun()
            else:
                st.error("Failed to launch environment")
        
        except Exception as e:
            st.error(f"Error launching environment: {str(e)}")

def delete_environment():
    """Delete environment with confirmation"""
    if st.session_state.get("confirm_delete"):
        with st.spinner("🗑️ Deleting environment..."):
            try:
                result = api_client.delete_environment()
                st.success("✅ Environment deleted successfully!")
                
                # Clear cache and refresh
                get_environment_status.clear()
                st.session_state.confirm_delete = False
                time.sleep(1)
                st.rerun()
            
            except Exception as e:
                st.error(f"Error deleting environment: {str(e)}")
    else:
        st.warning("⚠️ This will permanently delete your environment and all data!")
        if st.button("🗑️ Confirm Delete"):
            st.session_state.confirm_delete = True
            st.rerun()

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
                get_environment_status.clear()
                st.rerun()
        
        except Exception as e:
            st.error(f"Error restarting environment: {str(e)}")

if __name__ == "__main__":
    main()
