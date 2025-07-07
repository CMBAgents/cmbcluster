import streamlit as st
import requests
import time
from datetime import datetime

# Import our components
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.auth import check_authentication, show_login_screen, require_auth
from components.api_client import api_client
from config import settings

# Page configuration
st.set_page_config(
    page_title="Diagnostics - CMBCluster",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

@require_auth
def main():
    """Diagnostics page to help debug API issues"""
    
    # Clear only specific page-related session state (preserve auth and config)
    page_keys_to_clear = ['diag_temp_data']
    for key in page_keys_to_clear:
        if key in st.session_state:
            del st.session_state[key]
    
    st.empty()
    
    st.markdown("# 🔍 System Diagnostics")
    st.markdown("Debug API connectivity and performance issues")
    
    # API Health Check
    st.markdown("## 🏥 API Health Check")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Test API Connection", key="test_api_connection"):
            test_api_connection()
    
    with col2:
        if st.button("🧪 Test All Endpoints", key="test_all_endpoints"):
            test_all_endpoints()
    
    st.divider()
    
    # Current Configuration
    st.markdown("## ⚙️ Current Configuration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**API Settings:**")
        st.code(f"""
API URL: {settings.api_url}
Base Domain: {settings.base_domain}
Frontend URL: {settings.frontend_url}
Dev Mode: {settings.dev_mode}
        """)
    
    with col2:
        st.markdown("**Session State:**")
        auth_status = st.session_state.get("authenticated", False)
        token_present = bool(st.session_state.get("access_token"))
        st.code(f"""
Authenticated: {auth_status}
Token Present: {token_present}
User Info: {bool(st.session_state.get("user_info"))}
        """)
    
    st.divider()
    
    # Error Log
    st.markdown("## 📋 Recent Errors")
    api_errors = st.session_state.get("api_errors", [])
    
    if api_errors:
        for i, error in enumerate(api_errors[-10:]):  # Show last 10 errors
            st.error(f"Error {i+1}: {error}")
        
        if st.button("🧹 Clear Error Log", key="clear_errors"):
            st.session_state.api_errors = []
            st.rerun()
    else:
        st.success("No recent API errors logged")
    
    st.divider()
    
    # Manual API Test
    st.markdown("## 🛠️ Manual API Test")
    
    endpoint = st.selectbox("Select Endpoint", [
        "/health",
        "/environments",
        "/environments/heartbeat",
        "/activity",
        "/users/me"
    ])
    
    method = st.selectbox("HTTP Method", ["GET", "POST", "DELETE"])
    
    if st.button("🚀 Send Request", key="manual_request"):
        manual_api_request(endpoint, method)

def test_api_connection():
    """Test basic API connectivity"""
    st.markdown("### Testing API Connection...")
    
    start_time = time.time()
    
    try:
        # Test health endpoint
        result = api_client.health_check()
        response_time = time.time() - start_time
        
        st.success(f"✅ API connection successful! Response time: {response_time:.2f}s")
        st.json(result)
        
    except Exception as e:
        response_time = time.time() - start_time
        st.error(f"❌ API connection failed after {response_time:.2f}s: {str(e)}")

def test_all_endpoints():
    """Test all major endpoints"""
    st.markdown("### Testing All Endpoints...")
    
    endpoints = [
        ("Health Check", lambda: api_client.health_check()),
        ("Environment Status", lambda: api_client.get_environment_status()),
        ("Activity Log", lambda: api_client.get_activity_log(limit=5)),
        ("Heartbeat", lambda: api_client.send_heartbeat()),
    ]
    
    results = {}
    
    for name, func in endpoints:
        try:
            start_time = time.time()
            result = func()
            response_time = time.time() - start_time
            results[name] = {"status": "✅ Success", "time": f"{response_time:.2f}s", "data": result}
        except Exception as e:
            response_time = time.time() - start_time
            results[name] = {"status": "❌ Failed", "time": f"{response_time:.2f}s", "error": str(e)}
    
    # Display results
    for name, result in results.items():
        with st.expander(f"{result['status']} {name} ({result['time']})"):
            if "error" in result:
                st.error(result["error"])
            else:
                st.json(result["data"])

def manual_api_request(endpoint, method):
    """Make a manual API request"""
    st.markdown(f"### Testing {method} {endpoint}")
    
    try:
        url = f"{api_client.base_url}{endpoint}"
        headers = api_client._get_headers()
        
        start_time = time.time()
        
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            response = requests.post(url, headers=headers, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        
        response_time = time.time() - start_time
        
        st.success(f"✅ Request completed in {response_time:.2f}s")
        st.write(f"**Status Code:** {response.status_code}")
        st.write(f"**Response Headers:**")
        st.json(dict(response.headers))
        
        try:
            response_data = response.json()
            st.write(f"**Response Body:**")
            st.json(response_data)
        except:
            st.write(f"**Response Text:**")
            st.text(response.text)
            
    except Exception as e:
        response_time = time.time() - start_time
        st.error(f"❌ Request failed after {response_time:.2f}s: {str(e)}")

if __name__ == "__main__":
    if not check_authentication():
        show_login_screen()
    else:
        main()
