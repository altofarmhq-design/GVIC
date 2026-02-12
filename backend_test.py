#!/usr/bin/env python3
"""
GVIC Engine Backend API Testing
Tests all backend endpoints for functionality and integration
"""

import requests
import json
import sys
from datetime import datetime
from typing import Dict, Any, List

class GVICAPITester:
    def __init__(self, base_url="https://patent-vizui.preview.emergentagent.com"):
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
            result["response_data"] = response_data
        
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}: {details}")

    def run_test(self, name: str, method: str, endpoint: str, expected_status: int = 200, 
                 data: Dict = None, headers: Dict = None) -> tuple:
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=30)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=30)
            else:
                raise ValueError(f"Unsupported method: {method}")

            success = response.status_code == expected_status
            
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text[:500]}
            
            details = f"Status: {response.status_code} (expected {expected_status})"
            if not success:
                details += f" | Response: {str(response_data)[:200]}"
            
            self.log_test(name, success, details, response_data if success else None)
            return success, response_data

        except Exception as e:
            self.log_test(name, False, f"Exception: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        return self.run_test("Root API", "GET", "")

    def test_dashboard_api(self):
        """Test dashboard data retrieval"""
        return self.run_test("Dashboard Data", "GET", "dashboard")

    def test_system_status(self):
        """Test system status endpoint"""
        return self.run_test("System Status", "GET", "status")

    def test_process_value(self):
        """Test value processing"""
        test_data = {"value": 0.75}
        return self.run_test("Process Value", "POST", "process", 200, test_data)

    def test_process_history(self):
        """Test processing history retrieval"""
        return self.run_test("Process History", "GET", "process/history")

    def test_sigma_config(self):
        """Test sigma configuration endpoints"""
        # Get sigma
        success1, data1 = self.run_test("Get Sigma", "GET", "config/sigma")
        
        # Update sigma
        test_sigma = {"sigma": [0.30, 0.35, 0.35]}
        success2, data2 = self.run_test("Update Sigma", "PUT", "config/sigma", 200, test_sigma)
        
        return success1 and success2

    def test_omega_config(self):
        """Test omega configuration endpoints"""
        # Get omega
        success1, data1 = self.run_test("Get Omega", "GET", "config/omega")
        
        # Update omega
        test_omega = {
            "V_pub_min": 0.2,
            "V_pub_max": 0.5,
            "V_pro_min": 0.2,
            "V_pro_max": 0.5,
            "V_ind_min": 0.1,
            "V_ind_max": 0.5,
            "sum_constraint": 1.0
        }
        success2, data2 = self.run_test("Update Omega", "PUT", "config/omega", 200, test_omega)
        
        return success1 and success2

    def test_all_config(self):
        """Test all configuration retrieval"""
        return self.run_test("All Config", "GET", "config")

    def test_io_processing(self):
        """Test IO processing"""
        test_cases = [
            {"data": '{"value": 0.75, "type": "market"}', "format": "json"},
            {"data": "value,type\n0.75,market", "format": "csv"},
            {"data": "value=0.75\ntype=market", "format": "key_value"}
        ]
        
        all_success = True
        for i, test_data in enumerate(test_cases):
            success, _ = self.run_test(f"IO Process {test_data['format'].upper()}", "POST", "io/process", 200, test_data)
            all_success = all_success and success
        
        return all_success

    def test_io_statistics(self):
        """Test IO statistics"""
        return self.run_test("IO Statistics", "GET", "io/statistics")

    def test_alerts_system(self):
        """Test alerts system"""
        # Get alerts
        success1, data1 = self.run_test("Get Alerts", "GET", "alerts")
        
        # Run health check
        success2, data2 = self.run_test("Health Check", "POST", "health-check")
        
        return success1 and success2

    def test_logs_system(self):
        """Test logs system"""
        # Get logs
        success1, data1 = self.run_test("Get Logs", "GET", "logs")
        
        # Create log entry
        log_entry = {
            "phase": "테스트",
            "action": "API 테스트 실행",
            "data": {"test": True}
        }
        success2, data2 = self.run_test("Create Log", "POST", "logs", 200, log_entry)
        
        # Get log statistics
        success3, data3 = self.run_test("Log Statistics", "GET", "logs/statistics")
        
        return success1 and success2 and success3

    def test_modules_status(self):
        """Test modules status"""
        return self.run_test("Module Status", "GET", "modules")

    def test_invalid_endpoints(self):
        """Test error handling for invalid endpoints"""
        # Test invalid process value
        invalid_data = {"value": 15}  # Out of range (0-10)
        success1, _ = self.run_test("Invalid Process Value", "POST", "process", 422, invalid_data)
        
        # Test invalid sigma (sum != 1)
        invalid_sigma = {"sigma": [0.5, 0.5, 0.5]}  # Sum = 1.5
        success2, _ = self.run_test("Invalid Sigma", "PUT", "config/sigma", 400, invalid_sigma)
        
        return success1 and success2

    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 Starting GVIC Engine API Tests")
        print("=" * 50)
        
        # Basic connectivity
        print("\n📡 Testing Basic Connectivity...")
        self.test_root_endpoint()
        
        # Dashboard and status
        print("\n📊 Testing Dashboard & Status...")
        self.test_dashboard_api()
        self.test_system_status()
        
        # Processing functionality
        print("\n⚙️ Testing Processing...")
        self.test_process_value()
        self.test_process_history()
        
        # Configuration management
        print("\n🔧 Testing Configuration...")
        self.test_sigma_config()
        self.test_omega_config()
        self.test_all_config()
        
        # IO and data handling
        print("\n💾 Testing IO & Data...")
        self.test_io_processing()
        self.test_io_statistics()
        
        # Alerts and monitoring
        print("\n🔔 Testing Alerts & Monitoring...")
        self.test_alerts_system()
        
        # Logging system
        print("\n📝 Testing Logging...")
        self.test_logs_system()
        
        # Module status
        print("\n🧩 Testing Modules...")
        self.test_modules_status()
        
        # Error handling
        print("\n❌ Testing Error Handling...")
        self.test_invalid_endpoints()
        
        # Final results
        print("\n" + "=" * 50)
        print(f"📈 Test Results: {self.tests_passed}/{self.tests_run} passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print("⚠️ Some tests failed. Check the details above.")
            failed_tests = [r for r in self.test_results if not r['success']]
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['details']}")
            return 1

def main():
    """Main test execution"""
    tester = GVICAPITester()
    return tester.run_comprehensive_test()

if __name__ == "__main__":
    sys.exit(main())