#!/usr/bin/env python3
"""
Debug script to test admin endpoints and detect 500 errors
"""
import requests
import json

def debug_admin_endpoints():
    base_url = "http://localhost:8000"  # Adjust if needed
    
    print("=== Debugging Admin Endpoints ===")
    
    # Test if server is running
    try:
        response = requests.get(f"{base_url}/health", timeout=5)
        print(f"Health check: {response.status_code}")
        if response.status_code == 200:
            print(f"Health response: {response.json()}")
        else:
            print(f"Health response: {response.text}")
    except Exception as e:
        print(f"Health check failed: {e}")
        return
    
    # Test admin applications endpoint (without auth first to see what error we get)
    try:
        response = requests.get(f"{base_url}/admin/applications", timeout=5)
        print(f"Admin applications GET (no auth): {response.status_code}")
        print(f"Response: {response.text[:200]}")
    except Exception as e:
        print(f"Admin applications test failed: {e}")
    
    # Test form submission endpoint
    try:
        form_data = {
            'name': 'Test Application',
            'summary': 'Test summary',
            'image_path': 'test/image:latest',
            'category': 'research',
            'port': '8888',
            'tags': 'test,demo'
        }
        response = requests.post(f"{base_url}/admin/applications-with-image", 
                               data=form_data, timeout=10)
        print(f"Form submission test (no auth): {response.status_code}")
        print(f"Response: {response.text[:300]}")
    except Exception as e:
        print(f"Form submission test failed: {e}")

if __name__ == "__main__":
    debug_admin_endpoints()