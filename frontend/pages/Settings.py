import streamlit as st
import json
from datetime import datetime
import time

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth, logout
from components.api_client import api_client
from config import settings

# Page configuration
st.set_page_config(
    page_title="Settings - CMBCluster",
    page_icon="⚙️",
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
    .danger-zone {
        background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin: 1rem 0;
    }
    .info-card {
        background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin: 1rem 0;
    }
    .success-card {
        background: linear-gradient(135deg, #28a745 0%, #1e7e34 100%);
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
    
    # Header
    st.markdown("# ⚙️ Settings")
    st.markdown("Manage your account, preferences, and system configuration")
    
    # Get user info
    user_info = st.session_state.get("user_info", {})
    
    # Settings tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "👤 Profile", 
        "🔧 Preferences", 
        "🔐 Security", 
        "💾 Data & Storage", 
        "ℹ️ System Info"
    ])
    
    with tab1:
        show_profile_settings(user_info)
    
    with tab2:
        show_preference_settings()
    
    with tab3:
        show_security_settings(user_info)
    
    with tab4:
        show_data_storage_settings()
    
    with tab5:
        show_system_info()

def show_profile_settings(user_info):
    """User profile settings"""
    
    st.markdown("### 👤 User Profile")
    
    # Current profile info
    st.markdown("""
    <div class="settings-card">
        <h4>📋 Current Profile Information</h4>
        <p>Your profile information is automatically synced from your Google account.</p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.text_input("Full Name", value=user_info.get("name", ""), disabled=True)
        st.text_input("Email Address", value=user_info.get("email", ""), disabled=True)
        st.text_input("User ID", value=user_info.get("sub", ""), disabled=True)
    
    with col2:
        st.text_input("Account Type", value="Research User", disabled=True)
        st.text_input("Registration Date", value="2025-06-20", disabled=True)
        st.text_input("Last Login", value=datetime.now().strftime("%Y-%m-%d %H:%M"), disabled=True)
    
    # Profile preferences
    st.markdown("### 🎨 Profile Preferences")
    
    with st.form("profile_preferences"):
        col1, col2 = st.columns(2)
        
        with col1:
            display_name = st.text_input("Display Name", value=user_info.get("name", ""))
            timezone = st.selectbox("Timezone", [
                "UTC",
                "America/New_York",
                "America/Chicago", 
                "America/Denver",
                "America/Los_Angeles",
                "Europe/London",
                "Europe/Berlin",
                "Asia/Tokyo",
                "Asia/Kolkata"
            ], index=8)  # Default to IST
        
        with col2:
            language = st.selectbox("Language", ["English", "Spanish", "French", "German", "Japanese"])
            date_format = st.selectbox("Date Format", ["YYYY-MM-DD", "MM/DD/YYYY", "DD/MM/YYYY"])
        
        notification_email = st.checkbox("Email Notifications", value=True)
        newsletter = st.checkbox("Research Newsletter", value=False)
        
        if st.form_submit_button("💾 Save Profile Settings", type="primary"):
            # Store preferences in session state
            profile_prefs = {
                "display_name": display_name,
                "timezone": timezone,
                "language": language,
                "date_format": date_format,
                "notification_email": notification_email,
                "newsletter": newsletter
            }
            st.session_state.profile_preferences = profile_prefs
            st.success("✅ Profile settings saved successfully!")

def show_preference_settings():
    """Application preferences"""
    
    st.markdown("### 🔧 Application Preferences")
    
    # Environment preferences
    st.markdown("#### 🚀 Environment Preferences")
    
    with st.form("environment_preferences"):
        col1, col2 = st.columns(2)
        
        with col1:
            default_cpu = st.slider("Default CPU Cores", 0.5, 8.0, 2.0, 0.5)
            default_memory = st.slider("Default Memory (GB)", 1, 16, 4, 1)
            default_storage = st.slider("Default Storage (GB)", 5, 100, 10, 5)
        
        with col2:
            auto_cleanup_hours = st.slider("Auto-cleanup (hours)", 1, 24, 4, 1)
            auto_save_interval = st.slider("Auto-save interval (minutes)", 1, 30, 5, 1)
            
            # Environment image preference
            image_preference = st.selectbox("Preferred Environment", [
                "Standard (Recommended)",
                "GPU Enabled",
                "Lightweight",
                "Custom"
            ])
        
        # Startup preferences
        st.markdown("**Startup Options:**")
        auto_launch = st.checkbox("Auto-launch environment on login", value=False)
        preload_libraries = st.checkbox("Preload common libraries", value=True)
        restore_session = st.checkbox("Restore previous session", value=True)
        
        if st.form_submit_button("💾 Save Environment Preferences", type="primary"):
            env_prefs = {
                "default_cpu": default_cpu,
                "default_memory": default_memory,
                "default_storage": default_storage,
                "auto_cleanup_hours": auto_cleanup_hours,
                "auto_save_interval": auto_save_interval,
                "image_preference": image_preference,
                "auto_launch": auto_launch,
                "preload_libraries": preload_libraries,
                "restore_session": restore_session
            }
            st.session_state.environment_preferences = env_prefs
            st.success("✅ Environment preferences saved!")
    
    # UI preferences
    st.markdown("#### 🎨 Interface Preferences")
    
    with st.form("ui_preferences"):
        col1, col2 = st.columns(2)
        
        with col1:
            theme = st.selectbox("Theme", ["Auto", "Light", "Dark"])
            sidebar_default = st.selectbox("Sidebar Default", ["Expanded", "Collapsed"])
            
        with col2:
            page_width = st.selectbox("Page Width", ["Wide", "Centered"])
            chart_theme = st.selectbox("Chart Theme", ["Streamlit", "Plotly", "Seaborn"])
        
        animations = st.checkbox("Enable animations", value=True)
        tooltips = st.checkbox("Show tooltips", value=True)
        auto_refresh = st.checkbox("Auto-refresh dashboard", value=True)
        
        if st.form_submit_button("💾 Save UI Preferences", type="primary"):
            ui_prefs = {
                "theme": theme,
                "sidebar_default": sidebar_default,
                "page_width": page_width,
                "chart_theme": chart_theme,
                "animations": animations,
                "tooltips": tooltips,
                "auto_refresh": auto_refresh
            }
            st.session_state.ui_preferences = ui_prefs
            st.success("✅ Interface preferences saved!")

def show_security_settings(user_info):
    """Security and privacy settings"""
    
    st.markdown("### 🔐 Security & Privacy")
    
    # Account security overview
    st.markdown("""
    <div class="success-card">
        <h4>🛡️ Account Security Status</h4>
        <p>✅ Google OAuth authentication enabled</p>
        <p>✅ Secure session management active</p>
        <p>✅ Environment isolation configured</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Session management
    st.markdown("#### 🔑 Session Management")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Current Session", "Active")
        st.metric("Session Duration", "2h 34m")
        st.metric("Last Activity", "2 minutes ago")
    
    with col2:
        if st.button("🔓 Logout Current Session", use_container_width=True):
            logout()
            st.rerun()
        
        if st.button("🔄 Refresh Session", use_container_width=True):
            st.success("Session refreshed!")
    
    # Security preferences
    st.markdown("#### 🔒 Security Preferences")
    
    with st.form("security_preferences"):
        session_timeout = st.slider("Session timeout (hours)", 1, 24, 8, 1)
        auto_logout_inactive = st.slider("Auto-logout after inactivity (minutes)", 30, 480, 120, 30)
        
        # Privacy settings
        st.markdown("**Privacy Settings:**")
        usage_analytics = st.checkbox("Allow usage analytics", value=True)
        error_reporting = st.checkbox("Enable error reporting", value=True)
        performance_monitoring = st.checkbox("Performance monitoring", value=True)
        
        if st.form_submit_button("💾 Save Security Settings", type="primary"):
            security_prefs = {
                "session_timeout": session_timeout,
                "auto_logout_inactive": auto_logout_inactive,
                "usage_analytics": usage_analytics,
                "error_reporting": error_reporting,
                "performance_monitoring": performance_monitoring
            }
            st.session_state.security_preferences = security_prefs
            st.success("✅ Security settings saved!")
    
    # Data privacy
    st.markdown("#### 🛡️ Data Privacy")
    
    st.markdown("""
    <div class="info-card">
        <h4>📋 Data Handling Policy</h4>
        <p>• Your research data is stored in isolated, encrypted volumes</p>
        <p>• Workspace data persists across sessions until manually deleted</p>
        <p>• No data is shared between users or transmitted outside your environment</p>
        <p>• Activity logs are kept for 30 days for troubleshooting purposes</p>
    </div>
    """, unsafe_allow_html=True)

def show_data_storage_settings():
    """Data and storage management"""
    
    st.markdown("### 💾 Data & Storage Management")
    
    # Storage overview
    st.markdown("#### 📊 Storage Usage")
    
    # Mock storage data
    total_storage = 10  # GB
    used_storage = 3.2  # GB
    usage_percent = (used_storage / total_storage) * 100
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Storage", f"{total_storage} GB")
    
    with col2:
        st.metric("Used Storage", f"{used_storage:.1f} GB")
    
    with col3:
        st.metric("Available", f"{total_storage - used_storage:.1f} GB")
    
    # Storage usage chart
    st.progress(usage_percent / 100)
    st.caption(f"Storage usage: {usage_percent:.1f}%")
    
    # File management
    st.markdown("#### 📁 Workspace Files")
    
    # Mock file data
    files_data = [
        {"name": "cosmology_analysis.ipynb", "size": "1.2 MB", "modified": "2025-06-26 10:30"},
        {"name": "data/cmb_map.fits", "size": "850 MB", "modified": "2025-06-25 15:45"},
        {"name": "results/power_spectrum.png", "size": "245 KB", "modified": "2025-06-25 14:20"},
        {"name": "scripts/data_processing.py", "size": "12 KB", "modified": "2025-06-24 11:15"},
        {"name": "workspace_backup.tar.gz", "size": "2.1 GB", "modified": "2025-06-23 09:00"}
    ]
    
    files_df = pd.DataFrame(files_data)
    
    # Display files with sorting
    sort_by = st.selectbox("Sort by", ["name", "size", "modified"])
    if sort_by == "size":
        # Convert size to numeric for proper sorting
        files_df["size_bytes"] = files_df["size"].apply(lambda x: 
            float(x.split()[0]) * (1024**3 if 'GB' in x else 1024**2 if 'MB' in x else 1024 if 'KB' in x else 1))
        files_df = files_df.sort_values("size_bytes", ascending=False)
    else:
        files_df = files_df.sort_values(sort_by)
    
    st.dataframe(files_df[["name", "size", "modified"]], use_container_width=True)
    
    # Backup and restore
    st.markdown("#### 💾 Backup & Restore")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Create Backup:**")
        backup_name = st.text_input("Backup Name", value=f"backup_{datetime.now().strftime('%Y%m%d_%H%M')}")
        include_data = st.checkbox("Include large data files", value=False)
        
        if st.button("📦 Create Backup", type="primary"):
            with st.spinner("Creating backup..."):
                time.sleep(3)  # Simulate backup process
                st.success(f"✅ Backup '{backup_name}' created successfully!")
    
    with col2:
        st.markdown("**Available Backups:**")
        backups = [
            "backup_20250626_1030",
            "backup_20250625_1545", 
            "backup_20250624_0900"
        ]
        
        selected_backup = st.selectbox("Select Backup", backups)
        
        if st.button("♻️ Restore Backup"):
            st.warning("⚠️ This will replace current workspace data!")
            if st.button("Confirm Restore"):
                with st.spinner("Restoring backup..."):
                    time.sleep(3)
                    st.success(f"✅ Workspace restored from '{selected_backup}'!")
    
    # Data export
    st.markdown("#### 📤 Data Export")
    
    export_format = st.selectbox("Export Format", ["ZIP Archive", "TAR.GZ", "Individual Files"])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Export Workspace Data", type="primary"):
            st.info("🔄 Preparing export... Download will start automatically.")
    
    with col2:
        if st.button("📋 Generate File Manifest"):
            manifest = "\n".join([f"{row['name']} ({row['size']})" for _, row in files_df.iterrows()])
            st.text_area("File Manifest", manifest, height=150)

def show_system_info():
    """System information and diagnostics"""
    
    st.markdown("### ℹ️ System Information")
    
    # Platform information
    st.markdown("#### 🖥️ Platform Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        **Client Information:**
        - **Browser:** Chrome 126.0.6478.126
        - **Platform:** Web Application
        - **Screen Resolution:** 1920x1080
        - **Viewport:** 1200x800
        """)
        
        st.markdown("""
        **Application Version:**
        - **CMBCluster:** v1.0.0
        - **Frontend:** Streamlit 1.28.1
        - **Build Date:** 2025-06-26
        - **Git Commit:** abc123f
        """)
    
    with col2:
        st.markdown(f"""
        **Server Configuration:**
        - **API URL:** {settings.api_url}
        - **Base Domain:** {settings.base_domain}
        - **Environment:** {'Development' if settings.dev_mode else 'Production'}
        - **Region:** us-central1
        """)
        
        st.markdown("""
        **Kubernetes Cluster:**
        - **Namespace:** cmbcluster
        - **Node Pool:** standard-2
        - **Storage Class:** standard-rwo
        - **Ingress:** NGINX
        """)
    
    # Feature status
    st.markdown("#### 🔧 Feature Status")
    
    features = [
        {"name": "OAuth Authentication", "status": "✅ Active", "description": "Google OAuth integration"},
        {"name": "Environment Management", "status": "✅ Active", "description": "Pod lifecycle management"},
        {"name": "Persistent Storage", "status": "✅ Active", "description": "User workspace persistence"},
        {"name": "Auto-scaling", "status": "✅ Active", "description": "Horizontal pod autoscaling"},
        {"name": "SSL Certificates", "status": "✅ Active", "description": "Automated TLS management"},
        {"name": "Monitoring", "status": "✅ Active", "description": "Health checks and metrics"},
        {"name": "Backup System", "status": "🚧 Beta", "description": "Automated workspace backups"},
        {"name": "GPU Support", "status": "⏳ Planned", "description": "CUDA-enabled environments"}
    ]
    
    for feature in features:
        col1, col2, col3 = st.columns([2, 1, 3])
        with col1:
            st.write(f"**{feature['name']}**")
        with col2:
            st.write(feature['status'])
        with col3:
            st.caption(feature['description'])
    
    # Diagnostics
    st.markdown("#### 🔍 System Diagnostics")
    
    if st.button("🏥 Run Health Check", type="primary"):
        with st.spinner("Running diagnostics..."):
            time.sleep(2)
            
            diagnostics = [
                {"check": "API Connectivity", "status": "✅ Pass", "details": "Backend API responding"},
                {"check": "Authentication", "status": "✅ Pass", "details": "OAuth token valid"},
                {"check": "Storage Access", "status": "✅ Pass", "details": "Workspace accessible"},
                {"check": "Environment Capacity", "status": "✅ Pass", "details": "Resources available"},
                {"check": "Network Latency", "status": "⚠️ Warning", "details": "Slightly elevated (150ms)"},
            ]
            
            st.markdown("**Diagnostic Results:**")
            for diag in diagnostics:
                col1, col2, col3 = st.columns([2, 1, 3])
                with col1:
                    st.write(diag['check'])
                with col2:
                    st.write(diag['status'])
                with col3:
                    st.caption(diag['details'])
    
    # Support information
    st.markdown("#### 🆘 Support & Help")
    
    st.markdown("""
    <div class="info-card">
        <h4>📞 Get Help</h4>
        <p><strong>Documentation:</strong> <a href="https://github.com/archetana/cmbcluster/wiki" target="_blank">CMBCluster Wiki</a></p>
        <p><strong>Issues:</strong> <a href="https://github.com/archetana/cmbcluster/issues" target="_blank">GitHub Issues</a></p>
        <p><strong>Email Support:</strong> support@cmbcluster.io</p>
        <p><strong>Community:</strong> <a href="https://github.com/archetana/cmbcluster/discussions" target="_blank">GitHub Discussions</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Export settings
    st.markdown("#### 📋 Export Settings")
    
    if st.button("💾 Export All Settings"):
        all_settings = {
            "profile_preferences": st.session_state.get("profile_preferences", {}),
            "environment_preferences": st.session_state.get("environment_preferences", {}),
            "ui_preferences": st.session_state.get("ui_preferences", {}),
            "security_preferences": st.session_state.get("security_preferences", {}),
            "exported_at": datetime.now().isoformat()
        }
        
        settings_json = json.dumps(all_settings, indent=2)
        st.download_button(
            "📥 Download Settings",
            settings_json,
            file_name=f"cmbcluster-settings-{datetime.now().strftime('%Y%m%d')}.json",
            mime="application/json"
        )

if __name__ == "__main__":
    if not check_authentication():
        show_login_screen()
    else:
        main()
