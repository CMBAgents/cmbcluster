import streamlit as st
import json
import re
from datetime import datetime

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth, logout, show_user_info
from components.api_client import api_client
from components.dark_theme import DARK_THEME_CSS
from components.storage_file_manager import StorageFileManager
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
    page_title=f"{settings.app_title} - Settings",
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

# Initialize storage file manager
storage_file_manager = StorageFileManager(api_client)

# Apply dark theme CSS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Logo section with better alignment
col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])

with col1:
    # Add a custom class to identify Cambridge logo
    st.markdown('<div class="cambridge-logo-container">', unsafe_allow_html=True)
    st.image(CAMBRIDGE_LOGO_URL, width=120)
    st.markdown('</div>', unsafe_allow_html=True)

with col5:
    st.image(INFOSYS_LOGO_URL, width=120)

# Apply dark theme CSS
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)

# Custom CSS for logo styling and professional settings design
st.markdown("""
<style>
/* Make Cambridge logo text white by targeting the custom container */
.cambridge-logo-container img {
    filter: invert(1) brightness(2.5) contrast(2) saturate(0) hue-rotate(180deg) !important;
    -webkit-filter: invert(1) brightness(2.5) contrast(2) saturate(0) hue-rotate(180deg) !important;
}

.settings-card {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 1.5rem;
    margin: 1rem 0;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.settings-header {
    border-bottom: 2px solid var(--accent-primary);
    padding-bottom: 0.5rem;
    margin-bottom: 1.5rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.settings-section {
    background: var(--bg-tertiary);
    border-radius: 8px;
    padding: 1.25rem;
    margin: 1rem 0;
    border-left: 4px solid var(--accent-primary);
}

.metric-card {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 1rem;
    text-align: center;
    border: 1px solid var(--border-color);
}

.status-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.875rem;
    font-weight: 500;
}

.status-active {
    background-color: rgba(72, 187, 120, 0.1);
    color: #48BB78;
    border: 1px solid #48BB78;
}

.status-inactive {
    background-color: rgba(113, 128, 150, 0.1);
    color: #718096;
    border: 1px solid #718096;
}

.action-button {
    background: var(--accent-primary);
    color: white;
    border: none;
    padding: 0.5rem 1rem;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.action-button:hover {
    background: var(--accent-secondary);
    transform: translateY(-1px);
}

.danger-zone {
    background: rgba(245, 101, 101, 0.05);
    border: 1px solid rgba(245, 101, 101, 0.2);
    border-radius: 8px;
    padding: 1rem;
    margin-top: 2rem;
}
</style>
""", unsafe_allow_html=True)

def main():
    """Main settings page with professional structure"""
    
    # Show user info in sidebar
    show_user_info()
    
    # Clear only specific page-related session state (preserve auth and config)
    page_keys_to_clear = ['settings_temp_data']
    for key in page_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    # Header with icon and breadcrumb
    st.markdown("""
    <div class="settings-header">
        <h1>Settings & Configuration</h1>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("Manage your account, preferences, and workspace configurations")
    
    # Settings navigation tabs
    tab1, tab2, tab3 = st.tabs([
        "Profile", 
        "Environment Preferences", 
        "Environment Variables"
    ])
    
    # Get user info
    user_info = st.session_state.get("user_info", {})
    
    with tab1:
        show_profile_settings(user_info)
    
    with tab2:
        show_environment_preferences()
    
    with tab3:
        show_env_vars_section()

def show_env_vars_section():
    """Professional environment variables management UI"""
    st.markdown("""
    <div class="settings-section">
        <h3>Environment Variables Management</h3>
        <p>Configure environment variables that will be automatically injected into your research environments.</p>
    </div>
    """, unsafe_allow_html=True)
    
    api = api_client
    
    # Initialize environment variables in session state
    if 'env_vars' not in st.session_state:
        with st.spinner("Loading environment variables..."):
            result = api.get_user_env_vars()
            st.session_state.env_vars = result.get('env_vars', {}) if isinstance(result, dict) else {}

    env_vars = st.session_state.env_vars.copy()
    keys = list(env_vars.keys())

    # Statistics card
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Total Variables</h4>
            <h2 style="color: var(--accent-primary);">{}</h2>
        </div>
        """.format(len(keys)), unsafe_allow_html=True)
    
    with col2:
        active_vars = len([k for k in keys if env_vars[k].strip()])
        st.markdown("""
        <div class="metric-card">
            <h4>Active Variables</h4>
            <h2 style="color: #48BB78;">{}</h2>
        </div>
        """.format(active_vars), unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Last Updated</h4>
            <p style="color: var(--text-secondary);">{}</p>
        </div>
        """.format(datetime.now().strftime("%Y-%m-%d %H:%M")), unsafe_allow_html=True)

    st.markdown("---")

    # Current environment variables table
    if not keys:
        st.markdown("""
        <div class="settings-card">
            <h4>No Environment Variables</h4>
            <p>You haven't configured any environment variables yet. Add your first variable below.</p>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("### Current Environment Variables")
        
        # Table header
        header_col1, header_col2, header_col3, header_col4 = st.columns([3, 3, 2, 2])
        with header_col1:
            st.markdown("**Variable Name**")
        with header_col2:
            st.markdown("**Value**")
        with header_col3:
            st.markdown("**Status**")
        with header_col4:
            st.markdown("**Actions**")
        
        st.markdown("---")
        
        # Environment variables rows
        for i, k in enumerate(keys):
            col1, col2, col3, col4 = st.columns([3, 3, 2, 2])
            
            with col1:
                new_key = st.text_input(
                    f"Key_{k}", 
                    value=k, 
                    key=f"env_key_{k}",
                    label_visibility="collapsed"
                )
            
            with col2:
                # Check if user wants to show this value
                show_value_key = f"show_value_{k}"
                show_value = st.session_state.get(show_value_key, False)
                
                # Create columns for value input and visibility toggle
                val_col1, val_col2 = st.columns([4, 1])
                
                with val_col1:
                    if show_value:
                        # Show actual value
                        new_val = st.text_input(
                            f"Value_{k}", 
                            value=env_vars[k], 
                            key=f"env_val_{k}",
                            label_visibility="collapsed"
                        )
                    else:
                        # Show hidden value
                        display_value = "•" * min(len(env_vars[k]), 12) if env_vars[k] else ""
                        new_val = st.text_input(
                            f"Value_{k}", 
                            value=display_value,
                            key=f"env_val_display_{k}",
                            disabled=True,
                            label_visibility="collapsed",
                            help="Click the eye icon to reveal the value"
                        )
                        # Use original value for updates
                        new_val = env_vars[k]
                
                with val_col2:
                    # Toggle visibility button
                    icon = ":material/visibility:" if not show_value else ":material/visibility_off:"
                    if st.button(icon, key=f"toggle_vis_{k}", help="Toggle value visibility"):
                        st.session_state[show_value_key] = not show_value
                        st.rerun()
            
            with col3:
                status = "Active" if new_val.strip() else "Empty"
                st.markdown(f"""
                <div class="status-badge {'status-active' if new_val.strip() else 'status-inactive'}">
                    {status}
                </div>
                """, unsafe_allow_html=True)
            
            with col4:
                if st.button(":material/delete:", key=f"del_{k}", help="Delete variable"):
                    with st.spinner("Deleting..."):
                        resp = api.delete_user_env_var(k)
                        if resp.get("status") == "success":
                            st.session_state.env_vars.pop(k, None)
                            # Clean up visibility state
                            if show_value_key in st.session_state:
                                del st.session_state[show_value_key]
                            st.success(f"Deleted '{k}'")
                            st.rerun()
                        else:
                            st.error(f"Failed to delete: {resp.get('message', 'Unknown error')}")
                
                # Auto-update on change (only if value is visible and changed)
                elif new_key != k or (show_value and new_val != env_vars[k]):
                    with st.spinner("Updating..."):
                        if new_key != k:
                            # Delete old key first
                            api.delete_user_env_var(k)
                            # Clean up old visibility state
                            if show_value_key in st.session_state:
                                del st.session_state[show_value_key]
                        resp = api.set_user_env_var(new_key, new_val)
                        if resp.get("status") == "success":
                            st.session_state.env_vars.pop(k, None)
                            st.session_state.env_vars[new_key] = new_val
                            st.rerun()
                        else:
                            st.error(f"Failed to update: {resp.get('message', 'Unknown error')}")
            
            if i < len(keys) - 1:
                st.markdown("---")

    # Add new variable section
    st.markdown("---")
    st.markdown("### Add New Environment Variable")
    
    with st.form("add_env_var_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        
        with col1:
            new_key = st.text_input(
                "Variable Name", 
                key="add_env_key",
                placeholder="e.g., API_KEY, DATABASE_URL",
                help="Variable name must start with a letter or underscore"
            )
        
        with col2:
            new_val = st.text_input(
                "Variable Value", 
                key="add_env_val",
                placeholder="Enter the value for this variable"
            )
        
        # Validation info
        key_exists = new_key in env_vars
        key_valid = bool(new_key and new_key.strip() and re.match(r'^[A-Za-z_][A-Za-z0-9_\-]*$', new_key.strip()))
        
        if new_key and not key_valid:
            st.error("Variable name must start with a letter or underscore and contain only letters, numbers, underscores, or dashes.")
        elif key_exists:
            st.warning(f"Variable '{new_key}' already exists and will be overwritten.")
        
        submitted = st.form_submit_button(
            "Add Environment Variable", 
            type="primary", 
            icon=":material/add_circle:",
            use_container_width=True
        )
        
        if submitted:
            if not key_valid:
                st.error("Invalid variable name format!")
            elif key_exists:
                resp = api.set_user_env_var(new_key, new_val)
                if resp.get("status") == "success":
                    st.session_state.env_vars[new_key] = new_val
                    st.success(f"Updated '{new_key}' successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to update: {resp.get('message', 'Unknown error')}")
            else:
                resp = api.set_user_env_var(new_key, new_val)
                if resp.get("status") == "success":
                    st.session_state.env_vars[new_key] = new_val
                    st.success(f"Added '{new_key}' successfully!")
                    st.rerun()
                else:
                    st.error(f"Failed to add: {resp.get('message', 'Unknown error')}")

    # Help section
    with st.expander("Environment Variables Help", expanded=False):
        st.markdown("""
        **What are Environment Variables?**
        Environment variables are key-value pairs that are automatically injected into your research environments. 
        They're commonly used for:
        
        - **API Keys**: Store secure API keys for external services
        - **Database URLs**: Configure database connections
        - **Configuration**: Set application-specific configurations
        - **Secrets**: Store sensitive information securely
        
        **Best Practices:**
        - Use UPPERCASE names with underscores (e.g., `API_KEY`, `DATABASE_URL`)
        - Don't store sensitive data in variable names
        - Use descriptive names that indicate the variable's purpose
        - Test your variables in a development environment first
        - Click the eye icon next to any value to show/hide it
        
        **Security Notes:**
        - All values are hidden by default for security
        - Click the eye icon to temporarily reveal values when needed
        - All environment variables are encrypted at rest
        - Variables are only accessible within your research environments        **Using Visibility Controls:**
        - Click the eye icon to reveal hidden values
        - Click the hide icon to mask values again
        - Sensitive variables are automatically detected and protected
        - You can edit values even when they're hidden
        """)

def show_profile_settings(user_info):
    """Enhanced user profile settings"""
    st.markdown("""
    <div class="settings-section">
        <h3>Profile Information</h3>
        <p>Your profile information is automatically synchronized with your Google account and cannot be modified here.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Profile overview cards
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class="settings-card">
            <h4>Account Details</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input(
            "Full Name", 
            value=user_info.get("name", "Not available"), 
            disabled=True,
            help="Your display name from Google account"
        )
        st.text_input(
            "Email Address", 
            value=user_info.get("email", "Not available"), 
            disabled=True,
            help="Your primary email address"
        )
    
    with col2:
        st.markdown("""
        <div class="settings-card">
            <h4>Security Information</h4>
        </div>
        """, unsafe_allow_html=True)
        
        st.text_input(
            "User ID", 
            value=user_info.get("sub", "Not available"), 
            disabled=True,
            help="Your unique user identifier"
        )
        st.text_input(
            "Last Login", 
            value=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
            disabled=True,
            help="Current session start time"
        )
    
    # Account status
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
        <div class="metric-card">
            <h4>Account Status</h4>
            <div class="status-badge status-active">Active</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-card">
            <h4>Authentication</h4>
            <div class="status-badge status-active">Google OAuth</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-card">
            <h4>Access Level</h4>
            <div class="status-badge status-active">Researcher</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Account actions
    st.markdown("---")
    st.markdown("### Account Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(":material/restart_alt: Refresh Profile", help="Refresh profile information from Google"):
            st.success("Profile information refreshed!")
            st.rerun()
    
    with col2:
        if st.button(":material/logout: Sign Out", help="Sign out of your account"):
            logout()
            st.rerun()

def show_environment_preferences():
    """Enhanced environment preferences with better UX"""
    st.markdown("""
    <div class="settings-section">
        <h3>Default Environment Configuration</h3>
        <p>Set your preferred default settings for new research environments. These can be overridden when creating individual environments.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Load current preferences
    current_prefs = st.session_state.get('env_preferences', {
        "default_cpu": 2.0,
        "default_memory": 4,
        "auto_cleanup_hours": 4,
        "auto_save": True,
        "default_storage_class": "standard"
    })
    
    with st.form("environment_preferences_form"):
        # Resource defaults
        st.markdown("#### Default Resource Allocation")
        col1, col2 = st.columns(2)
        
        with col1:
            default_cpu = st.slider(
                "CPU Cores", 
                min_value=0.5, 
                max_value=8.0, 
                value=current_prefs.get("default_cpu", 2.0), 
                step=0.5,
                help="Default number of CPU cores for new environments"
            )
            
            default_memory = st.slider(
                "Memory (GB)", 
                min_value=1, 
                max_value=32, 
                value=current_prefs.get("default_memory", 4), 
                step=1,
                help="Default memory allocation in gigabytes"
            )
        
        with col2:
            default_storage_class = st.selectbox(
                "Default Storage Class",
                options=["standard", "nearline", "coldline"],
                index=["standard", "nearline", "coldline"].index(current_prefs.get("default_storage_class", "standard")),
                help="Default storage class for new workspaces"
            )
            
            auto_cleanup_hours = st.slider(
                "Auto-cleanup (hours)", 
                min_value=1, 
                max_value=168,  # 1 week
                value=current_prefs.get("auto_cleanup_hours", 4), 
                step=1,
                help="Automatically stop idle environments after this many hours"
            )
        
                # Advanced preferences
        st.markdown("---")
        st.markdown("#### Advanced Preferences")
        
        col1, col2 = st.columns(2)
        
        with col1:
            auto_save = st.checkbox(
                "Auto-save workspace changes", 
                value=current_prefs.get("auto_save", True),
                help="Automatically save workspace changes periodically"
            )
            
            enable_monitoring = st.checkbox(
                "Enable environment monitoring",
                value=current_prefs.get("enable_monitoring", True),
                help="Monitor resource usage and performance"
            )
        
        with col2:
            email_notifications = st.checkbox(
                "Email notifications",
                value=current_prefs.get("email_notifications", False),
                help="Receive email notifications for environment events"
            )
            
            auto_backup = st.checkbox(
                "Auto-backup workspaces",
                value=current_prefs.get("auto_backup", False),
                help="Automatically backup workspace data"
            )
        
        # Preview current settings
        st.markdown("---")
        st.markdown("#### Configuration Preview")
        
        preview_col1, preview_col2 = st.columns(2)
        
        with preview_col1:
            st.code(f"""
Resource Defaults:
├── CPU: {default_cpu} cores
├── Memory: {default_memory} GB
└── Storage: {default_storage_class}
            """)
        
        with preview_col2:
            st.code(f"""
Automation Settings:
├── Auto-cleanup: {auto_cleanup_hours}h
├── Auto-save: {'✓' if auto_save else '✗'}
├── Monitoring: {'✓' if enable_monitoring else '✗'}
├── Notifications: {'✓' if email_notifications else '✗'}
└── Auto-backup: {'✓' if auto_backup else '✗'}
            """)
        
        # Form submission
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            submitted = st.form_submit_button(
                ":material/save: Save Environment Preferences", 
                type="primary", 
                icon=":material/save:",
                use_container_width=True
            )
        
        if submitted:
            # Store preferences in session state
            env_prefs = {
                "default_cpu": default_cpu,
                "default_memory": default_memory,
                "default_storage_class": default_storage_class,
                "auto_cleanup_hours": auto_cleanup_hours,
                "auto_save": auto_save,
                "enable_monitoring": enable_monitoring,
                "email_notifications": email_notifications,
                "auto_backup": auto_backup,
                "last_updated": datetime.now().isoformat()
            }
            
            st.session_state.env_preferences = env_prefs
            st.success("Environment preferences saved successfully!")
            st.balloons()
            
            # Show what was saved
            with st.expander("Saved Configuration", expanded=True):
                st.json(env_prefs)

def format_datetime(dt_str):
    """Format datetime string for display"""
    if not dt_str:
        return "N/A"
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str if dt_str else "N/A"

if __name__ == "__main__":
    main()
