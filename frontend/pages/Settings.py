import streamlit as st
import json
from datetime import datetime

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth, logout, show_user_info
from components.api_client import api_client
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

col1, col2, col3 = st.columns([1, 2, 1])

with col1:
    st.image(CAMBRIDGE_LOGO_URL, width=120)

with col3:
    st.image(INFOSYS_LOGO_URL, width=120) 

# Page configuration
st.set_page_config(
    page_title=settings.app_title,
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .settings-card {
        background: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@require_auth
def main():
    """Main settings page"""
    
    # Show user info in sidebar
    show_user_info()
    
    # Clear only specific page-related session state (preserve auth and config)
    page_keys_to_clear = ['settings_temp_data']
    for key in page_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.empty()
    
    # Header
    st.markdown("# ⚙️ Settings")
    st.markdown("Manage your account and preferences")
    
    # Get user info
    user_info = st.session_state.get("user_info", {})
    
    # Settings sections
    st.markdown("## 👤 Profile")
    show_profile_settings(user_info)
    
    st.divider()
    
    st.markdown("## 🔧 Environment Preferences") 
    show_environment_preferences()
    
    st.divider()
    
    st.divider()
    st.markdown("## 🌱 Environment Variables")
    show_env_vars_section()
    st.divider()
    st.markdown("## 🔐 Security")
    show_security_settings()
    st.divider()
    st.markdown("## ℹ️ System Information")
    show_system_info()

def show_env_vars_section():
    """User environment variables management UI"""
    st.markdown("Manage environment variables that will be injected into your research environment.")
    api = api_client
    if 'env_vars' not in st.session_state:
        # Fetch from backend
        result = api.get_user_env_vars()
        st.session_state.env_vars = result.get('env_vars', {}) if isinstance(result, dict) else {}

    env_vars = st.session_state.env_vars.copy()
    keys = list(env_vars.keys())

    # Inline editing table
    st.write("**Current Environment Variables:**")
    if not keys:
        st.info("No environment variables set.")
    else:
        for k in keys:
            cols = st.columns([4, 4, 1])
            new_key = cols[0].text_input(f"Key_{k}", value=k, key=f"env_key_{k}")
            new_val = cols[1].text_input(f"Value_{k}", value=env_vars[k], key=f"env_val_{k}")
            if cols[2].button("🗑️", key=f"del_{k}"):
                resp = api.delete_user_env_var(new_key)
                if resp.get("status") == "success":
                    st.session_state.env_vars.pop(k, None)
                    st.rerun()
                else:
                    st.error(f"Failed to delete variable: {resp.get('message', 'Unknown error')}")
            elif new_key != k or new_val != env_vars[k]:
                # Update if changed
                resp = api.set_user_env_var(new_key, new_val)
                if resp.get("status") == "success":
                    st.session_state.env_vars.pop(k, None)
                    st.session_state.env_vars[new_key] = new_val
                    st.rerun()
                else:
                    st.error(f"Failed to update variable: {resp.get('message', 'Unknown error')}")

    st.markdown("---")
    st.write("**Add New Variable:**")
    import re
    with st.form("add_env_var_form"):
        new_key = st.text_input("Key", key="add_env_key")
        new_val = st.text_input("Value", key="add_env_val")
        submitted = st.form_submit_button("Add")
        key_exists = new_key in env_vars
        # Key validation: not empty, not whitespace, valid chars (alphanum, _, -)
        key_valid = bool(new_key and new_key.strip() and re.match(r'^[A-Za-z_][A-Za-z0-9_\-]*$', new_key.strip()))
        if submitted:
            if not key_valid:
                st.error("Key must start with a letter or underscore and contain only letters, numbers, underscores, or dashes.")
            elif key_exists:
                if st.confirm(f"Key '{new_key}' already exists. Overwrite?"):
                    resp = api.set_user_env_var(new_key, new_val)
                    if resp.get("status") == "success":
                        st.session_state.env_vars[new_key] = new_val
                        st.success(f"Overwritten {new_key}")
                        st.rerun()
                    else:
                        st.error(f"Failed to overwrite variable: {resp.get('message', 'Unknown error')}")
            else:
                resp = api.set_user_env_var(new_key, new_val)
                if resp.get("status") == "success":
                    st.session_state.env_vars[new_key] = new_val
                    st.success(f"Added {new_key}")
                    st.rerun()
                else:
                    st.error(f"Failed to add variable: {resp.get('message', 'Unknown error')}")
def show_profile_settings(user_info):
    """User profile settings"""
    
    # Current profile info
    st.markdown("""
    <div class="settings-card">
        <h4>📋 Profile Information</h4>
        <p>Your profile is automatically synced from your Google account.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Name", value=user_info.get("name", ""), disabled=True)
        st.text_input("Email", value=user_info.get("email", ""), disabled=True)
    
    with col2:
        st.text_input("User ID", value=user_info.get("sub", ""), disabled=True)
        st.text_input("Last Login", value=datetime.now().strftime("%Y-%m-%d %H:%M"), disabled=True)

def show_environment_preferences():
    """Environment preferences"""
    
    with st.form("environment_preferences"):
        st.markdown("**Default Environment Settings:**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            default_cpu = st.slider("CPU Cores", 0.5, 8.0, 2.0, 0.5)
            default_memory = st.slider("Memory (GB)", 1, 16, 4, 1)
        
        with col2:
            auto_cleanup_hours = st.slider("Auto-cleanup (hours)", 1, 24, 4, 1)
            auto_save = st.checkbox("Auto-save workspace", value=True)
        
        if st.form_submit_button("💾 Save Preferences", type="primary"):
            # Store preferences in session state
            env_prefs = {
                "default_cpu": default_cpu,
                "default_memory": default_memory,
                "auto_cleanup_hours": auto_cleanup_hours,
                "auto_save": auto_save
            }
            st.session_state.environment_preferences = env_prefs
            st.success("✅ Environment preferences saved!")

def show_security_settings():
    """Security settings"""
    
    # Account security overview
    st.markdown("""
    <div class="info-card">
        <h4>🛡️ Security Status</h4>
        <p>✅ Google OAuth authentication enabled</p>
        <p>✅ Secure session management active</p>
        <p>✅ Environment isolation configured</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Session management
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Session Status", "Active")
    
    with col2:
        if st.button("🔓 Logout", use_container_width=True, key="settings_logout_btn"):
            logout()
            st.rerun()

def show_system_info():
    """System information"""
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **Configuration:**
        - **API URL:** {settings.api_url}
        - **Environment:** {'Development' if settings.dev_mode else 'Production'}
        """)
    
    with col2:
        st.markdown("""
        **Features:**
        - **Authentication:** ✅ Active
        - **Environment Management:** ✅ Active
        - **Persistent Storage:** ✅ Active
        """)
    
    # Export settings
    if st.button("💾 Export Settings", key="settings_export_btn"):
        all_settings = {
            "environment_preferences": st.session_state.get("environment_preferences", {}),
            "exported_at": datetime.now().isoformat()
        }
        
        settings_json = json.dumps(all_settings, indent=2)
        st.download_button(
            "📥 Download Settings",
            settings_json,
            file_name=f"cmbcluster-settings-{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json",
            key="settings_download_btn"
        )

if __name__ == "__main__":
    if not check_authentication():
        show_login_screen()
    else:
        main()
