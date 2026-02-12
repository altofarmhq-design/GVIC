"""GVIC Engine API Tests
Tests for all backend API endpoints including:
- Dashboard API
- Process API
- Configuration APIs (Sigma/Omega)
- IO APIs
- Alert APIs
- Log APIs
- Module Status APIs
- Integration APIs
"""
import pytest
import requests
import os
import json

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestDashboardAPI:
    """Dashboard endpoint tests"""
    
    def test_root_endpoint(self):
        """Test root API endpoint"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "GVIC Engine API" in data["message"]
    
    def test_dashboard_endpoint(self):
        """Test dashboard data retrieval"""
        response = requests.get(f"{BASE_URL}/api/dashboard")
        assert response.status_code == 200
        data = response.json()
        
        # Verify structure
        assert "metrics" in data
        assert "sigma" in data
        assert "omega" in data
        assert "balance_score" in data
        assert "charts" in data
        
        # Verify metrics structure
        metrics = data["metrics"]
        assert "total_processed" in metrics
        assert "success_rate" in metrics
        assert "active_alerts" in metrics
        assert "system_status" in metrics
        
        # Verify sigma is a list of 3 values
        assert isinstance(data["sigma"], list)
        assert len(data["sigma"]) == 3
        
        # Verify charts structure
        charts = data["charts"]
        assert "distribution" in charts
        assert "balance" in charts
    
    def test_system_status_endpoint(self):
        """Test system status retrieval"""
        response = requests.get(f"{BASE_URL}/api/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "sigma" in data
        assert "omega" in data
        assert "total_processed" in data
        assert "success_rate" in data
        assert "modules" in data


class TestProcessAPI:
    """Process endpoint tests"""
    
    def test_process_valid_value(self):
        """Test processing with valid value"""
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"value": 5.0}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "data" in data
        assert "timestamp" in data
        
        # Verify result structure
        result_data = data["data"]
        assert "asset" in result_data
        assert "distribution" in result_data
        assert "convergence" in result_data
        assert "balance_score" in result_data
        
        # Verify distribution has all three domains
        dist = result_data["distribution"]
        assert "public" in dist
        assert "productive" in dist
        assert "individual" in dist
        
        # Verify convergence data
        conv = result_data["convergence"]
        assert "input_ratio" in conv
        assert "output_ratio" in conv
        assert "is_valid" in conv
    
    def test_process_boundary_values(self):
        """Test processing with boundary values"""
        # Test minimum value
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"value": 0}
        )
        assert response.status_code == 200
        
        # Test maximum value
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"value": 10}
        )
        assert response.status_code == 200
    
    def test_process_invalid_value(self):
        """Test processing with invalid value (out of range)"""
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"value": -1}
        )
        assert response.status_code == 422  # Validation error
        
        response = requests.post(
            f"{BASE_URL}/api/process",
            json={"value": 11}
        )
        assert response.status_code == 422
    
    def test_process_history(self):
        """Test processing history retrieval"""
        response = requests.get(f"{BASE_URL}/api/process/history")
        assert response.status_code == 200
        data = response.json()
        
        assert "history" in data
        assert "count" in data
        assert isinstance(data["history"], list)


class TestConfigurationAPI:
    """Configuration endpoint tests (Sigma/Omega)"""
    
    def test_get_sigma(self):
        """Test sigma retrieval"""
        response = requests.get(f"{BASE_URL}/api/config/sigma")
        assert response.status_code == 200
        data = response.json()
        
        assert "sigma" in data
        assert isinstance(data["sigma"], list)
        assert len(data["sigma"]) == 3
        
        # Verify sum is approximately 1.0
        sigma_sum = sum(data["sigma"])
        assert abs(sigma_sum - 1.0) < 0.02
    
    def test_update_sigma_valid(self):
        """Test sigma update with valid values"""
        # First get current sigma
        get_response = requests.get(f"{BASE_URL}/api/config/sigma")
        original_sigma = get_response.json()["sigma"]
        
        # Update sigma
        new_sigma = [0.33, 0.34, 0.33]
        response = requests.put(
            f"{BASE_URL}/api/config/sigma",
            json={"sigma": new_sigma}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "sigma" in data
        
        # Restore original sigma
        requests.put(
            f"{BASE_URL}/api/config/sigma",
            json={"sigma": original_sigma}
        )
    
    def test_update_sigma_invalid_sum(self):
        """Test sigma update with invalid sum (not equal to 1)"""
        response = requests.put(
            f"{BASE_URL}/api/config/sigma",
            json={"sigma": [0.5, 0.5, 0.5]}  # Sum = 1.5
        )
        assert response.status_code == 400
    
    def test_get_omega(self):
        """Test omega retrieval"""
        response = requests.get(f"{BASE_URL}/api/config/omega")
        assert response.status_code == 200
        data = response.json()
        
        assert "omega" in data
        omega = data["omega"]
        
        # Verify omega structure
        assert "V_pub_min" in omega
        assert "V_pub_max" in omega
        assert "V_pro_min" in omega
        assert "V_pro_max" in omega
        assert "V_ind_min" in omega
        assert "V_ind_max" in omega
    
    def test_update_omega(self):
        """Test omega update"""
        # Get current omega
        get_response = requests.get(f"{BASE_URL}/api/config/omega")
        original_omega = get_response.json()["omega"]
        
        # Update omega
        new_omega = {
            "V_pub_min": 0.2,
            "V_pub_max": 0.5,
            "V_pro_min": 0.2,
            "V_pro_max": 0.5,
            "V_ind_min": 0.1,
            "V_ind_max": 0.5,
            "sum_constraint": 1.0
        }
        response = requests.put(
            f"{BASE_URL}/api/config/omega",
            json=new_omega
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        
        # Restore original omega
        requests.put(
            f"{BASE_URL}/api/config/omega",
            json=original_omega
        )
    
    def test_get_all_config(self):
        """Test all configuration retrieval"""
        response = requests.get(f"{BASE_URL}/api/config")
        assert response.status_code == 200
        data = response.json()
        
        assert "sigma" in data
        assert "omega" in data


class TestIOAPI:
    """IO endpoint tests"""
    
    def test_process_io_json(self):
        """Test IO processing with JSON format"""
        response = requests.post(
            f"{BASE_URL}/api/io/process",
            json={"data": '{"value": 10.5, "type": "market"}', "format": "json"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "data" in data
    
    def test_process_io_csv(self):
        """Test IO processing with CSV format"""
        response = requests.post(
            f"{BASE_URL}/api/io/process",
            json={"data": "value,type\n10.5,market", "format": "csv"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
    
    def test_process_io_key_value(self):
        """Test IO processing with key-value format"""
        response = requests.post(
            f"{BASE_URL}/api/io/process",
            json={"data": "value=10.5\ntype=market", "format": "key_value"}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
    
    def test_io_statistics(self):
        """Test IO statistics retrieval"""
        response = requests.get(f"{BASE_URL}/api/io/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_processed" in data


class TestAlertAPI:
    """Alert endpoint tests"""
    
    def test_get_alerts(self):
        """Test alerts retrieval"""
        response = requests.get(f"{BASE_URL}/api/alerts")
        assert response.status_code == 200
        data = response.json()
        
        assert "active_alerts" in data
        assert "statistics" in data
        
        stats = data["statistics"]
        assert "total" in stats
        assert "active" in stats
        assert "resolved" in stats
    
    def test_health_check(self):
        """Test health check execution"""
        response = requests.post(f"{BASE_URL}/api/health-check")
        assert response.status_code == 200
        data = response.json()
        
        assert "results" in data
        assert "summary" in data


class TestLogAPI:
    """Log endpoint tests"""
    
    def test_get_logs(self):
        """Test logs retrieval"""
        response = requests.get(f"{BASE_URL}/api/logs")
        assert response.status_code == 200
        data = response.json()
        
        assert "logs" in data
        assert "count" in data
        assert isinstance(data["logs"], list)
    
    def test_create_log(self):
        """Test log creation"""
        response = requests.post(
            f"{BASE_URL}/api/logs",
            json={"phase": "테스트", "action": "API 테스트 실행", "data": {"test": True}}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
    
    def test_log_statistics(self):
        """Test log statistics retrieval"""
        response = requests.get(f"{BASE_URL}/api/logs/statistics")
        assert response.status_code == 200
        data = response.json()
        
        assert "total_logs" in data


class TestModuleAPI:
    """Module status endpoint tests"""
    
    def test_get_modules(self):
        """Test module status retrieval"""
        response = requests.get(f"{BASE_URL}/api/modules")
        assert response.status_code == 200
        data = response.json()
        
        assert "modules" in data
        modules = data["modules"]
        
        assert isinstance(modules, list)
        assert len(modules) >= 6  # At least 6 modules
        
        # Verify module structure
        for module in modules:
            assert "name" in module
            assert "status" in module
            assert "description" in module


class TestIntegrationAPI:
    """Integration endpoint tests (Patent 6-J)"""
    
    def test_get_integration_status(self):
        """Test integration status retrieval"""
        response = requests.get(f"{BASE_URL}/api/integration/status")
        assert response.status_code == 200
        data = response.json()
        
        assert "adapters" in data
        assert "semantic_mappings" in data
        assert "routing" in data
    
    def test_get_adapters(self):
        """Test adapters retrieval"""
        response = requests.get(f"{BASE_URL}/api/integration/adapters")
        assert response.status_code == 200
        data = response.json()
        
        assert "adapters" in data
        assert isinstance(data["adapters"], list)
    
    def test_get_mappings(self):
        """Test semantic mappings retrieval"""
        response = requests.get(f"{BASE_URL}/api/integration/mappings")
        assert response.status_code == 200
        data = response.json()
        
        assert "mappings" in data
        assert isinstance(data["mappings"], list)
    
    def test_get_routing_rules(self):
        """Test routing rules retrieval"""
        response = requests.get(f"{BASE_URL}/api/integration/routing")
        assert response.status_code == 200
        data = response.json()
        
        assert "rules" in data
        assert isinstance(data["rules"], list)
    
    def test_execute_exchange(self):
        """Test data exchange execution"""
        response = requests.post(
            f"{BASE_URL}/api/integration/exchange",
            json={
                "data": {"order_id": "TEST-001", "amount": 1000},
                "source_domain": "erp",
                "message_type": "order"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
    
    def test_create_adapter(self):
        """Test adapter creation"""
        response = requests.post(
            f"{BASE_URL}/api/integration/adapters",
            json={
                "domain_id": "test_domain",
                "domain_type": "custom",
                "protocol": "rest",
                "endpoint": "http://test.example.com"
            }
        )
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "adapter" in data


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
