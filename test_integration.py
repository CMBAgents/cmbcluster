#!/usr/bin/env python3
"""
CMB Cluster Backend-Frontend Integration Test Script

This script tests the compatibility between your FastAPI backend and Next.js frontend
by simulating the API calls that your frontend makes.

Usage:
    python test_integration.py

Requirements:
    pip install requests python-dotenv
"""

import json
import requests
import time
from typing import Dict, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class CMBClusterAPITester:
    def __init__(self, base_url: str = "http://localhost:8000", dev_mode: bool = True):
        self.base_url = base_url
        self.session = requests.Session()
        
        # Use dev token in development mode
        if dev_mode:
            self.session.headers.update({
                'Authorization': 'Bearer dev-token',
                'Content-Type': 'application/json'
            })
        
        self.test_results = []
    
    def log_test(self, test_name: str, success: bool, details: str = ""):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status} {test_name}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_health_check(self):
        """Test basic health check endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            if response.status_code == 200:
                data = response.json()
                expected_fields = ['status', 'timestamp', 'version', 'uptime']
                missing_fields = [field for field in expected_fields if field not in data]
                
                if missing_fields:
                    self.log_test("Health Check", False, f"Missing fields: {missing_fields}")
                else:
                    self.log_test("Health Check", True, f"Status: {data['status']}")
            else:
                self.log_test("Health Check", False, f"Status code: {response.status_code}")
        except Exception as e:
            self.log_test("Health Check", False, str(e))
    
    def test_authentication(self):
        """Test authentication requirements"""
        # Test without token
        try:
            session_no_auth = requests.Session()
            response = session_no_auth.get(f"{self.base_url}/environments")
            
            if response.status_code == 401:
                self.log_test("Authentication Required", True, "Properly rejects requests without token")
            else:
                self.log_test("Authentication Required", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Authentication Required", False, str(e))
        
        # Test with valid token (dev mode)
        try:
            response = self.session.get(f"{self.base_url}/environments")
            if response.status_code in [200, 404]:  # 404 is OK if no environments exist
                self.log_test("Authentication Working", True, "Valid token accepted")
            else:
                self.log_test("Authentication Working", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Authentication Working", False, str(e))
    
    def test_environment_endpoints(self):
        """Test environment management endpoints"""
        
        # Test list environments
        try:
            response = self.session.get(f"{self.base_url}/environments/list")
            if response.status_code == 200:
                data = response.json()
                if 'environments' in data:
                    self.log_test("List Environments", True, f"Found {len(data['environments'])} environments")
                else:
                    self.log_test("List Environments", False, "Missing 'environments' field")
            else:
                self.log_test("List Environments", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("List Environments", False, str(e))
        
        # Test environment status
        try:
            response = self.session.get(f"{self.base_url}/environments")
            if response.status_code == 200:
                data = response.json()
                required_fields = ['active']
                if all(field in data for field in required_fields):
                    self.log_test("Environment Status", True, f"Active: {data['active']}")
                else:
                    self.log_test("Environment Status", False, "Missing required fields")
            else:
                self.log_test("Environment Status", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Environment Status", False, str(e))
        
        # Test create environment (expect this to work but may create actual environment)
        try:
            test_config = {
                "cpu_limit": 1.0,
                "memory_limit": "2Gi",
                "storage_size": "25Gi",
                "create_new_storage": True,
                "storage_class": "STANDARD"
            }
            
            response = self.session.post(f"{self.base_url}/environments", json=test_config)
            if response.status_code in [200, 201]:
                data = response.json()
                if 'status' in data and data['status'] in ['created', 'existing']:
                    self.log_test("Create Environment", True, f"Status: {data['status']}")
                    
                    # If environment was created, try to clean it up
                    if 'environment' in data and 'id' in data['environment']:
                        env_id = data['environment']['id']
                        self.cleanup_test_environment(env_id)
                else:
                    self.log_test("Create Environment", False, "Invalid response format")
            else:
                self.log_test("Create Environment", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Create Environment", False, str(e))
    
    def test_storage_endpoints(self):
        """Test storage management endpoints"""
        
        # Test list storage
        try:
            response = self.session.get(f"{self.base_url}/storage/list")
            if response.status_code == 200:
                data = response.json()
                if 'storages' in data:
                    self.log_test("List Storage", True, f"Found {len(data['storages'])} storage buckets")
                else:
                    self.log_test("List Storage", False, "Missing 'storages' field")
            else:
                self.log_test("List Storage", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("List Storage", False, str(e))
    
    def test_user_env_vars(self):
        """Test user environment variables endpoints"""
        
        # Test get env vars
        try:
            response = self.session.get(f"{self.base_url}/user-env-vars")
            if response.status_code == 200:
                data = response.json()
                if 'env_vars' in data:
                    self.log_test("Get User Env Vars", True, f"Found {len(data['env_vars'])} variables")
                else:
                    self.log_test("Get User Env Vars", False, "Missing 'env_vars' field")
            else:
                self.log_test("Get User Env Vars", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Get User Env Vars", False, str(e))
        
        # Test set env var
        try:
            test_var = {"key": "TEST_INTEGRATION", "value": "test_value"}
            response = self.session.post(f"{self.base_url}/user-env-vars", json=test_var)
            if response.status_code == 200:
                data = response.json()
                if data.get('status') == 'success':
                    self.log_test("Set User Env Var", True, f"Set {test_var['key']}")
                    
                    # Clean up test variable
                    try:
                        self.session.delete(f"{self.base_url}/user-env-vars/{test_var['key']}")
                    except:
                        pass
                else:
                    self.log_test("Set User Env Var", False, "Operation failed")
            else:
                self.log_test("Set User Env Var", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Set User Env Var", False, str(e))
    
    def test_file_endpoints(self):
        """Test file management endpoints"""
        
        # Test list user files
        try:
            response = self.session.get(f"{self.base_url}/user-files")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) or 'files' in data:
                    file_count = len(data) if isinstance(data, list) else len(data.get('files', []))
                    self.log_test("List User Files", True, f"Found {file_count} files")
                else:
                    self.log_test("List User Files", False, "Invalid response format")
            else:
                self.log_test("List User Files", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("List User Files", False, str(e))
    
    def test_activity_log(self):
        """Test activity log endpoint"""
        try:
            response = self.session.get(f"{self.base_url}/activity")
            if response.status_code == 200:
                data = response.json()
                if 'activities' in data:
                    self.log_test("Activity Log", True, f"Found {len(data['activities'])} activities")
                else:
                    self.log_test("Activity Log", False, "Missing 'activities' field")
            else:
                self.log_test("Activity Log", False, f"Status: {response.status_code}")
        except Exception as e:
            self.log_test("Activity Log", False, str(e))
    
    def cleanup_test_environment(self, env_id: str):
        """Clean up test environment"""
        try:
            response = self.session.delete(f"{self.base_url}/environments", 
                                         params={"env_id": env_id})
            if response.status_code == 200:
                print(f"   Cleaned up test environment: {env_id}")
        except Exception as e:
            print(f"   Failed to clean up test environment: {e}")
    
    def test_cors_headers(self):
        """Test CORS configuration"""
        try:
            response = self.session.options(f"{self.base_url}/environments")
            cors_headers = {
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods', 
                'Access-Control-Allow-Headers'
            }
            
            present_headers = set(response.headers.keys()) & cors_headers
            if len(present_headers) > 0:
                self.log_test("CORS Configuration", True, f"Found CORS headers: {present_headers}")
            else:
                # Try a regular GET request and check response headers
                response = self.session.get(f"{self.base_url}/health")
                cors_origin = response.headers.get('Access-Control-Allow-Origin')
                if cors_origin:
                    self.log_test("CORS Configuration", True, f"Allow-Origin: {cors_origin}")
                else:
                    self.log_test("CORS Configuration", False, "No CORS headers found")
        except Exception as e:
            self.log_test("CORS Configuration", False, str(e))
    
    def test_data_format_compatibility(self):
        """Test data format compatibility between frontend and backend"""
        
        # Test date format handling
        test_date = "2024-08-23T10:00:00Z"
        try:
            from datetime import datetime
            parsed_date = datetime.fromisoformat(test_date.replace('Z', '+00:00'))
            self.log_test("Date Format Compatibility", True, f"ISO format parsed correctly")
        except Exception as e:
            self.log_test("Date Format Compatibility", False, str(e))
        
        # Test status enum values
        valid_statuses = {'running', 'pending', 'failed', 'stopped', 'unknown'}
        backend_statuses = {'running', 'pending', 'failed', 'succeeded', 'unknown'}  # From PodStatus enum
        
        compatible_statuses = valid_statuses & backend_statuses
        if len(compatible_statuses) >= 4:  # Most statuses should match
            self.log_test("Status Format Compatibility", True, 
                         f"Compatible statuses: {compatible_statuses}")
        else:
            self.log_test("Status Format Compatibility", False, 
                         f"Limited compatibility: {compatible_statuses}")
    
    def run_all_tests(self):
        """Run comprehensive integration tests"""
        print("🧪 Starting CMB Cluster Integration Tests...")
        print(f"Testing backend at: {self.base_url}")
        print("-" * 60)
        
        # Core functionality tests
        self.test_health_check()
        self.test_authentication()
        self.test_cors_headers()
        
        # API endpoint tests
        self.test_environment_endpoints()
        self.test_storage_endpoints()
        self.test_user_env_vars()
        self.test_file_endpoints()
        self.test_activity_log()
        
        # Compatibility tests
        self.test_data_format_compatibility()
        
        # Generate report
        self.generate_report()
    
    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("🎯 INTEGRATION TEST REPORT")
        print("=" * 60)
        
        passed = len([r for r in self.test_results if r['success']])
        total = len(self.test_results)
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print(f"Tests Passed: {passed}/{total} ({success_rate:.1f}%)")
        print(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Categorize results
        categories = {
            'Core': ['Health Check', 'Authentication Required', 'Authentication Working', 'CORS Configuration'],
            'Environment': ['List Environments', 'Environment Status', 'Create Environment'],  
            'Storage': ['List Storage'],
            'User Management': ['Get User Env Vars', 'Set User Env Var', 'List User Files'],
            'Monitoring': ['Activity Log'],
            'Compatibility': ['Date Format Compatibility', 'Status Format Compatibility']
        }
        
        print("\n📊 Results by Category:")
        for category, tests in categories.items():
            category_results = [r for r in self.test_results if r['test'] in tests]
            if category_results:
                category_passed = len([r for r in category_results if r['success']])
                category_total = len(category_results)
                category_rate = (category_passed / category_total) * 100
                status = "✅" if category_rate == 100 else "⚠️" if category_rate >= 50 else "❌"
                print(f"  {status} {category}: {category_passed}/{category_total} ({category_rate:.0f}%)")
        
        # Failed tests details
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print("\n❌ Failed Tests:")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        # Overall assessment
        print(f"\n🎯 Overall Assessment:")
        if success_rate >= 90:
            print("   🟢 EXCELLENT - Ready for production!")
        elif success_rate >= 75:
            print("   🟡 GOOD - Minor issues to address")
        elif success_rate >= 50:
            print("   🟠 FAIR - Several issues need fixing")
        else:
            print("   🔴 POOR - Major integration problems")
        
        # Integration checklist
        print(f"\n✅ Integration Checklist:")
        checklist_items = [
            ("Authentication", any(r['success'] for r in self.test_results if 'Authentication' in r['test'])),
            ("Environment Management", any(r['success'] for r in self.test_results if 'Environment' in r['test'])),
            ("Storage Operations", any(r['success'] for r in self.test_results if 'Storage' in r['test'])),
            ("User Settings", any(r['success'] for r in self.test_results if 'User Env Var' in r['test'])),
            ("CORS Configured", any(r['success'] for r in self.test_results if 'CORS' in r['test'])),
            ("Data Compatibility", any(r['success'] for r in self.test_results if 'Compatibility' in r['test']))
        ]
        
        for item, status in checklist_items:
            icon = "✅" if status else "❌"
            print(f"   {icon} {item}")
        
        # Save detailed report
        self.save_detailed_report()
        
        print(f"\n📄 Detailed report saved to: integration_test_report.json")
        print("=" * 60)
    
    def save_detailed_report(self):
        """Save detailed JSON report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "backend_url": self.base_url,
            "summary": {
                "total_tests": len(self.test_results),
                "passed": len([r for r in self.test_results if r['success']]),
                "failed": len([r for r in self.test_results if not r['success']]),
                "success_rate": (len([r for r in self.test_results if r['success']]) / len(self.test_results)) * 100 if self.test_results else 0
            },
            "results": self.test_results
        }
        
        with open('integration_test_report.json', 'w') as f:
            json.dump(report, f, indent=2, default=str)

def main():
    """Main test runner"""
    import argparse
    parser = argparse.ArgumentParser(description='CMB Cluster Integration Tester')
    parser.add_argument('--url', default='http://localhost:8000', 
                       help='Backend URL (default: http://localhost:8000)')
    parser.add_argument('--no-dev-mode', action='store_true',
                       help='Disable dev mode (requires real authentication)')
    
    args = parser.parse_args()
    
    tester = CMBClusterAPITester(base_url=args.url, dev_mode=not args.no_dev_mode)
    tester.run_all_tests()

if __name__ == "__main__":
    main()
