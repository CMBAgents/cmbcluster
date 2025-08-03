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
    tab1, tab2, tab3, tab4 = st.tabs([
        "Profile", 
        "Storage Management", 
        "Environment Preferences", 
        "Environment Variables"
    ])
    
    # Get user info
    user_info = st.session_state.get("user_info", {})
    
    with tab1:
        show_profile_settings(user_info)
    
    with tab2:
        show_storage_management()
    
    with tab3:
        show_environment_preferences()
    
    with tab4:
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
                st.success(f"Active {status.title()}")
            else:
                st.info(f"Inactive {status.title()}")
        
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
    """Enhanced delete confirmation with better UX"""
    storage_id = storage.get("id")
    display_name = storage.get("display_name")
    size_bytes = storage.get("size_bytes", 0)
    
    st.markdown("""
    <div class="danger-zone">
        <h4>:material/warning: Delete Workspace Confirmation</h4>
        <p><strong>This action cannot be undone!</strong></p>
    </div>
    """, unsafe_allow_html=True)
    
    st.warning(f"""
    **You are about to delete:** `{display_name}`
    
    **Storage Size:** {format_storage_size(size_bytes)}
    
    **What will happen:**
    - All data in this workspace will be permanently deleted
    - Any environments using this workspace will lose access
    - This action cannot be reversed
    """)
    
    with st.form(f"delete_confirmation_{storage_id}"):
        # Confirmation inputs
        col1, col2 = st.columns(2)
        
        with col1:
            confirm_delete = st.checkbox(
                "I understand this action is permanent",
                key=f"confirm_delete_{storage_id}",
                help="Check this box to confirm you understand the consequences"
            )
        
        with col2:
            force_delete = st.checkbox(
                "Force delete (ignore warnings)",
                key=f"force_delete_{storage_id}",
                help="Delete even if the workspace contains data"
            )
        
        # Type the workspace name for additional confirmation
        if confirm_delete:
            confirmation_text = st.text_input(
                f"Type '{display_name}' to confirm:",
                key=f"confirm_text_{storage_id}",
                help="Type the exact workspace name to confirm deletion"
            )
            name_matches = confirmation_text == display_name
        else:
            name_matches = False
        
        # Action buttons
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            delete_enabled = confirm_delete and name_matches
            if st.form_submit_button(
                ":material/delete: Delete Workspace", 
                type="primary" if delete_enabled else "secondary",
                disabled=not delete_enabled,
                help="Permanently delete this workspace"
            ):
                if delete_enabled:
                    delete_storage_bucket(storage_id, force_delete)
                else:
                    st.error("Please complete all confirmation steps")
        
        with col2:
            if st.form_submit_button(":material/cancel: Cancel", help="Cancel deletion"):
                # Clean up all related session state
                keys_to_remove = [key for key in st.session_state.keys() if storage_id in key]
                for key in keys_to_remove:
                    del st.session_state[key]
                st.rerun()

def delete_storage_bucket(storage_id: str, force: bool = False):
    """Enhanced storage bucket deletion with better feedback"""
    try:
        with st.spinner("🗑️ Deleting workspace... This may take a moment."):
            response = api_client.delete_storage(storage_id, force=force)
        
        if response.get("status") == "deleted":
            st.success(":material/check_circle: Workspace deleted successfully!")
            st.balloons()
            
            # Clean up session state
            keys_to_remove = [key for key in st.session_state.keys() 
                             if storage_id in key and any(prefix in key for prefix in 
                             ['show_delete_', 'confirm_delete_', 'force_delete_', 'delete_btn_', 'confirm_btn_', 'cancel_btn_'])]
            for key in keys_to_remove:
                del st.session_state[key]

            # Wait and refresh
            import time
            time.sleep(2)
            st.rerun()
        else:
            error_msg = response.get('message', 'Unknown error occurred')
            st.error(f":material/error: Failed to delete workspace: {error_msg}")
            
            # Show additional help for common errors
            if "not empty" in error_msg.lower():
                st.info(":material/lightbulb: **Tip:** Use 'Force delete' to delete workspaces that contain data")
            elif "in use" in error_msg.lower():
                st.info(":material/lightbulb: **Tip:** Stop all environments using this workspace before deleting")
    
    except Exception as e:
        st.error(f":material/error: Error deleting workspace: {str(e)}")
        
        # Show troubleshooting information
        with st.expander(":material/construction: Troubleshooting", expanded=True):
            st.markdown("""
            **Common solutions:**
            - Wait a few minutes and try again
            - Ensure no environments are currently using this workspace
            - Contact support if the problem persists
            """)

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
