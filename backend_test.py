#!/usr/bin/env python3
"""
GVIC Engine Dashboard Backend API Testing
Tests all major API endpoints for functionality
"""
import requests
import sys
import json
from datetime import datetime
from typing import Dict, Any

class GVICAPITester:
    def __init__(self, base_url="https://session-manager-35.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def log_test(self, name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        if response_data:
            result["response_sample"] = str(response_data)[:200]
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    {details}")
        if not success and response_data:
            print(f"    Response: {response_data}")

    def test_api_endpoint(self, method: str, endpoint: str, expected_status: int = 200, 
                         data: Dict = None, test_name: str = None) -> tuple:
        """Generic API test method"""
        url = f"{self.api_url}/{endpoint}"
        test_name = test_name or f"{method} {endpoint}"
        
        try:
            headers = {'Content-Type': 'application/json'}
            
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    self.log_test(test_name, True, f"Status: {response.status_code}", response_data)
                    return True, response_data
                except:
                    self.log_test(test_name, True, f"Status: {response.status_code}, Non-JSON response")
                    return True, response.text
            else:
                error_msg = f"Expected {expected_status}, got {response.status_code}"
                try:
                    error_data = response.json()
                    self.log_test(test_name, False, error_msg, error_data)
                except:
                    self.log_test(test_name, False, f"{error_msg}, Response: {response.text[:100]}")
                return False, None

        except requests.exceptions.RequestException as e:
            self.log_test(test_name, False, f"Request failed: {str(e)}")
            return False, None
        except Exception as e:
            self.log_test(test_name, False, f"Unexpected error: {str(e)}")
            return False, None

    def test_basic_connectivity(self):
        """Test basic API connectivity"""
        print("\n🔍 Testing Basic Connectivity...")
        return self.test_api_endpoint('GET', '', test_name="API Root Endpoint")

    def test_dashboard_apis(self):
        """Test dashboard related APIs"""
        print("\n📊 Testing Dashboard APIs...")
        
        # Main dashboard
        success, data = self.test_api_endpoint('GET', 'dashboard', test_name="Dashboard Data")
        
        # Dashboard charts
        self.test_api_endpoint('GET', 'dashboard/charts/distribution', test_name="Distribution Chart")
        self.test_api_endpoint('GET', 'dashboard/charts/convergence', test_name="Convergence Chart")
        
        return success

    def test_engine_apis(self):
        """Test engine processing APIs"""
        print("\n⚙️ Testing Engine APIs...")
        
        # Engine status
        self.test_api_endpoint('GET', 'engine/status', test_name="Engine Status")
        
        # Process single value
        process_data = {"value": 50.0, "source_type": "auto"}
        success, result = self.test_api_endpoint('POST', 'engine/process', data=process_data, test_name="Process Single Value")
        
        # Process batch
        batch_data = {"items": [{"value": 30}, {"value": 70}]}
        self.test_api_endpoint('POST', 'engine/batch', data=batch_data, test_name="Process Batch")
        
        # Reset engine
        self.test_api_endpoint('POST', 'engine/reset', test_name="Reset Engine")
        
        return success

    def test_config_apis(self):
        """Test configuration APIs"""
        print("\n⚙️ Testing Configuration APIs...")
        
        # Get sigma
        success, sigma_data = self.test_api_endpoint('GET', 'config/sigma', test_name="Get Sigma Config")
        
        # Update sigma
        new_sigma = {"sigma": [0.4, 0.4, 0.2]}
        self.test_api_endpoint('PUT', 'config/sigma', data=new_sigma, test_name="Update Sigma Config")
        
        # Get omega
        self.test_api_endpoint('GET', 'config/omega', test_name="Get Omega Config")
        
        # Update omega
        new_omega = {"V_pub_min": 0.2, "V_pub_max": 0.8, "V_ind_max": 0.5, "sum_constraint": 1.0}
        self.test_api_endpoint('PUT', 'config/omega', data=new_omega, test_name="Update Omega Config")
        
        return success

    def test_control_apis(self):
        """Test control system APIs"""
        print("\n🚨 Testing Control APIs...")
        
        # Health check
        self.test_api_endpoint('GET', 'control/health', test_name="Health Check")
        
        # Get alerts
        success, alerts = self.test_api_endpoint('GET', 'control/alerts', test_name="Get Alerts")
        
        # Get thresholds
        self.test_api_endpoint('GET', 'control/thresholds', test_name="Get Thresholds")
        
        return success

    def test_data_apis(self):
        """Test data management APIs"""
        print("\n💾 Testing Data APIs...")
        
        # Database stats
        success, stats = self.test_api_endpoint('GET', 'data/stats', test_name="Database Statistics")
        
        # Get processing results
        self.test_api_endpoint('GET', 'data/processing-results', test_name="Get Processing Results")
        
        # Get configs
        self.test_api_endpoint('GET', 'data/configs', test_name="Get All Configs")
        
        # Get alerts data
        self.test_api_endpoint('GET', 'data/alerts', test_name="Get Alerts Data")
        
        # Get metrics
        self.test_api_endpoint('GET', 'data/metrics', test_name="Get Metrics Data")
        
        # Test export (processing_results)
        self.test_api_endpoint('POST', 'data/export?collection=processing_results', test_name="Export Processing Results")
        
        return success

    def test_error_handling(self):
        """Test error handling"""
        print("\n🚫 Testing Error Handling...")
        
        # Invalid sigma (sum != 1.0)
        invalid_sigma = {"sigma": [0.6, 0.6, 0.2]}  # Sum = 1.4
        self.test_api_endpoint('PUT', 'config/sigma', data=invalid_sigma, expected_status=400, test_name="Invalid Sigma (Sum != 1.0)")
        
        # Invalid process value
        invalid_process = {"value": 150.0}  # Out of range
        self.test_api_endpoint('POST', 'engine/process', data=invalid_process, expected_status=422, test_name="Invalid Process Value")
        
        # Non-existent alert resolution
        self.test_api_endpoint('POST', 'control/alerts/nonexistent/resolve', expected_status=404, test_name="Resolve Non-existent Alert")

    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting GVIC Engine Dashboard API Tests")
        print(f"🌐 Testing against: {self.base_url}")
        print("=" * 60)
        
        # Run test categories
        basic_ok = self.test_basic_connectivity()
        if not basic_ok:
            print("\n❌ Basic connectivity failed. Stopping tests.")
            return self.generate_report()
        
        dashboard_ok = self.test_dashboard_apis()
        engine_ok = self.test_engine_apis()
        config_ok = self.test_config_apis()
        control_ok = self.test_control_apis()
        data_ok = self.test_data_apis()
        
        # Test error handling
        self.test_error_handling()
        
        return self.generate_report()

    def generate_report(self):
        """Generate test report"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        
        print(f"Total Tests: {self.tests_run}")
        print(f"Passed: {self.tests_passed}")
        print(f"Failed: {self.tests_run - self.tests_passed}")
        print(f"Success Rate: {success_rate:.1f}%")
        
        # Show failed tests
        failed_tests = [t for t in self.test_results if not t['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  • {test['test']}: {test['details']}")
        
        # Determine overall status
        if success_rate >= 80:
            print(f"\n✅ Overall Status: GOOD ({success_rate:.1f}%)")
            return 0
        elif success_rate >= 60:
            print(f"\n⚠️ Overall Status: ACCEPTABLE ({success_rate:.1f}%)")
            return 1
        else:
            print(f"\n❌ Overall Status: POOR ({success_rate:.1f}%)")
            return 2

def main():
    """Main test execution"""
    tester = GVICAPITester()
    return tester.run_all_tests()

if __name__ == "__main__":
    sys.exit(main())