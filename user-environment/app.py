import streamlit as st
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os
import requests
import time

# Configuration
USER_ID = os.getenv("USER_ID", "unknown")
USER_EMAIL = os.getenv("USER_EMAIL", "unknown@example.com")
HUB_URL = os.getenv("HUB_URL", "http://localhost:8000")
WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/workspace")

# Page config
st.set_page_config(
    page_title="CMBCluster Research Environment",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .user-header {
        background: linear-gradient(90deg, #4CAF50 0%, #45a049 100%);
        padding: 1rem;
        border-radius: 0.5rem;
        color: white;
        margin-bottom: 1rem;
    }
    .workspace-card {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .code-output {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #dee2e6;
        font-family: 'Courier New', monospace;
    }
</style>
""", unsafe_allow_html=True)

def send_heartbeat():
    """Send heartbeat to hub to keep environment alive"""
    try:
        response = requests.post(f"{HUB_URL}/environments/heartbeat", timeout=5)
        return response.status_code == 200
    except:
        return False

def main():
    """Main application"""
    # Header
    st.markdown(f"""
    <div class="user-header">
        <h1>🔬 CMBCluster Research Environment</h1>
        <p>User: {USER_EMAIL} | ID: {USER_ID}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-heartbeat
    setup_heartbeat()
    
    # Sidebar
    setup_sidebar()
    
    # Main content
    show_main_interface()

def setup_heartbeat():
    """Setup automatic heartbeat"""
    if "last_heartbeat" not in st.session_state:
        st.session_state.last_heartbeat = 0
    
    current_time = time.time()
    if current_time - st.session_state.last_heartbeat > 300:  # 5 minutes
        if send_heartbeat():
            st.session_state.last_heartbeat = current_time
            st.session_state.heartbeat_status = "✅ Connected"
        else:
            st.session_state.heartbeat_status = "❌ Disconnected"

def setup_sidebar():
    """Setup sidebar with user info and controls"""
    with st.sidebar:
        st.markdown("### 👤 User Information")
        st.write(f"**Email:** {USER_EMAIL}")
        st.write(f"**User ID:** {USER_ID}")
        st.write(f"**Status:** {st.session_state.get('heartbeat_status', '🔄 Connecting...')}")
        
        st.markdown("---")
        
        st.markdown("### 🔧 Environment Controls")
        
        if st.button("💓 Send Heartbeat", use_container_width=True):
            if send_heartbeat():
                st.success("Heartbeat sent!")
                st.session_state.last_heartbeat = time.time()
            else:
                st.error("Failed to send heartbeat")
        
        st.markdown(f"**Workspace:** `{WORKSPACE_DIR}`")
        
        # File management
        st.markdown("### 📁 File Management")
        uploaded_file = st.file_uploader("Upload file to workspace")
        if uploaded_file:
            file_path = os.path.join(WORKSPACE_DIR, uploaded_file.name)
            try:
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                st.success(f"File saved: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error saving file: {str(e)}")
        
        # Workspace files
        try:
            files = os.listdir(WORKSPACE_DIR)
            if files:
                st.write("**Workspace Files:**")
                for file in files[:5]:  # Show first 5 files
                    st.write(f"📄 {file}")
                if len(files) > 5:
                    st.write(f"... and {len(files) - 5} more")
            else:
                st.info("No files in workspace")
        except:
            st.warning("Cannot access workspace directory")

def show_main_interface():
    """Main research interface"""
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Data Analysis", 
        "🧮 Calculations", 
        "🌌 Cosmology Tools", 
        "📝 Notebook", 
        "⚙️ System"
    ])
    
    with tab1:
        show_data_analysis()
    
    with tab2:
        show_calculations()
    
    with tab3:
        show_cosmology_tools()
    
    with tab4:
        show_notebook()
    
    with tab5:
        show_system_info()

def show_data_analysis():
    """Data analysis tools"""
    st.markdown("## 📊 Data Analysis Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Generate Sample Data")
        
        data_type = st.selectbox("Data Type", [
            "Random Normal", 
            "CMB Temperature Map", 
            "Galaxy Survey",
            "Time Series"
        ])
        
        n_points = st.slider("Number of Points", 100, 10000, 1000)
        
        if st.button("Generate Data"):
            if data_type == "Random Normal":
                data = np.random.randn(n_points)
                st.session_state.analysis_data = data
                st.session_state.data_type = "1D Array"
            
            elif data_type == "CMB Temperature Map":
                # Simulate CMB temperature fluctuations
                nside = 64
                npix = 12 * nside**2
                data = np.random.normal(0, 1e-5, npix)  # μK fluctuations
                st.session_state.analysis_data = data
                st.session_state.data_type = "CMB Map"
            
            elif data_type == "Galaxy Survey":
                # Simulate galaxy positions and redshifts
                n_gal = min(n_points, 5000)
                ra = np.random.uniform(0, 360, n_gal)
                dec = np.random.uniform(-90, 90, n_gal)
                z = np.random.exponential(0.3, n_gal)
                data = pd.DataFrame({'ra': ra, 'dec': dec, 'redshift': z})
                st.session_state.analysis_data = data
                st.session_state.data_type = "Galaxy Catalog"
            
            elif data_type == "Time Series":
                t = np.linspace(0, 10, n_points)
                signal = np.sin(2*np.pi*t) + 0.1*np.random.randn(n_points)
                data = pd.DataFrame({'time': t, 'signal': signal})
                st.session_state.analysis_data = data
                st.session_state.data_type = "Time Series"
            
            st.success(f"Generated {data_type} data!")
    
    with col2:
        st.markdown("### Data Visualization")
        
        if "analysis_data" in st.session_state:
            data = st.session_state.analysis_data
            data_type = st.session_state.data_type
            
            if data_type == "1D Array":
                fig = plt.figure(figsize=(10, 6))
                plt.hist(data, bins=50, alpha=0.7, edgecolor='black')
                plt.title("Data Distribution")
                plt.xlabel("Value")
                plt.ylabel("Frequency")
                st.pyplot(fig)
                
                # Statistics
                st.markdown("**Statistics:**")
                st.write(f"Mean: {np.mean(data):.4f}")
                st.write(f"Std: {np.std(data):.4f}")
                st.write(f"Min: {np.min(data):.4f}")
                st.write(f"Max: {np.max(data):.4f}")
            
            elif data_type == "Galaxy Catalog":
                fig = px.scatter(data, x='ra', y='dec', color='redshift',
                               title="Galaxy Distribution on Sky")
                st.plotly_chart(fig, use_container_width=True)
                
                # Redshift distribution
                fig2 = px.histogram(data, x='redshift', bins=30,
                                  title="Redshift Distribution")
                st.plotly_chart(fig2, use_container_width=True)
            
            elif data_type == "Time Series":
                fig = px.line(data, x='time', y='signal',
                            title="Time Series Data")
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Generate data to see visualizations")

def show_calculations():
    """Scientific calculations"""
    st.markdown("## 🧮 Scientific Calculations")
    
    calc_type = st.selectbox("Calculation Type", [
        "Basic Math",
        "Cosmological Parameters", 
        "Statistical Analysis",
        "Linear Algebra"
    ])
    
    if calc_type == "Basic Math":
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### Calculator")
            num1 = st.number_input("First number", value=0.0, format="%.6f")
            operation = st.selectbox("Operation", ["+", "-", "*", "/", "**", "log", "exp"])
            num2 = st.number_input("Second number", value=0.0, format="%.6f")
            
            if st.button("Calculate"):
                try:
                    if operation == "+":
                        result = num1 + num2
                    elif operation == "-":
                        result = num1 - num2
                    elif operation == "*":
                        result = num1 * num2
                    elif operation == "/":
                        result = num1 / num2 if num2 != 0 else "Division by zero!"
                    elif operation == "**":
                        result = num1 ** num2
                    elif operation == "log":
                        result = np.log(num1) if num1 > 0 else "Invalid input for log"
                    elif operation == "exp":
                        result = np.exp(num1)
                    
                    st.success(f"Result: {result}")
                except Exception as e:
                    st.error(f"Error: {str(e)}")
        
        with col2:
            st.markdown("### Array Operations")
            array_size = st.slider("Array size", 10, 1000, 100)
            
            if st.button("Generate Random Array"):
                arr = np.random.randn(array_size)
                st.session_state.calc_array = arr
            
            if "calc_array" in st.session_state:
                arr = st.session_state.calc_array
                
                col2a, col2b = st.columns(2)
                with col2a:
                    st.metric("Mean", f"{np.mean(arr):.4f}")
                    st.metric("Std Dev", f"{np.std(arr):.4f}")
                with col2b:
                    st.metric("Min", f"{np.min(arr):.4f}")
                    st.metric("Max", f"{np.max(arr):.4f}")
                
                # Quick plot
                fig = plt.figure(figsize=(8, 4))
                plt.plot(arr[:min(100, len(arr))])
                plt.title("Array Values (first 100 points)")
                st.pyplot(fig)
    
    elif calc_type == "Cosmological Parameters":
        st.markdown("### Cosmological Distance Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            H0 = st.slider("Hubble Constant (km/s/Mpc)", 50, 100, 70, 1)
            Omega_m = st.slider("Matter Density", 0.1, 0.5, 0.3, 0.01)
            Omega_L = st.slider("Dark Energy Density", 0.5, 0.9, 0.7, 0.01)
            redshift = st.slider("Redshift", 0.0, 5.0, 1.0, 0.1)
        
        with col2:
            # Simple cosmological calculations
            c = 299792.458  # km/s
            
            # Hubble distance
            d_H = c / H0
            st.metric("Hubble Distance", f"{d_H:.1f} Mpc")
            
            # Comoving distance (approximate)
            d_c = d_H * redshift  # Very simplified!
            st.metric("Comoving Distance", f"{d_c:.1f} Mpc")
            
            # Lookback time (approximate)
            t_lookback = (2/3) * (1/H0) * (1/np.sqrt(Omega_m)) * 1e3  # Gyr
            st.metric("Lookback Time", f"{t_lookback:.1f} Gyr")

def show_cosmology_tools():
    """Cosmology-specific tools"""
    st.markdown("## 🌌 Cosmology Tools")
    
    tool_type = st.selectbox("Tool Type", [
        "CMB Power Spectrum",
        "Galaxy Clustering",
        "Weak Lensing",
        "BAO Analysis"
    ])
    
    if tool_type == "CMB Power Spectrum":
        st.markdown("### CMB Temperature Power Spectrum")
        
        # Simulate CMB power spectrum
        l = np.arange(2, 3000)
        # Simplified model: just the basic shape
        Cl = 1e12 * np.exp(-(l-200)**2/(2*100**2)) / l**2
        
        fig = plt.figure(figsize=(12, 6))
        plt.loglog(l, l*(l+1)*Cl/(2*np.pi), 'b-', linewidth=2)
        plt.xlabel(r'Multipole $\ell$')
        plt.ylabel(r'$\ell(\ell+1)C_\ell/2\pi$ [$\mu K^2$]')
        plt.title('CMB Temperature Power Spectrum')
        plt.grid(True, alpha=0.3)
        st.pyplot(fig)
        
        st.info("This is a simplified simulation. Real CMB analysis requires specialized codes like CAMB or CLASS.")
    
    elif tool_type == "Galaxy Clustering":
        st.markdown("### Galaxy Two-Point Correlation Function")
        
        # Simulate correlation function
        r = np.logspace(-1, 2, 50)  # Mpc/h
        xi = (r/5)**(-1.8)  # Power law
        
        fig = plt.figure(figsize=(10, 6))
        plt.loglog(r, xi, 'ro-', markersize=4)
        plt.xlabel(r'$r$ [Mpc/h]')
        plt.ylabel(r'$\xi(r)$')
        plt.title('Galaxy Two-Point Correlation Function')
        plt.grid(True, alpha=0.3)
        st.pyplot(fig)

def show_notebook():
    """Interactive notebook-style interface"""
    st.markdown("## 📝 Research Notebook")
    
    st.markdown("### Code Execution")
    
    # Code input
    code = st.text_area("Enter Python code:", height=200, value="""
# Example: Create and analyze some cosmological data
import numpy as np
import matplotlib.pyplot as plt

# Generate mock galaxy redshift distribution
z = np.random.exponential(0.5, 1000)
z = z[z < 3]  # Cut at z=3

# Calculate number density
hist, bins = np.histogram(z, bins=30)
bin_centers = (bins[1:] + bins[:-1]) / 2

print(f"Generated {len(z)} galaxies")
print(f"Mean redshift: {np.mean(z):.2f}")
print(f"Max redshift: {np.max(z):.2f}")

# Plot
plt.figure(figsize=(10, 6))
plt.hist(z, bins=30, alpha=0.7, edgecolor='black')
plt.xlabel('Redshift')
plt.ylabel('Number of Galaxies')
plt.title('Mock Galaxy Redshift Distribution')
plt.show()
""")
    
    if st.button("🚀 Execute Code"):
        try:
            # Create execution environment
            exec_globals = {
                'np': np, 
                'plt': plt, 
                'pd': pd,
                'st': st
            }
            
            # Capture output
            import io
            import sys
            from contextlib import redirect_stdout, redirect_stderr
            
            output_buffer = io.StringIO()
            error_buffer = io.StringIO()
            
            with redirect_stdout(output_buffer), redirect_stderr(error_buffer):
                exec(code, exec_globals)
            
            # Display output
            output = output_buffer.getvalue()
            errors = error_buffer.getvalue()
            
            if output:
                st.markdown("**Output:**")
                st.code(output)
            
            if errors:
                st.markdown("**Errors:**")
                st.error(errors)
            
            # Display any matplotlib figures
            if plt.get_fignums():
                for fignum in plt.get_fignums():
                    fig = plt.figure(fignum)
                    st.pyplot(fig)
                plt.close('all')
            
        except Exception as e:
            st.error(f"Execution error: {str(e)}")
    
    # Save/load code
    st.markdown("### Save/Load Code")
    
    col1, col2 = st.columns(2)
    
    with col1:
        filename = st.text_input("Filename", value="my_code.py")
        if st.button("💾 Save Code"):
            try:
                filepath = os.path.join(WORKSPACE_DIR, filename)
                with open(filepath, 'w') as f:
                    f.write(code)
                st.success(f"Code saved to {filename}")
            except Exception as e:
                st.error(f"Error saving file: {str(e)}")
    
    with col2:
        try:
            py_files = [f for f in os.listdir(WORKSPACE_DIR) if f.endswith('.py')]
            if py_files:
                selected_file = st.selectbox("Load File", py_files)
                if st.button("📂 Load Code"):
                    try:
                        filepath = os.path.join(WORKSPACE_DIR, selected_file)
                        with open(filepath, 'r') as f:
                            loaded_code = f.read()
                        st.session_state.loaded_code = loaded_code
                        st.success(f"Code loaded from {selected_file}")
                    except Exception as e:
                        st.error(f"Error loading file: {str(e)}")
        except:
            st.info("No Python files found in workspace")

def show_system_info():
    """System information and diagnostics"""
    st.markdown("## ⚙️ System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### Environment")
        st.write(f"**User ID:** {USER_ID}")
        st.write(f"**User Email:** {USER_EMAIL}")
        st.write(f"**Hub URL:** {HUB_URL}")
        st.write(f"**Workspace:** {WORKSPACE_DIR}")
        st.write(f"**Python Version:** {os.sys.version}")
        
        # System resources
        try:
            import psutil
            st.markdown("### System Resources")
            st.write(f"**CPU Usage:** {psutil.cpu_percent()}%")
            st.write(f"**Memory Usage:** {psutil.virtual_memory().percent}%")
            st.write(f"**Disk Usage:** {psutil.disk_usage('/').percent}%")
        except ImportError:
            st.info("Install psutil for system monitoring")
    
    with col2:
        st.markdown("### Installed Packages")
        
        key_packages = [
            'numpy', 'scipy', 'matplotlib', 'pandas', 
            'streamlit', 'plotly', 'astropy'
        ]
        
        for package in key_packages:
            try:
                module = __import__(package)
                version = getattr(module, '__version__', 'Unknown')
                st.write(f"**{package}:** {version}")
            except ImportError:
                st.write(f"**{package}:** Not installed")
        
        # Connectivity test
        st.markdown("### Connectivity")
        
        if st.button("🔗 Test Hub Connection"):
            if send_heartbeat():
                st.success("✅ Connected to hub")
            else:
                st.error("❌ Cannot connect to hub")
        
        # Workspace info
        st.markdown("### Workspace Info")
        try:
            files = os.listdir(WORKSPACE_DIR)
            st.write(f"**Files:** {len(files)}")
            
            total_size = 0
            for file in files:
                filepath = os.path.join(WORKSPACE_DIR, file)
                if os.path.isfile(filepath):
                    total_size += os.path.getsize(filepath)
            
            st.write(f"**Total Size:** {total_size / 1024 / 1024:.2f} MB")
        except:
            st.warning("Cannot access workspace directory")

if __name__ == "__main__":
    main()
