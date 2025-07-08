import streamlit as st
import pandas as pd
import yaml
import json
from datetime import datetime
import time
import asyncio
import threading

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth, show_user_info
from components.api_client import api_client
from config import settings

# Page configuration
st.set_page_config(
    page_title="Environment - CMBCluster",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .env-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    .resource-config {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin: 0.5rem 0;
    }
    .status-card {
        background: #e8f5e8;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #28a745;
        margin: 0.5rem 0;
    }
    .warning-card {
        background: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ffc107;
        margin: 0.5rem 0;
    }
    .error-card {
        background: #f8d7da;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #dc3545;
        margin: 0.5rem 0;
    }
    .stProgress .st-bo {
        background-color: #e9ecef;
    }
    .stProgress .st-bp {
        background-color: #28a745;
    }
</style>
""", unsafe_allow_html=True)

@require_auth
def main():
    """Main environment page"""
    # Show user info in sidebar
    show_user_info()
    
    # Clear all confirmation states and UI-related session state to prevent stacking
    page_keys_to_clear = [
        'env_logs_last_refresh', 'env_logs_auto_refresh', 
        'confirm_delete_env']
    for key in page_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Clear any environment-specific confirmation states
    # keys_to_remove = [key for key in st.session_state.keys() 
    #                  if key.startswith(('confirm_restart_', 'confirm_stop_'))]
    # for key in keys_to_remove:
    #     del st.session_state[key]
    
    # Clear page content to prevent stacking
    st.empty()
    
    # Page header
    st.title("🚀 Environment Management")
    st.markdown("Manage your research computing environments")
    
    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["🖥️ Environments", "📊 Monitoring", "⚙️ Settings"])
    
    with tab1:
        show_environment_management()
    
    with tab2:
        show_environment_monitoring()
    
    with tab3:
        show_environment_settings()

def show_environment_management():
    """Main environment management interface"""
    # Get environments
    environments = get_user_environments()
    
    if not environments:
        st.info("No environments found. Create your first environment below.")
        show_launch_interface()
    else:
        # Show active environments
        st.markdown("### 🏃 Active Environments")
        for env in environments:
            show_environment_card(env)
        
        st.markdown("---")
        st.markdown("### 🚀 Launch New Environment")
        show_launch_interface()

def show_environment_card(env):
    """Display a single environment card"""
    status = env.get("status", "unknown").lower()
    
    # Extract environment ID - prefer env_id over composite id
    env_id = env.get("env_id")  # This is the short UUID
    if not env_id:
        env_id = env.get("id", "unknown")  # Fallback to full id
    
    # For display, use the short env_id if available
    display_id = env.get("env_id", env.get("id", "unknown"))
    
    # Status indicator
    if status == "running":
        status_emoji = "🟢"
        status_color = "#28a745"
    elif status == "pending":
        status_emoji = "🟡"
        status_color = "#ffc107"
    elif status == "failed":
        status_emoji = "🔴"
        status_color = "#dc3545"
    else:
        status_emoji = "⚪"
        status_color = "#6c757d"
    
    # Environment card
    with st.container():
        st.markdown(f"""
        <div class="env-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h4>{status_emoji} Environment {display_id[:8]}...</h4>
                    <p style="color: {status_color}; font-weight: bold;">Status: {status.title()}</p>
                    <p><strong>Created:</strong> {format_datetime(env.get('created_at'))}</p>
                    <p><strong>URL:</strong> <a href="{env.get('url', '#')}" target="_blank">{env.get('url', 'N/A')}</a></p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Action buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔗 Open", key=f"open_{env_id}", type="primary"):
                env_url = env.get("url")
                if env_url:
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', unsafe_allow_html=True)
        
        with col2:
            if st.button("🔄 Restart", key=f"restart_{env_id}"):
                restart_environment(env_id)
        
        with col3:
            if st.button("⏹️ Stop", key=f"stop_{env_id}"):
                stop_environment(env_id)
        
        with col4:
            if st.button("📊 Status", key=f"status_{env_id}"):
                check_environment_status(env_id)

def show_launch_interface():
    """Environment launch interface with enhanced user experience"""
    st.markdown("#### 🚀 Launch Configuration")
    
    # Add helpful description
    st.markdown("""
    💡 **Getting Started:** Choose a preset configuration based on your computational needs.
    Each preset includes optimized CPU, memory, and storage allocation.
    """)
    
    # Environment presets with better descriptions
    preset_options = [
        "Standard Research (2 CPU, 4GB RAM) - Recommended for most users",
        "Heavy Computation (4 CPU, 8GB RAM) - For intensive calculations",
        "Light Analysis (1 CPU, 2GB RAM) - For simple tasks and testing",
        "Custom Configuration - Advanced users only"
    ]
    
    preset = st.selectbox("Environment Preset", preset_options, key="environment_preset_select")
    
    # Clean up preset name for processing
    preset_clean = preset.split(" - ")[0]
    
    # Show resource configuration with better formatting
    config = get_preset_config(preset_clean)
    
    # Show configuration in columns for better readability
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("🖥️ CPU Cores", f"{config['cpu_limit']}")
    with col2:
        st.metric("💾 Memory", config['memory_limit'])
    with col3:
        st.metric("💽 Storage", config['storage_size'])
    
    # Expandable detailed configuration
    with st.expander("📋 Detailed Configuration", expanded=False):
        st.json(config)
    
    # Enhanced launch button with confirmation
    st.markdown("---")
    
    # Add estimated launch time
    st.info("⏱️ **Estimated launch time:** 30-60 seconds")
    
    # Check if launch is in progress
    if st.session_state.get("launch_in_progress", False):
        st.warning("🚀 Launch in progress... Please wait")
        if st.button("❌ Cancel Launch", key="cancel_launch"):
            st.session_state.launch_in_progress = False
            st.rerun()
    else:
        # Launch button with better styling
        launch_col1, launch_col2 = st.columns([3, 1])
        
        with launch_col1:
            if st.button("🚀 Launch Environment", type="primary", use_container_width=True, key="launch_env_button"):
                st.session_state.launch_in_progress = True
                st.rerun()
        
        with launch_col2:
            if st.button("📋 Preview", use_container_width=True, key="preview_config"):
                st.info("📊 **Configuration Preview:**")
                st.json(config)
    
    # Execute launch if triggered
    if st.session_state.get("launch_in_progress", False):
        launch_environment_with_progress(preset_clean, config)
        st.session_state.launch_in_progress = False

def get_preset_config(preset):
    """Get configuration for preset"""
    config_map = {
        "Standard Research (2 CPU, 4GB RAM)": {"cpu_limit": 2.0, "memory_limit": "4Gi", "storage_size": "20Gi"},
        "Heavy Computation (4 CPU, 8GB RAM)": {"cpu_limit": 4.0, "memory_limit": "8Gi", "storage_size": "50Gi"},
        "Light Analysis (1 CPU, 2GB RAM)": {"cpu_limit": 1.0, "memory_limit": "2Gi", "storage_size": "10Gi"},
        "Custom Configuration": st.session_state.get("custom_config", {"cpu_limit": 2.0, "memory_limit": "4Gi", "storage_size": "20Gi"})
    }
    return config_map.get(preset, {"cpu_limit": 2.0, "memory_limit": "4Gi", "storage_size": "20Gi"})

def launch_environment_with_progress(preset, config):
    """Launch environment with simplified progress tracking"""
    try:
        # Check if user is authenticated
        token = st.session_state.get("access_token")
        if not token:
            st.error("❌ Authentication required. Please login again.")
            return
        
        # Step 1: Validation
        st.info("🔍 Validating configuration...")
        progress_bar = st.progress(0)
        time.sleep(0.5)
        progress_bar.progress(33)
        
        # Step 2: API call
        st.info("🚀 Launching environment...")
        progress_bar.progress(66)
        
        result = api_client.create_environment(config)
        progress_bar.progress(100)
        
        if result.get("status") in ["created", "existing"]:
            if result.get("status") == "existing":
                st.success(f"✅ Environment already exists with {preset}!")
            else:
                st.success(f"✅ Environment created successfully with {preset}!")
            
            # Show stars instead of balloons
            st.markdown("⭐ ⭐ ⭐ **Success!** ⭐ ⭐ ⭐")
            
            env_url = result.get("environment", {}).get("url")
            if env_url:
                st.info(f"🔗 Access your environment: {env_url}")
                # Add a direct link button
                if st.button("🌐 Open Environment", key="open_new_env", type="primary"):
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', unsafe_allow_html=True)
            
            st.info("📊 Note: Environment may take a few minutes to fully start. Check the Monitoring tab for status updates.")
            
        else:
            st.error(f"❌ Failed to launch environment. Status: {result.get('status', 'Unknown')}")
            
            # Show helpful error information
            if result.get("message"):
                st.warning(f"📝 Details: {result.get('message')}")
            
            # Add retry button
            if st.button("🔄 Retry Launch", key="retry_launch"):
                st.rerun()
        
    except Exception as e:
        st.error(f"❌ Error launching environment: {str(e)}")
        
        # Add troubleshooting information
        with st.expander("🔧 Troubleshooting"):
            st.markdown("""
            **Common issues and solutions:**
            - **Network issues**: Check your internet connection
            - **Authentication**: Try logging out and back in
            - **Resource limits**: Try a smaller configuration
            - **Server busy**: Wait a moment and try again
            """)
        
        # Add retry button for errors too
        if st.button("🔄 Retry Launch", key="retry_launch_error"):
            st.rerun()

def restart_environment(env_id):
    """Restart environment with simplified confirmation"""
    # Check if confirmation is pending
    with st.spinner("🔄 Restarting environment..."):
        try:
            # Use the API client restart method
            result = api_client.restart_environment(env_id=env_id)
            
            if result.get("status") == "success":
                st.success("✅ Environment restart initiated successfully!")
                # Show stars instead of balloons
                st.markdown("⭐ ⭐ ⭐ **Restart Initiated!** ⭐ ⭐ ⭐")
                st.info("📊 Environment is restarting. Please check the Monitoring tab for status updates.")
                
                # Clear confirmation state
                st.session_state[f"confirm_restart_{env_id}"] = False
            elif result.get("status") == "error":
                st.error(f"❌ Failed to restart environment")
                st.warning(f"📝 Details: {result.get('message', 'Unknown error')}")
                st.session_state[f"confirm_restart_{env_id}"] = False
            else:
                # Legacy handling for backward compatibility
                if result.get("status") in ["created", "existing"]:
                    st.success("✅ Environment restart initiated successfully!")
                    st.markdown("⭐ ⭐ ⭐ **Restart Initiated!** ⭐ ⭐ ⭐")
                    st.info("📊 Environment is restarting. Please check the Monitoring tab for status updates.")
                    st.session_state[f"confirm_restart_{env_id}"] = False
                else:
                    st.error(f"❌ Failed to restart environment. Status: {result.get('status', 'Unknown')}")
                    if result.get("message"):
                        st.warning(f"📝 Details: {result.get('message')}")
                    st.session_state[f"confirm_restart_{env_id}"] = False
                
        except Exception as e:
            st.error(f"❌ Error restarting environment: {str(e)}")
            with st.expander("🔧 Debug Information"):
                st.write(f"Environment ID: {env_id}")
                st.write(f"Error type: {type(e).__name__}")
                st.write(f"Error details: {str(e)}")
            st.session_state[f"confirm_restart_{env_id}"] = False


def stop_environment(env_id):
    """Stop environment with simplified confirmation"""
    # Check if confirmation is pending
    
    with st.spinner("🗑️ Stopping environment..."):
        try:
            # Use the API client stop method
            result = api_client.stop_environment(env_id=env_id)
            
            if result.get("status") == "success":
                st.success("✅ Environment stop initiated successfully!")
                # Show stars instead of balloons
                st.markdown("⭐ ⭐ ⭐ **Stop Initiated!** ⭐ ⭐ ⭐")
                st.info("📊 Environment is stopping. Please refresh the page to see updated status.")
                
                # Clear confirmation state
                st.session_state[f"confirm_stop_{env_id}"] = False
            elif result.get("status") == "error":
                st.error(f"❌ Failed to stop environment")
                st.warning(f"📝 Details: {result.get('message', 'Unknown error')}")
                st.session_state[f"confirm_stop_{env_id}"] = False
            else:
                # Legacy handling for backward compatibility
                if result.get("status") == "deleted":
                    st.success("✅ Environment stop initiated successfully!")
                    st.markdown("⭐ ⭐ ⭐ **Stop Initiated!** ⭐ ⭐ ⭐")
                    st.info("📊 Environment is stopping. Please refresh the page to see updated status.")
                    st.session_state[f"confirm_stop_{env_id}"] = False
                else:
                    st.error(f"❌ Failed to stop environment. Status: {result.get('status', 'Unknown')}")
                    if result.get("message"):
                        st.warning(f"📝 Details: {result.get('message')}")
                    st.session_state[f"confirm_stop_{env_id}"] = False
            
        except Exception as e:
            st.error(f"❌ Error stopping environment: {str(e)}")
            with st.expander("🔧 Debug Information"):
                st.write(f"Environment ID: {env_id}")
                st.write(f"Error type: {type(e).__name__}")
                st.write(f"Error details: {str(e)}")
            st.session_state[f"confirm_stop_{env_id}"] = False
 

def check_environment_status(env_id):
    """Check and display environment status"""
    try:
        status = get_environment_status_by_id(env_id)
        if status.get("active"):
            env_info = status.get("environment", {})
            st.success(f"✅ Environment Status: {env_info.get('status', 'Unknown').title()}")
            with st.expander("📊 Detailed Status"):
                st.json(env_info)
        else:
            st.warning("⚠️ Environment not found or inactive")
    except Exception as e:
        st.error(f"❌ Error checking status: {str(e)}")

def show_environment_monitoring():
    """Environment monitoring tab"""
    st.markdown("### 📊 Environment Monitoring")
    
    # Manual refresh button instead of auto-refresh
    if st.button("🔄 Refresh Status", key="refresh_monitoring"):
        st.rerun()
    
    # Get environments
    environments = get_user_environments()
    
    if not environments:
        st.info("No environments to monitor.")
        return
    
    # Show monitoring cards
    for env in environments:
        show_monitoring_card(env)

def show_monitoring_card(env):
    """Display monitoring card for an environment"""
    status = env.get("status", "unknown").lower()
    env_id = env.get("id", env.get("env_id", "unknown"))
    
    # Status card
    if status == "running":
        card_class = "status-card"
        status_emoji = "🟢"
    elif status == "pending":
        card_class = "warning-card"
        status_emoji = "🟡"
    else:
        card_class = "error-card"
        status_emoji = "🔴"
    
    st.markdown(f"""
    <div class="{card_class}">
        <h4>{status_emoji} Environment {env_id[:8]}...</h4>
        <p><strong>Status:</strong> {status.title()}</p>
        <p><strong>Created:</strong> {format_datetime(env.get('created_at'))}</p>
        <p><strong>Last Activity:</strong> {format_datetime(env.get('last_activity'))}</p>
        <p><strong>URL:</strong> <a href="{env.get('url', '#')}" target="_blank">{env.get('url', 'N/A')}</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Resource usage (if available)
    resource_config = env.get("resource_config", {})
    if resource_config:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("CPU", resource_config.get("cpu_limit", "N/A"))
        with col2:
            st.metric("Memory", resource_config.get("memory_limit", "N/A"))
        with col3:
            st.metric("Storage", resource_config.get("storage_size", "N/A"))

def show_environment_settings():
    """Environment settings tab"""
    st.markdown("### ⚙️ Environment Settings")
    
    # Custom configuration
    st.markdown("#### 🔧 Custom Configuration")
    
    with st.form("custom_config"):
        cpu_limit = st.number_input("CPU Limit", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
        memory_limit = st.selectbox("Memory Limit", ["1Gi", "2Gi", "4Gi", "8Gi", "16Gi"], index=2)
        storage_size = st.selectbox("Storage Size", ["10Gi", "20Gi", "50Gi", "100Gi"], index=1)
        
        if st.form_submit_button("💾 Save Configuration"):
            custom_config = {
                "cpu_limit": cpu_limit,
                "memory_limit": memory_limit,
                "storage_size": storage_size
            }
            st.session_state.custom_config = custom_config
            st.success("✅ Custom configuration saved!")
    
    # Display current settings
    if "custom_config" in st.session_state:
        st.markdown("#### 📋 Current Custom Configuration")
        st.json(st.session_state.custom_config)

def get_user_environments():
    """Get user environments from API"""
    try:
        response = api_client.list_environments()
        return response.get("environments", [])
    except Exception as e:
        st.error(f"❌ Error fetching environments: {str(e)}")
        return []

def get_environment_status_by_id(env_id):
    """Get environment status by ID"""
    try:
        # First try the specific method
        result = api_client.get_environment_by_id(env_id)
        if result.get("active"):
            return result
        
        # Fallback: refresh the environments list to catch newly created ones
        environments = api_client.list_environments().get("environments", [])
        for env in environments:
            if env.get("id") == env_id or env.get("env_id") == env_id:
                return {"active": True, "environment": env}
        
        return {"active": False, "environment": None}
    except Exception as e:
        return {"active": False, "environment": None}

def format_datetime(dt_str):
    """Format datetime string for display"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str

if __name__ == "__main__":
    if not check_authentication():
        show_login_screen()
    else:
        main()
