import streamlit as st
import pandas as pd
import yaml
import json
from datetime import datetime
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
    .log-entry {
        background: #212529;
        color: #ffffff;
        padding: 0.5rem;
        border-radius: 0.25rem;
        font-family: 'Courier New', monospace;
        font-size: 0.85rem;
        margin: 0.25rem 0;
        white-space: pre-wrap;
    }
    .status-badge {
        padding: 0.25rem 0.5rem;
        border-radius: 0.25rem;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-running { background: #28a745; color: white; }
    .status-pending { background: #ffc107; color: black; }
    .status-failed { background: #dc3545; color: white; }
</style>
""", unsafe_allow_html=True)

@require_auth
def main():
    """Main environment management page (multi-environment)"""
    st.markdown("# 🚀 Environment Management")
    st.markdown("Manage your research environments, resources, and configuration")

    # List all environments for the user
    envs_data = api_client.list_environments()
    environments = envs_data.get("environments", [])

    if not environments:
        st.info("No environments found. Launch a new environment to get started.")
    else:
        st.markdown("## 🗂️ Your Environments")
        for env in environments:
            show_active_environment_details(env)

    # Get environment status
    status_data = get_environment_status()
    
    # Main layout
    tab1, tab2, tab3, tab4 = st.tabs(["🏠 Overview", "⚙️ Configuration", "📊 Monitoring", "📋 Logs"])
    
    with tab1:
        show_environment_overview(status_data)
    
    with tab2:
        show_environment_configuration(status_data)
    
    with tab3:
        show_environment_monitoring(status_data)
    
    with tab4:
        show_environment_logs(status_data)

def show_environment_overview(status_data):
    """Environment overview tab"""
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.markdown("### 🎯 Current Environment Status")
        
        if status_data.get("active"):
            env_info = status_data.get("environment", {})
            show_active_environment_details(env_info)
        else:
            show_inactive_environment_state()
    
    with col2:
        st.markdown("### 🛠️ Environment Actions")
        show_environment_actions(status_data)
        
        st.markdown("### 📊 Quick Stats")
        show_quick_stats(status_data)

def show_active_environment_details(env_info):
    """Display active environment details"""
    
    # Status badge
    status = env_info.get('status', 'unknown').lower()
    badge_class = f"status-{status}" if status in ['running', 'pending', 'failed'] else "status-running"
    
    st.markdown(f"""
    <div class="env-card">
        <h4>✅ Environment Active</h4>
        <p><strong>Status:</strong> <span class="status-badge {badge_class}">{status.upper()}</span></p>
        <p><strong>Pod Name:</strong> <code>{env_info.get('pod_name', 'Unknown')}</code></p>
        <p><strong>Created At:</strong> {env_info.get('created_at', 'Unknown')}</p>
        <p><strong>Last Activity:</strong> {env_info.get('last_activity', 'Unknown')}</p>
        <p><strong>Access URL:</strong> <a href="{env_info.get('url', '#')}" target="_blank">{env_info.get('url', 'Not available')}</a></p>
    </div>
    """, unsafe_allow_html=True)
    
    # Resource configuration
    resource_config = env_info.get('resource_config', {})
    if resource_config:
        st.markdown("#### 💾 Resource Allocation")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("CPU Limit", f"{resource_config.get('cpu_limit', 'Unknown')} cores")
        
        with col2:
            st.metric("Memory Limit", resource_config.get('memory_limit', 'Unknown'))
        
        with col3:
            st.metric("Storage Size", resource_config.get('storage_size', 'Unknown'))

def show_inactive_environment_state():
    """Display inactive environment state"""
    
    st.markdown("""
    <div class="env-card">
        <h4>❌ No Active Environment</h4>
        <p>Your research environment is currently not running. Launch a new environment to get started.</p>
        <p><strong>Benefits of launching an environment:</strong></p>
        <ul>
            <li>Access to pre-configured cosmology tools</li>
            <li>Persistent workspace storage</li>
            <li>Jupyter notebook integration</li>
            <li>High-performance computing resources</li>
        </ul>
    </div>
    """, unsafe_allow_html=True)

def show_environment_actions(status_data):
    """Display environment action buttons"""
    
    env_active = status_data.get("active", False)
    
    if not env_active:
        st.markdown("#### 🚀 Launch Environment")
        
        # Quick launch options
        preset = st.selectbox("Environment Preset", [
            "Standard Research (2 CPU, 4GB RAM)",
            "Heavy Computation (4 CPU, 8GB RAM)",
            "Light Analysis (1 CPU, 2GB RAM)",
            "Custom Configuration"
        ])
        
        if st.button("🚀 Launch Environment", type="primary", use_container_width=True):
            launch_environment_with_config(preset)
    
    else:
        st.markdown("#### 🔧 Environment Controls")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Restart", use_container_width=True):
                restart_environment()
        
        with col2:
            if st.button("⏹️ Stop", use_container_width=True):
                delete_environment()
        
        env_url = status_data.get("environment", {}).get("url")
        if env_url:
            if st.button("🔗 Open Environment", type="primary", use_container_width=True):
                st.markdown(f'<meta http-equiv="refresh" content="0;URL={env_url}" target="_blank">', 
                           unsafe_allow_html=True)
        
        # Advanced actions
        st.markdown("#### 🔧 Advanced Actions")
        
        if st.button("💓 Send Heartbeat", use_container_width=True):
            send_heartbeat()
        
        if st.button("📊 Force Refresh Status", use_container_width=True):
            get_environment_status.clear()
            st.rerun()

def show_quick_stats(status_data):
    """Display quick statistics"""
    
    if status_data.get("active"):
        env_info = status_data.get("environment", {})
        
        # Calculate uptime
        created_at = env_info.get('created_at')
        if created_at:
            try:
                created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                uptime = datetime.now() - created_time.replace(tzinfo=None)
                uptime_str = f"{uptime.days}d {uptime.seconds//3600}h {(uptime.seconds%3600)//60}m"
            except:
                uptime_str = "Unknown"
        else:
            uptime_str = "Unknown"
        
        st.metric("Uptime", uptime_str)
        st.metric("Status", env_info.get('status', 'Unknown').title())
        
    else:
        st.info("Launch an environment to see statistics")

def show_environment_configuration(status_data):
    """Environment configuration tab"""
    
    st.markdown("### ⚙️ Environment Configuration")
    
    # Current configuration
    if status_data.get("active"):
        env_info = status_data.get("environment", {})
        resource_config = env_info.get('resource_config', {})
        
        st.markdown("#### 📊 Current Configuration")
        
        current_config = {
            "CPU Limit": resource_config.get('cpu_limit', 'Unknown'),
            "Memory Limit": resource_config.get('memory_limit', 'Unknown'),
            "Storage Size": resource_config.get('storage_size', 'Unknown'),
            "Environment Image": "cmbcluster/user-env:latest"
        }
        
        st.json(current_config)
    
    st.markdown("#### 🔧 Resource Configuration")
    
    with st.form("resource_config"):
        col1, col2 = st.columns(2)
        
        with col1:
            cpu_limit = st.slider("CPU Cores", 0.5, 8.0, 2.0, 0.5)
            memory_gb = st.slider("Memory (GB)", 1, 16, 4, 1)
            
        with col2:
            storage_gb = st.slider("Storage (GB)", 5, 100, 10, 5)
            auto_cleanup_hours = st.slider("Auto-cleanup (hours)", 1, 24, 4, 1)
        
        st.markdown("#### 🖼️ Environment Image")
        image_options = [
            "cmbcluster/user-env:latest (Standard)",
            "cmbcluster/user-env:gpu (GPU Enabled)",
            "cmbcluster/user-env:minimal (Lightweight)",
            "custom (Specify custom image)"
        ]
        selected_image = st.selectbox("Container Image", image_options)
        
        if selected_image == "custom (Specify custom image)":
            custom_image = st.text_input("Custom Image URL")
        
        st.markdown("#### 🌿 Environment Variables")
        env_vars = st.text_area("Environment Variables (KEY=VALUE, one per line)", 
                                height=100,
                                value="JUPYTER_ENABLE_LAB=yes\nPYTHONPATH=/workspace")
        
        submitted = st.form_submit_button("💾 Save Configuration", type="primary")
        
        if submitted:
            config = {
                "cpu_limit": cpu_limit,
                "memory_limit": f"{memory_gb}Gi",
                "storage_size": f"{storage_gb}Gi",
                "auto_cleanup_hours": auto_cleanup_hours,
                "image": selected_image,
                "env_vars": env_vars
            }
            
            # Store configuration in session state
            st.session_state.env_config = config
            st.success("✅ Configuration saved! Changes will apply to the next environment launch.")

def show_environment_monitoring(status_data):
    """Environment monitoring tab"""
    
    st.markdown("### 📊 Environment Monitoring")
    
    if not status_data.get("active"):
        st.info("Launch an environment to see monitoring data")
        return
    
    # Real-time metrics
    st.markdown("#### 📈 Real-time Metrics")
    
    # Mock monitoring data
    import numpy as np
    
    # Generate realistic metric data
    timestamps = pd.date_range(start=datetime.now() - pd.Timedelta(hours=1), 
                              end=datetime.now(), freq='1min')
    
    metrics_data = pd.DataFrame({
        'timestamp': timestamps,
        'cpu_percent': np.random.normal(45, 10, len(timestamps)).clip(0, 100),
        'memory_percent': np.random.normal(60, 8, len(timestamps)).clip(0, 100),
        'disk_io_read': np.random.exponential(2, len(timestamps)),
        'disk_io_write': np.random.exponential(1.5, len(timestamps)),
        'network_in': np.random.exponential(5, len(timestamps)),
        'network_out': np.random.exponential(3, len(timestamps))
    })
    
    # CPU and Memory usage
    col1, col2 = st.columns(2)
    
    with col1:
        st.line_chart(metrics_data.set_index('timestamp')[['cpu_percent']], 
                     use_container_width=True, height=200)
        st.caption("CPU Usage (%)")
    
    with col2:
        st.line_chart(metrics_data.set_index('timestamp')[['memory_percent']], 
                     use_container_width=True, height=200)
        st.caption("Memory Usage (%)")
    
    # Disk and Network I/O
    col3, col4 = st.columns(2)
    
    with col3:
        disk_data = metrics_data.set_index('timestamp')[['disk_io_read', 'disk_io_write']]
        st.line_chart(disk_data, use_container_width=True, height=200)
        st.caption("Disk I/O (MB/s)")
    
    with col4:
        network_data = metrics_data.set_index('timestamp')[['network_in', 'network_out']]
        st.line_chart(network_data, use_container_width=True, height=200)
        st.caption("Network I/O (MB/s)")
    
    # Current metrics summary
    st.markdown("#### 📊 Current Metrics")
    
    current_metrics = metrics_data.iloc[-1]
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("CPU Usage", f"{current_metrics['cpu_percent']:.1f}%")
    
    with col2:
        st.metric("Memory Usage", f"{current_metrics['memory_percent']:.1f}%")
    
    with col3:
        st.metric("Disk Read", f"{current_metrics['disk_io_read']:.2f} MB/s")
    
    with col4:
        st.metric("Network In", f"{current_metrics['network_in']:.2f} MB/s")

def show_environment_logs(status_data):
    """Environment logs tab"""
    
    st.markdown("### 📋 Environment Logs")
    
    if not status_data.get("active"):
        st.info("Launch an environment to view logs")
        return
    
    # Log filtering options
    col1, col2, col3 = st.columns(3)
    
    with col1:
        log_level = st.selectbox("Log Level", ["All", "INFO", "WARNING", "ERROR"])
    
    with col2:
        log_lines = st.selectbox("Number of Lines", [50, 100, 200, 500])
    
    with col3:
        if st.button("🔄 Refresh Logs"):
            st.rerun()
    
    # Auto-refresh option
    auto_refresh_logs = st.checkbox("Auto-refresh logs (10s)")
    
    if auto_refresh_logs:
        time.sleep(10)
        st.rerun()
    
    # Mock log entries
    log_entries = [
        {"timestamp": "2025-06-26 10:55:23", "level": "INFO", "message": "Streamlit server started on port 8501"},
        {"timestamp": "2025-06-26 10:55:20", "level": "INFO", "message": "Loading cosmology libraries..."},
        {"timestamp": "2025-06-26 10:55:18", "level": "INFO", "message": "Mounting workspace volume at /workspace"},
        {"timestamp": "2025-06-26 10:55:15", "level": "INFO", "message": "Container started successfully"},
        {"timestamp": "2025-06-26 10:55:12", "level": "INFO", "message": "Pulling image cmbcluster/user-env:latest"},
        {"timestamp": "2025-06-26 10:55:10", "level": "INFO", "message": "Creating persistent volume claim"},
        {"timestamp": "2025-06-26 10:55:08", "level": "INFO", "message": "Pod creation initiated"},
        {"timestamp": "2025-06-26 10:54:30", "level": "WARNING", "message": "Previous session terminated due to inactivity"},
        {"timestamp": "2025-06-26 09:30:15", "level": "ERROR", "message": "Failed to connect to external data source"},
        {"timestamp": "2025-06-26 09:15:42", "level": "INFO", "message": "User authentication successful"}
    ]
    
    # Filter logs
    if log_level != "All":
        log_entries = [entry for entry in log_entries if entry["level"] == log_level]
    
    log_entries = log_entries[:log_lines]
    
    # Display logs
    st.markdown("#### 📝 Log Output")
    
    log_container = st.container()
    
    with log_container:
        for entry in log_entries:
            log_color = {
                "INFO": "#28a745",
                "WARNING": "#ffc107", 
                "ERROR": "#dc3545"
            }.get(entry["level"], "#ffffff")
            
            st.markdown(f"""
            <div class="log-entry">
                <span style="color: #6c757d;">{entry["timestamp"]}</span>
                <span style="color: {log_color}; font-weight: bold;">[{entry["level"]}]</span>
                <span>{entry["message"]}</span>
            </div>
            """, unsafe_allow_html=True)
    
    # Log export
    st.markdown("#### 📥 Export Logs")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📋 Copy to Clipboard"):
            log_text = "\n".join([f"{entry['timestamp']} [{entry['level']}] {entry['message']}" 
                                 for entry in log_entries])
            st.code(log_text)
    
    with col2:
        log_text = "\n".join([f"{entry['timestamp']} [{entry['level']}] {entry['message']}" 
                             for entry in log_entries])
        st.download_button("💾 Download Logs", log_text, 
                          file_name=f"cmbcluster-logs-{datetime.now().strftime('%Y%m%d-%H%M%S')}.txt",
                          mime="text/plain")

# Helper functions
@st.cache_data(ttl=30)
def get_environment_status():
    """Get environment status with caching"""
    try:
        return api_client.get_environment_status()
    except Exception as e:
        st.error(f"Failed to get environment status: {str(e)}")
        return {"active": False}

def launch_environment_with_config(preset):
    """Launch environment with selected configuration"""
    with st.spinner("🚀 Launching environment..."):
        try:
            # Map preset to configuration
            config_map = {
                "Standard Research (2 CPU, 4GB RAM)": {"cpu_limit": 2.0, "memory_limit": "4Gi"},
                "Heavy Computation (4 CPU, 8GB RAM)": {"cpu_limit": 4.0, "memory_limit": "8Gi"},
                "Light Analysis (1 CPU, 2GB RAM)": {"cpu_limit": 1.0, "memory_limit": "2Gi"},
                "Custom Configuration": st.session_state.get("env_config", {})
            }
            
            config = config_map.get(preset, {"cpu_limit": 2.0, "memory_limit": "4Gi"})
            
            result = api_client.create_environment(config)
            
            if result.get("status") in ["created", "existing"]:
                st.success(f"✅ Environment {result['status']} with {preset}!")
                env_url = result.get("environment", {}).get("url")
                if env_url:
                    st.info(f"🔗 Access your environment: {env_url}")
                
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
    if st.session_state.get("confirm_delete_env"):
        with st.spinner("🗑️ Stopping environment..."):
            try:
                result = api_client.delete_environment()
                st.success("✅ Environment stopped successfully!")
                
                get_environment_status.clear()
                st.session_state.confirm_delete_env = False
                time.sleep(1)
                st.rerun()
            
            except Exception as e:
                st.error(f"Error stopping environment: {str(e)}")
    else:
        st.warning("⚠️ This will stop your environment. Your workspace data will be preserved.")
        if st.button("🗑️ Confirm Stop"):
            st.session_state.confirm_delete_env = True
            st.rerun()

def send_heartbeat():
    """Send heartbeat to keep environment alive"""
    try:
        result = api_client.send_heartbeat()
        st.success("💓 Heartbeat sent successfully!")
        get_environment_status.clear()
    except Exception as e:
        st.error(f"Failed to send heartbeat: {str(e)}")

if __name__ == "__main__":
    if not check_authentication():
        show_login_screen()
    else:
        main()
