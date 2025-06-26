import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth
from components.api_client import api_client
from config import settings

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
    .quick-action-btn {
        width: 100%;
        margin: 0.25rem 0;
    }
</style>
""", unsafe_allow_html=True)

@require_auth
def main():
    """Main dashboard page"""
    
    # Header
    st.markdown("# 🏠 Dashboard")
    st.markdown("Welcome to your CMBCluster research environment overview")
    
    # Auto-refresh setup
    if st.checkbox("Auto-refresh (30s)", value=True, key="dashboard_refresh"):
        time.sleep(30)
        st.rerun()
    
    # Get environment status
    status_data = get_environment_status()
    user_info = st.session_state.get("user_info", {})
    
    # Overview metrics row
    show_overview_metrics(status_data, user_info)
    
    st.divider()
    
    # Main content
    col1, col2 = st.columns([2, 1])
    
    with col1:
        show_environment_status(status_data)
        st.markdown("### 📊 Activity Overview")
        show_activity_charts()
    
    with col2:
        show_quick_actions(status_data)
        show_recent_activity()

def show_overview_metrics(status_data, user_info):
    """Display overview metrics cards"""
    col1, col2, col3, col4 = st.columns(4)
    
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
        uptime = status_data.get("uptime", "0 minutes") if env_active else "N/A"
        st.markdown(f"""
        <div class="metric-card">
            <h3>Uptime</h3>
            <h2>{uptime}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        last_activity = status_data.get("last_activity", "Never")
        st.markdown(f"""
        <div class="metric-card">
            <h3>Last Activity</h3>
            <h2>{last_activity}</h2>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        user_name = user_info.get("name", "Unknown User")
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
                if st.button("🔗 Open Environment", type="primary"):
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', 
                               unsafe_allow_html=True)
                st.markdown(f"[Direct Link]({env_url})")
        
        # Resource usage (mock data for demonstration)
        show_resource_usage()
        
    else:
        st.markdown("""
        <div class="status-inactive">
            <h3>❌ No Active Environment</h3>
            <p>Launch your environment to start working</p>
        </div>
        """, unsafe_allow_html=True)
        
        st.info("🚀 Ready to start your research? Launch your environment to access pre-configured cosmology tools and persistent workspace.")

def show_resource_usage():
    """Display resource usage charts"""
    st.markdown("#### 📈 Resource Usage")
    
    # Mock resource data
    cpu_usage = 45
    memory_usage = 62
    storage_usage = 28
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        fig_cpu = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = cpu_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "CPU Usage (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkblue"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ],
                'threshold': {
                    'line': {'color': "red", 'width': 4},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_cpu.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_cpu, use_container_width=True)
    
    with col2:
        fig_mem = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = memory_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Memory Usage (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "darkgreen"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ]
            }
        ))
        fig_mem.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_mem, use_container_width=True)
    
    with col3:
        fig_storage = go.Figure(go.Indicator(
            mode = "gauge+number",
            value = storage_usage,
            domain = {'x': [0, 1], 'y': [0, 1]},
            title = {'text': "Storage Usage (%)"},
            gauge = {
                'axis': {'range': [None, 100]},
                'bar': {'color': "purple"},
                'steps': [
                    {'range': [0, 50], 'color': "lightgray"},
                    {'range': [50, 80], 'color': "yellow"},
                    {'range': [80, 100], 'color': "red"}
                ]
            }
        ))
        fig_storage.update_layout(height=200, margin=dict(l=0, r=0, t=30, b=0))
        st.plotly_chart(fig_storage, use_container_width=True)

def show_activity_charts():
    """Display activity timeline and usage patterns"""
    
    # Mock activity data
    dates = pd.date_range(start='2025-06-20', end='2025-06-26', freq='D')
    activity_data = pd.DataFrame({
        'Date': dates,
        'Sessions': [2, 3, 1, 4, 2, 3, 1],
        'Duration (hours)': [1.5, 2.8, 0.5, 3.2, 1.8, 2.1, 0.8],
        'Data Processed (GB)': [0.5, 1.2, 0.2, 2.1, 0.8, 1.5, 0.3]
    })
    
    # Activity timeline
    fig_timeline = px.line(activity_data, x='Date', y='Duration (hours)', 
                          title='Daily Usage Pattern',
                          markers=True)
    fig_timeline.update_layout(height=300)
    st.plotly_chart(fig_timeline, use_container_width=True)
    
    # Usage distribution
    col1, col2 = st.columns(2)
    
    with col1:
        fig_sessions = px.bar(activity_data, x='Date', y='Sessions',
                             title='Daily Sessions')
        fig_sessions.update_layout(height=250)
        st.plotly_chart(fig_sessions, use_container_width=True)
    
    with col2:
        fig_data = px.bar(activity_data, x='Date', y='Data Processed (GB)',
                         title='Data Processing')
        fig_data.update_layout(height=250)
        st.plotly_chart(fig_data, use_container_width=True)

def show_quick_actions(status_data):
    """Display quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    
    env_active = status_data.get("active", False)
    
    if not env_active:
        if st.button("🚀 Launch Environment", type="primary", key="launch_env"):
            launch_environment()
    else:
        if st.button("🔄 Restart Environment", key="restart_env"):
            restart_environment()
        
        if st.button("⏹️ Stop Environment", key="stop_env"):
            delete_environment()
        
        env_url = status_data.get("environment", {}).get("url")
        if env_url:
            if st.button("🔗 Open Environment", key="open_env"):
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', 
                           unsafe_allow_html=True)
    
    st.markdown("### 🔧 Quick Settings")
    
    # Auto-cleanup setting
    auto_cleanup = st.checkbox("Auto-cleanup (4h inactive)", value=True)
    
    # Resource presets
    resource_preset = st.selectbox("Resource Preset", 
                                  ["Light (1 CPU, 2GB)", "Standard (2 CPU, 4GB)", "Heavy (4 CPU, 8GB)"])
    
    if st.button("Apply Settings"):
        st.success("Settings applied! Changes will take effect on next environment launch.")

def show_recent_activity():
    """Display recent activity log"""
    st.markdown("### 📋 Recent Activity")
    
    # Mock recent activity
    activities = [
        {"time": "2 minutes ago", "action": "Environment heartbeat", "status": "✅"},
        {"time": "15 minutes ago", "action": "Data analysis executed", "status": "✅"},
        {"time": "1 hour ago", "action": "Environment launched", "status": "✅"},
        {"time": "Yesterday", "action": "Environment stopped", "status": "🔴"},
        {"time": "2 days ago", "action": "Data uploaded", "status": "✅"}
    ]
    
    for activity in activities:
        with st.container():
            col1, col2, col3 = st.columns([3, 2, 1])
            with col1:
                st.write(activity["action"])
            with col2:
                st.caption(activity["time"])
            with col3:
                st.write(activity["status"])

# Helper functions
@st.cache_data(ttl=30)
def get_environment_status():
    """Get environment status with caching"""
    try:
        return api_client.get_environment_status()
    except Exception as e:
        st.error(f"Failed to get environment status: {str(e)}")
        return {"active": False}

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

def delete_environment():
    """Delete environment with confirmation"""
    if st.session_state.get("confirm_delete_dashboard"):
        with st.spinner("🗑️ Stopping environment..."):
            try:
                result = api_client.delete_environment()
                st.success("✅ Environment stopped successfully!")
                
                # Clear cache and refresh
                get_environment_status.clear()
                st.session_state.confirm_delete_dashboard = False
                time.sleep(1)
                st.rerun()
            
            except Exception as e:
                st.error(f"Error stopping environment: {str(e)}")
    else:
        st.warning("⚠️ This will stop your environment. Your data will be preserved.")
        if st.button("🗑️ Confirm Stop"):
            st.session_state.confirm_delete_dashboard = True
            st.rerun()

if __name__ == "__main__":
    # Check authentication
    if not check_authentication():
        show_login_screen()
    else:
        main()
