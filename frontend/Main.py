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
from components.storage_file_manager import StorageFileManager
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

# Initialize storage file manager
storage_file_manager = StorageFileManager(api_client)

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
    
    # Tabs for different views (added Storage tab)
    tab1, tab2, tab3 = st.tabs(["Environments", "Storage", "Monitoring"])
    
    with tab1:
        show_environment_management()
    
    with tab2:
        show_storage_management()
    
    with tab3:
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
                action_col2, action_col3, action_col4 = st.columns(3)
                
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

# ============ STORAGE MANAGEMENT FUNCTIONS ============

def show_storage_management():
    """Enhanced storage management interface"""
    st.markdown("""
    <div class="settings-section">
        <h3>Workspace Storage Management</h3>
        <p>Manage your research workspace storage buckets. Each workspace provides isolated storage for your projects and data.</p>
    </div>
    """, unsafe_allow_html=True)

    # Refresh button and actions
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("### Your Workspaces")
    with col2:
        if st.button(":material/restart_alt: Refresh", key="storage_refresh", help="Refresh storage list"):
            st.rerun()

    # Fetch all storages with loading state
    try:
        with st.spinner("Loading workspaces..."):
            response = api_client.list_user_storages()
            storages = response.get("storages", [])
    except Exception as e:
        st.error(f"Failed to load storage options: {str(e)}")
        storages = []

    # Show storage cards or empty state
    if not storages:
        st.markdown("""
        <div class="settings-card" style="text-align: center; padding: 3rem;">
            <h3>No Workspaces Found</h3>
            <p>You don't have any workspace storage buckets yet. Create your first workspace to get started with your research projects.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        # Storage grid layout
        for i, storage in enumerate(storages):
            show_enhanced_storage_card(storage)

def format_storage_size(size_bytes: int) -> str:
    """Format storage size in human-readable format"""
    if size_bytes == 0:
        return "Empty"
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def show_enhanced_storage_card(storage: dict):
    """Enhanced storage card with better design and information"""
    storage_id = storage.get("id")
    display_name = storage.get("display_name", "Unknown Workspace")
    bucket_name = storage.get("bucket_name", "unknown")
    storage_class = storage.get("storage_class", "standard")
    created_at = storage.get("created_at", "")
    size_bytes = storage.get("size_bytes", 0)
    status = storage.get("status", "unknown").lower()
    
    # Status styling
    status_color = "#48BB78" if status == "active" else "#718096"
    status_icon = "Active" if status == "active" else "Inactive"
    
    with st.container():
        # Use Streamlit components instead of raw HTML
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(display_name)
            st.caption(f"Bucket: {bucket_name}")
        
        with col2:
            if status == 'active':
                st.success("Active")
            else:
                st.info("Inactive")
        
        # Storage details in columns
        detail_col1, detail_col2, detail_col3 = st.columns(3)
        
        with detail_col1:
            st.write("**Storage Class:**")
            st.write(storage_class.title())
        
        with detail_col2:
            st.write("**Size:**")
            st.write(format_storage_size(size_bytes))
        
        with detail_col3:
            st.write("**Created:**")
            st.write(format_datetime(created_at))
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 1])
        
        with col1:
            if st.button("Details", key=f"details_{storage_id}", help="View detailed information"):
                st.session_state[f"show_details_{storage_id}"] = not st.session_state.get(f"show_details_{storage_id}", False)
        
        with col2:
            if st.button(":material/restart_alt: Refresh", key=f"refresh_{storage_id}", help="Refresh this workspace"):
                with st.spinner("Refreshing..."):
                    st.success("Workspace refreshed!")
        
        with col3:
            if st.button(":material/delete: Delete", key=f"delete_{storage_id}", type="secondary", help="Delete this workspace"):
                st.session_state[f"show_delete_{storage_id}"] = True
                st.rerun()
        
        # Show details if requested
        if st.session_state.get(f"show_details_{storage_id}", False):
            with st.expander("Workspace Details", expanded=True):
                # Create tabs for details and file management
                details_tab, files_tab = st.tabs(["📋 Details", "📁 Files"])
                
                with details_tab:
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("**Basic Information:**")
                        details = {
                            "Storage ID": storage_id,
                            "Display Name": display_name,
                            "Bucket Name": bucket_name,
                            "Storage Class": storage_class.title(),
                            "Status": status.title()
                        }
                        for key, value in details.items():
                            st.write(f"**{key}:** {value}")
                    
                    with col2:
                        st.markdown("**Storage Details:**")
                        storage_details = {
                            "Size": format_storage_size(size_bytes),
                            "Created": format_datetime(created_at),
                            "Region": storage.get("region", "Unknown"),
                            "Last Modified": format_datetime(storage.get("updated_at", created_at))
                        }
                        for key, value in storage_details.items():
                            st.write(f"**{key}:** {value}")
                
                with files_tab:
                    # File management interface
                    st.markdown("**File Management**")
                    if status == 'active':
                        storage_file_manager.show_file_browser(storage_id, display_name)
                    else:
                        st.warning("File management is only available for active workspaces.")
        
        # Show delete confirmation if triggered
        if st.session_state.get(f"show_delete_{storage_id}", False):
            show_enhanced_delete_confirmation(storage)
        
        st.markdown("---")

def show_enhanced_delete_confirmation(storage: dict):
    """Simple delete confirmation - deletes workspace directly"""
    storage_id = storage.get("id")
    display_name = storage.get("display_name")
    
    st.warning(f"Deleting workspace: **{display_name}**")
    
    col1, col2 = st.columns([1, 1])
    
    with col1:
        if st.button(":material/delete: Confirm Delete", type="primary", key=f"confirm_delete_{storage_id}"):
            delete_storage_bucket(storage_id, force=True)
    
    with col2:
        if st.button(":material/cancel: Cancel", key=f"cancel_delete_{storage_id}"):
            # Clean up session state
            if f"show_delete_{storage_id}" in st.session_state:
                del st.session_state[f"show_delete_{storage_id}"]
            st.rerun()

def delete_storage_bucket(storage_id: str, force: bool = False):
    """Simple storage bucket deletion"""
    try:
        with st.spinner("Deleting workspace..."):
            response = api_client.delete_storage(storage_id, force=force)
        
        if response.get("status") == "deleted":
            st.success("Workspace deleted successfully!")
            
            # Clean up session state
            keys_to_remove = [key for key in st.session_state.keys() if storage_id in key]
            for key in keys_to_remove:
                del st.session_state[key]
            
            st.rerun()
        else:
            error_msg = response.get('message', 'Unknown error occurred')
            st.error(f"Failed to delete workspace: {error_msg}")
    
    except Exception as e:
        st.error(f"Error deleting workspace: {str(e)}")

def show_enhanced_storage_creation_form():
    """Enhanced storage creation form with better UX"""
    st.markdown("""
    <div class="settings-section">
        <h3>:material/add_circle: Create New Workspace</h3>
        <p>Create a new isolated workspace for your research projects. Each workspace provides secure, dedicated storage.</p>
    </div>
    """, unsafe_allow_html=True)
    
    with st.form("create_storage_form"):
        # Storage configuration
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Storage Configuration:**")
            storage_class = st.selectbox(
                "Storage Class",
                options=["standard", "nearline", "coldline"],
                index=0,
                help="Choose storage class based on your access frequency needs"
            )
            
            # Show storage class information
            storage_info = {
                "standard": ":material/speed: **Standard**: Best for frequently accessed data. Higher cost, instant access.",
                "nearline": ":material/analytics: **Nearline**: Best for data accessed monthly. Lower cost, fast access.",
                "coldline": ":material/ac_unit: **Coldline**: Best for archival data. Lowest cost, slower access."
            }
            st.info(storage_info[storage_class])
        
        with col2:
            st.markdown("**Workspace Options:**")
            auto_backup = st.checkbox(
                "Enable automatic backups",
                value=False,
                help="Automatically create periodic backups of your workspace"
            )
            
            enable_versioning = st.checkbox(
                "Enable file versioning",
                value=True,
                help="Keep multiple versions of files for better data protection"
            )
            
            public_access = st.checkbox(
                "Allow public read access",
                value=False,
                help="⚠️ Make workspace content publicly readable (use with caution)"
            )
        
        # Estimated costs (mock data for demonstration)
        st.markdown("---")
        st.markdown("**Estimated Monthly Costs:**")
        
        cost_estimates = {
            "standard": {"storage": "$0.020/GB", "operations": "$0.004/1K ops"},
            "nearline": {"storage": "$0.010/GB", "operations": "$0.01/1K ops"},
            "coldline": {"storage": "$0.004/GB", "operations": "$0.02/1K ops"}
        }
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Storage Cost", cost_estimates[storage_class]["storage"])
        with col2:
            st.metric("Operations Cost", cost_estimates[storage_class]["operations"])
        
        # Preview configuration
        st.markdown("---")
        st.markdown("**Configuration Summary:**")
        config_preview = f"""
**Storage Class:** {storage_class.title()}
**Auto Backup:** {':material/check: Enabled' if auto_backup else ':material/close: Disabled'}
**File Versioning:** {':material/check: Enabled' if enable_versioning else ':material/close: Disabled'}
**Public Access:** {':material/warning: Enabled' if public_access else ':material/check: Private'}
        """
        st.code(config_preview)
        
        # Warning for public access
        if public_access:
            st.warning(":material/warning: **Security Warning**: Public access will make your workspace content readable by anyone with the URL. Only enable this for non-sensitive data.")
        
        # Create button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                ":material/rocket_launch: Create Workspace", 
                type="primary",
                icon=":material/add_circle:",
                use_container_width=True,
                help="Create a new workspace with the specified configuration"
            )
        
        if submitted:
            create_enhanced_storage(storage_class, auto_backup, enable_versioning, public_access)

def create_enhanced_storage(storage_class: str, auto_backup: bool, enable_versioning: bool, public_access: bool):
    """Enhanced storage creation with better feedback"""
    try:
        with st.spinner(":material/construction: Creating your new workspace... This may take up to 30 seconds."):
            # Show progress steps
            progress_container = st.container()
            with progress_container:
                progress_col1, progress_col2 = st.columns([3, 1])
                with progress_col1:
                    progress_text = st.empty()
                    progress_bar = st.progress(0)
                with progress_col2:
                    status_icon = st.empty()
            
            # Step 1: Validate configuration
            progress_text.text("Validating configuration...")
            status_icon.markdown(":material/schedule:")
            progress_bar.progress(25)
            import time
            time.sleep(0.5)
            
            # Step 2: Create storage bucket
            progress_text.text("Creating storage bucket...")
            status_icon.markdown(":material/construction:")
            progress_bar.progress(50)
            
            response = api_client.create_storage_bucket(
                storage_class=storage_class,
                # Additional parameters would be passed here in a real implementation
            )
            
            # Step 3: Configure settings
            progress_text.text("Configuring workspace settings...")
            status_icon.markdown(":material/tune:")
            progress_bar.progress(75)
            time.sleep(0.3)
            
            # Step 4: Finalize
            progress_text.text("Finalizing workspace...")
            status_icon.markdown(":material/auto_awesome:")
            progress_bar.progress(100)
            time.sleep(0.2)
        
        if response.get("status") == "created":
            progress_text.text("Workspace created successfully!")
            status_icon.markdown(":material/check_circle:")
            
            workspace_name = response.get('display_name', 'New Workspace')
            st.success(f":material/celebration: Workspace '{workspace_name}' created successfully!")
            st.balloons()
            
            # Show workspace details
            with st.expander(":material/analytics: New Workspace Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("**Workspace Information:**")
                    st.write(f"**Name:** {workspace_name}")
                    st.write(f"**Storage Class:** {storage_class.title()}")
                    st.write(f"**Bucket:** {response.get('bucket_name', 'N/A')}")
                
                with col2:
                    st.markdown("**Configuration:**")
                    st.write(f"**Auto Backup:** {':material/check:' if auto_backup else ':material/close:'}")
                    st.write(f"**Versioning:** {':material/check:' if enable_versioning else ':material/close:'}")
                    st.write(f"**Public Access:** {':material/warning: Yes' if public_access else ':material/check: No'}")
            
            # Refresh the page after a delay
            time.sleep(2)
            st.rerun()
        else:
            progress_text.text("Creation failed!")
            status_icon.markdown(":material/error:")
            error_msg = response.get('message', 'Unknown error occurred')
            st.error(f":material/error: Failed to create workspace: {error_msg}")
            
            # Show helpful suggestions
            with st.expander(":material/lightbulb: Troubleshooting", expanded=True):
                st.markdown("""
                **Common solutions:**
                - Check your account permissions
                - Verify you have available storage quota
                - Try again with different settings
                - Contact support if the problem persists
                """)
    
    except Exception as e:
        st.error(f":material/error: Error creating workspace: {str(e)}")
        
        # Show error details for debugging
        with st.expander(":material/construction: Error Details", expanded=False):
            st.code(f"Error Type: {type(e).__name__}\nError Message: {str(e)}")

# ============ END STORAGE MANAGEMENT FUNCTIONS ============
    except Exception as e:
        return []

if __name__ == "__main__":
    main()
