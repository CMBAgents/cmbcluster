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
from components.auth import check_authentication, show_login_screen, require_auth, show_user_info
from components.api_client import api_client
from components.storage_selector import show_storage_selector
from components.dark_theme import DARK_THEME_CSS
from config import settings
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
        'About': f"# {settings.app_title}\n{settings.app_tagline}"
    }
)

# Check authentication first, before rendering any content
if not check_authentication():
    show_login_screen()
    st.stop()

# Apply dark theme CSS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Custom CSS for logo styling
st.markdown("""
<style>
/* Make Cambridge logo text white by targeting the custom container */
.cambridge-logo-container img {
    filter: invert(1) brightness(2.5) contrast(2) saturate(0) hue-rotate(180deg) !important;
    -webkit-filter: invert(1) brightness(2.5) contrast(2) saturate(0) hue-rotate(180deg) !important;
}
</style>
""", unsafe_allow_html=True)

# Logo section with better alignment
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

with col1:
    # Add a custom class to identify Cambridge logo
    st.markdown('<div class="cambridge-logo-container">', unsafe_allow_html=True)
    st.image(CAMBRIDGE_LOGO_URL, width=120)
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.image(INFOSYS_LOGO_URL, width=120)

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
    st.title("Research Computing Environments")
    
    # Tabs for different views (removed Settings tab, moved Storage to Settings page)
    tab1, tab2 = st.tabs(["Environments", "Monitoring"])
    
    with tab1:
        show_environment_management()
    
    with tab2:
        show_environment_monitoring()

def show_environment_management():
    """Main environment management interface"""
    # Get environments
    environments = get_user_environments()
    
    if not environments:
        # Compact no environments message
        st.markdown("""
                <div class="empty-state-card">
            <h4>No Active Environments</h4>
            <p>You don't have any running environments. Launch your first environment to get started!</p>
        </div>
        """, unsafe_allow_html=True)
        show_compact_launch_interface()
    else:
        # Compact environments overview
        st.markdown("### Active Environments")
        
        # Summary metrics
        running_count = len([e for e in environments if e.get("status", "").lower() == "running"])
        total_count = len(environments)
        
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        with metric_col1:
            st.metric("Total", total_count)
        with metric_col2:
            st.metric("Running", running_count, delta=f"{running_count}/{total_count}")
        with metric_col3:
            st.metric("Available", total_count - running_count)
        
        # Compact environments table
        show_compact_environments_table(environments)
        
        # Compact launch section
        with st.expander("Launch New Environment", expanded=False):
            show_compact_launch_interface()

def show_compact_environments_table(environments):
    """Display environments in a compact table format"""
    st.markdown("#### Environment List")
    
    for i, env in enumerate(environments):
        status = env.get("status", "unknown").lower()
        env_id = env.get("env_id", env.get("id", "unknown"))
        display_id = env_id[:8] if len(env_id) > 8 else env_id
        
        # Status styling
        status_styles = {
            "running": {"color": "#48BB78"},
            "pending": {"color": "#ED8936"},
            "failed": {"color": "#F56565"},
            "stopped": {"color": "#718096"}
        }
        
        style = status_styles.get(status, {"color": "#718096"})
        
        # Compact environment row
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 4])
            
            with col1:
                st.markdown(f"""
                <div style="padding: 0.5rem; background: var(--bg-tertiary); border-radius: 6px; margin: 0.25rem 0;">
                    <strong style="color: var(--text-primary);">{display_id}</strong><br>
                    <small style="color: {style['color']};">{status.title()}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                created_time = format_datetime(env.get('created_at'))
                st.markdown(f"""
                <div style="padding: 0.5rem; font-size: 0.85rem; color: var(--text-secondary);">
                    <strong>Created:</strong><br>{created_time}
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                env_url = env.get('url', '')
                if env_url:
                    st.markdown(f"""
                    <div style="padding: 0.5rem; font-size: 0.85rem;">
                        <a href="{env_url}" target="_blank" style="color: var(--accent-primary); text-decoration: none;">
                            Access
                        </a>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("**URL:** N/A")
            
            with col4:
                # Compact action buttons
                action_col1, action_col2, action_col3, action_col4 = st.columns(4)
                
                with action_col1:
                    if env.get('url') and st.button("", key=f"open_{env_id}", help="Open Environment", icon=":material/launch:"):
                        st.markdown(f'<meta http-equiv="refresh" content="0;URL={env.get("url")}" target="_blank">', unsafe_allow_html=True)
                
                with action_col2:
                    if st.button("", key=f"restart_{env_id}", help="Restart", icon=":material/restart_alt:"):
                        restart_environment(env_id)
                
                with action_col3:
                    if st.button("", key=f"stop_{env_id}", help="Stop", icon=":material/stop_circle:"):
                        stop_environment(env_id)
                
                with action_col4:
                    if st.button("", key=f"status_{env_id}", help="Refresh Status", icon=":material/visibility:"):
                        show_environment_details(env)
        
        # Add separator for readability
        if i < len(environments) - 1:
            st.markdown("---")

def show_compact_launch_interface():
    """Compact environment launch interface"""
    
    # Compact preset selection and workspace selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        preset_options = {
            "Standard Research": "2 CPU, 4GB RAM - Recommended",
            "Heavy Computation": "4 CPU, 8GB RAM - Intensive tasks", 
            "Light Analysis": "1 CPU, 2GB RAM - Simple tasks"
            # "Custom": "Advanced configuration"  # Commented out for now
        }
        
        selected_preset = st.selectbox(
            "Environment Type",
            options=list(preset_options.keys()),
            format_func=lambda x: f"{x} ({preset_options[x]})",
            help="Choose the environment configuration that matches your workload"
        )
        
        # Workspace selection (compact)
        st.markdown("**Workspace Storage:**")
        selected_storage = show_storage_selector()
    
    with col2:
        # Add some spacing to align with the preset selection
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Quick launch button - only enabled if storage is selected
        button_disabled = not selected_storage or selected_storage.get("selection_type") == "pending"
        
        if st.button("Quick Launch", type="primary", icon=":material/rocket_launch:", 
                    use_container_width=True, disabled=button_disabled):
            quick_launch_environment(selected_preset, selected_storage)
    
    # Show warning if storage not selected
    if not selected_storage or selected_storage.get("selection_type") == "pending":
        st.warning("Please select a workspace before launching")
    
    # Launch status
    if st.session_state.get("launch_in_progress", False):
        with st.container():
            st.markdown("""
            <div class="warning-card">
                <h4>Launching Environment</h4>
                <p>Please wait while your environment is being created...</p>
            </div>
            """, unsafe_allow_html=True)
            
            progress = st.progress(0)
            for i in range(100):
                time.sleep(0.01)
                progress.progress(i + 1)
            
            if st.button("Cancel Launch", icon=":material/cancel:"):
                st.session_state.launch_in_progress = False
                st.rerun()

def show_custom_configuration():
    """Show custom configuration options"""
    col1, col2, col3 = st.columns(3)
    
    with col1:
        cpu_cores = st.slider("CPU Cores", 0.5, 8.0, 2.0, 0.5)
    with col2:
        memory_gb = st.slider("Memory (GB)", 1, 32, 4, 1)
    with col3:
        storage_gb = st.slider("Storage (GB)", 10, 500, 50, 10)
    
    # Store custom config
    custom_config = {
        "cpu_limit": cpu_cores,
        "memory_limit": f"{memory_gb}Gi",
        "storage_size": f"{storage_gb}Gi"
    }
    
    st.session_state.custom_config = custom_config
    
    # Preview configuration
    st.markdown("**Configuration Preview:**")
    st.code(f"CPU: {cpu_cores} cores\nMemory: {memory_gb}GB\nStorage: {storage_gb}GB")
    
    if st.button("Launch Custom Environment", type="primary", icon=":material/build:"):
        launch_environment_with_progress("Custom", custom_config)

def show_environment_details(env):
    """Show simple status refresh for environment"""
    env_id = env.get("env_id", env.get("id", "unknown"))
    status = env.get('status', 'Unknown')
    
    # Just show a simple status refresh message
    st.success(f"Environment {env_id[:8]} status refreshed: {status.title()}")
    
    # Auto-close after a moment (optional)
    import time
    time.sleep(1)

def quick_launch_environment(preset_name, selected_storage):
    """Quick launch with preset configuration and storage selection"""
    config = get_preset_config(preset_name)
    
    # Add storage information to config
    if selected_storage and selected_storage.get("selection_type") != "pending":
        config["storage"] = selected_storage
    
    st.session_state.launch_in_progress = True
    launch_environment_with_progress(preset_name, config)
    st.session_state.launch_in_progress = False

def show_launch_interface():
    """Legacy launch interface - now redirects to compact version"""
    show_compact_launch_interface()

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
            st.error("Authentication required. Please login again.")
            return
        
        # Single line progress indicator
        progress_container = st.container()
        with progress_container:
            progress_col1, progress_col2 = st.columns([3, 1])
            with progress_col1:
                progress_text = st.empty()
                progress_bar = st.progress(0)
            with progress_col2:
                status_icon = st.empty()
        
        # Step 1: Validation
        progress_text.text("Validating configuration...")
        status_icon.markdown("⏳")
        progress_bar.progress(25)
        time.sleep(0.3)
        
        # Step 2: API call
        progress_text.text("Launching environment...")
        status_icon.markdown("🚀")
        progress_bar.progress(75)
        
        result = api_client.create_environment(config)
        progress_bar.progress(100)
        
        if result.get("status") in ["created", "existing"]:
            progress_text.text("Launch successful!")
            status_icon.markdown("✅")
            
            if result.get("status") == "existing":
                st.success(f"Environment already exists with {preset} configuration!")
            else:
                st.success(f"Environment created successfully with {preset} configuration!")
                
                # Show storage information for new environments
                if config.get("storage", {}).get("selection_type") == "create_new":
                    st.info("✨ New workspace storage created successfully!")
                elif config.get("storage", {}).get("selection_type") == "existing":
                    storage_name = config.get("storage", {}).get("storage_name", "existing workspace")
                    st.info(f"📁 Using {storage_name}")
            
            env_url = result.get("environment", {}).get("url")
            if env_url:
                st.info(f"Environment URL: {env_url}")
                # Add a direct link button
                if st.button("Open Environment", key="open_new_env", type="primary", icon=":material/launch:"):
                    st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', unsafe_allow_html=True)
            
            st.info("Note: Environment may take a few minutes to fully start. Check the Monitoring tab for status updates.")
            
            # Auto-refresh page after successful launch
            time.sleep(2)
            st.rerun()
            
        else:
            progress_text.text("Launch failed!")
            status_icon.markdown("❌")
            st.error(f"Failed to launch environment. Status: {result.get('status', 'Unknown')}")
            
            # Show helpful error information
            if result.get("message"):
                st.warning(f"Details: {result.get('message')}")
            
            # Add retry button
            if st.button("Retry Launch", key="retry_launch", icon=":material/restart_alt:"):
                st.rerun()
        
    except Exception as e:
        progress_text.text("Error occurred!")
        status_icon.markdown("❌")
        st.error(f"Error launching environment: {str(e)}")
        
        # Add troubleshooting information
        with st.expander("Troubleshooting", icon=":material/help:"):
            st.markdown("""
            **Common issues and solutions:**
            - **Network issues**: Check your internet connection
            - **Authentication**: Try logging out and back in
            - **Resource limits**: Try a smaller configuration
            - **Server busy**: Wait a moment and try again
            """)
        
        # Add retry button for errors too
        if st.button("Retry Launch", key="retry_launch_error", icon=":material/restart_alt:"):
            st.rerun()

def restart_environment(env_id):
    """Restart environment with simplified confirmation"""
    # Single line progress indicator
    progress_container = st.container()
    with progress_container:
        progress_col1, progress_col2 = st.columns([3, 1])
        with progress_col1:
            progress_text = st.empty()
        with progress_col2:
            status_icon = st.empty()
    
    try:
        # Show progress
        progress_text.text("Restarting environment...")
        status_icon.markdown("🔄")
        
        # Use the API client restart method
        result = api_client.restart_environment(env_id=env_id)
        
        if result.get("status") == "success":
            progress_text.text("Restart initiated successfully!")
            status_icon.markdown("✅")
            st.info("Environment is restarting. Please check the Monitoring tab for status updates.")
            
            # Clear confirmation state and refresh page
            st.session_state[f"confirm_restart_{env_id}"] = False
            time.sleep(1)
            st.rerun()
        elif result.get("status") == "error":
            progress_text.text("Restart failed!")
            status_icon.markdown("❌")
            st.error("Failed to restart environment")
            st.warning(f"Details: {result.get('message', 'Unknown error')}")
            st.session_state[f"confirm_restart_{env_id}"] = False
        else:
            # Legacy handling for backward compatibility
            if result.get("status") in ["created", "existing"]:
                progress_text.text("Restart initiated successfully!")
                status_icon.markdown("✅")
                st.info("Environment is restarting. Please check the Monitoring tab for status updates.")
                st.session_state[f"confirm_restart_{env_id}"] = False
                time.sleep(1)
                st.rerun()
            else:
                progress_text.text("Restart failed!")
                status_icon.markdown("❌")
                st.error(f"Failed to restart environment. Status: {result.get('status', 'Unknown')}")
                if result.get("message"):
                    st.warning(f"Details: {result.get('message')}")
                st.session_state[f"confirm_restart_{env_id}"] = False
            
    except Exception as e:
        progress_text.text("Error occurred!")
        status_icon.markdown("❌")
        st.error(f"Error restarting environment: {str(e)}")
        with st.expander("Debug Information", icon=":material/info:"):
            st.write(f"Environment ID: {env_id}")
            st.write(f"Error type: {type(e).__name__}")
            st.write(f"Error details: {str(e)}")
        st.session_state[f"confirm_restart_{env_id}"] = False


def stop_environment(env_id):
    """Stop environment with simplified confirmation"""
    # Single line progress indicator
    progress_container = st.container()
    with progress_container:
        progress_col1, progress_col2 = st.columns([3, 1])
        with progress_col1:
            progress_text = st.empty()
        with progress_col2:
            status_icon = st.empty()
    
    try:
        # Show progress
        progress_text.text("Stopping environment...")
        status_icon.markdown("⏹️")
        
        # Use the API client stop method
        result = api_client.stop_environment(env_id=env_id)
        
        if result.get("status") == "success":
            progress_text.text("Stop initiated successfully!")
            status_icon.markdown("✅")
            st.info("Environment is stopping. Please refresh the page to see updated status.")
            
            # Clear confirmation state and refresh page
            st.session_state[f"confirm_stop_{env_id}"] = False
            time.sleep(1)
            st.rerun()
        elif result.get("status") == "error":
            progress_text.text("Stop failed!")
            status_icon.markdown("❌")
            st.error("Failed to stop environment")
            st.warning(f"Details: {result.get('message', 'Unknown error')}")
            st.session_state[f"confirm_stop_{env_id}"] = False
        else:
            # Legacy handling for backward compatibility
            if result.get("status") == "deleted":
                progress_text.text("Stop initiated successfully!")
                status_icon.markdown("✅")
                st.info("Environment is stopping. Please refresh the page to see updated status.")
                st.session_state[f"confirm_stop_{env_id}"] = False
                time.sleep(1)
                st.rerun()
            else:
                progress_text.text("Stop failed!")
                status_icon.markdown("❌")
                st.error(f"Failed to stop environment. Status: {result.get('status', 'Unknown')}")
                if result.get("message"):
                    st.warning(f"Details: {result.get('message')}")
                st.session_state[f"confirm_stop_{env_id}"] = False
        
    except Exception as e:
        progress_text.text("Error occurred!")
        status_icon.markdown("❌")
        st.error(f"Error stopping environment: {str(e)}")
        with st.expander("Debug Information", icon=":material/info:"):
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
            st.success(f"Environment Status: {env_info.get('status', 'Unknown').title()}")
            with st.expander("Detailed Status", icon=":material/info:"):
                st.json(env_info)
        else:
            st.warning("Environment not found or inactive")
    except Exception as e:
        st.error(f"Error checking status: {str(e)}")

def show_environment_monitoring():
    """Environment monitoring interface"""
    st.markdown("### System Monitoring")
    
    # Manual refresh button
    if st.button("Refresh Status", key="refresh_monitoring", icon=":material/restart_alt:"):
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
    
    # Status card with material design
    if status == "running":
        card_class = "status-card"
        status_indicator = "●"
        status_color = "#28a745"
    elif status == "pending":
        card_class = "warning-card"
        status_indicator = "●"
        status_color = "#ffc107"
    else:
        card_class = "error-card"
        status_indicator = "●"
        status_color = "#dc3545"
    
    st.markdown(f"""
    <div class="{card_class}">
        <h4><span style="color: {status_color};">{status_indicator}</span> Environment {env_id[:8]}</h4>
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
    st.markdown("### Environment Settings")
    
    # Custom configuration
    st.markdown("#### Custom Configuration")
    
    with st.form("custom_config"):
        cpu_limit = st.number_input("CPU Limit", min_value=0.5, max_value=8.0, value=2.0, step=0.5)
        memory_limit = st.selectbox("Memory Limit", ["1Gi", "2Gi", "4Gi", "8Gi", "16Gi"], index=2)
        storage_size = st.selectbox("Storage Size", ["10Gi", "20Gi", "50Gi", "100Gi"], index=1)
        
        if st.form_submit_button(":material/save: Save Configuration"):
            custom_config = {
                "cpu_limit": cpu_limit,
                "memory_limit": memory_limit,
                "storage_size": storage_size
            }
            st.session_state.custom_config = custom_config
            st.success("Custom configuration saved!")
    
    # Display current settings
    if "custom_config" in st.session_state:
        st.markdown("#### Current Custom Configuration")
        st.json(st.session_state.custom_config)

def get_user_environments():
    """Get user environments from API"""
    try:
        response = api_client.list_environments()
        return response.get("environments", [])
    except Exception as e:
        st.error(f"Error fetching environments: {str(e)}")
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

def get_storage_list():
    """Get storage list with caching"""
    try:
        response = api_client.list_user_storages()
        if response.get("status") == "success":
            return response.get("storages", [])
        else:
            return []
    except Exception as e:
        return []

if __name__ == "__main__":
    main()
