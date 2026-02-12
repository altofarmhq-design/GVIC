"""Data Sources API Tests
Tests for external data source integration endpoints:
- GET /api/datasources (목록 조회)
- POST /api/datasources (생성)
- GET /api/datasources/{source_id} (상세 조회)
- PUT /api/datasources/{source_id} (수정)
- DELETE /api/datasources/{source_id} (삭제)
- POST /api/datasources/{source_id}/fetch (데이터 가져오기)
- GET /api/datasources/collected (수집 데이터 조회)
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data source configuration
TEST_SOURCE_CONFIG = {
    "name": "TEST_JSONPlaceholder API",
    "source_type": "api",
    "url": "https://jsonplaceholder.typicode.com/posts/1",
    "method": "GET",
    "auth_type": "none",
    "auth_value": "",
    "polling_interval": 60,
    "data_mapping": {"value": "id"},
    "enabled": True
}


class TestDataSourcesCRUD:
    """Data Sources CRUD endpoint tests"""
    
    created_source_id = None
    
    def test_01_get_datasources_list(self):
        """Test GET /api/datasources - 데이터 소스 목록 조회"""
        response = requests.get(f"{BASE_URL}/api/datasources")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "sources" in data
        assert "total" in data
        assert isinstance(data["sources"], list)
        assert isinstance(data["total"], int)
        print(f"✓ Found {data['total']} data sources")
    
    def test_02_create_datasource(self):
        """Test POST /api/datasources - 데이터 소스 생성"""
        response = requests.post(
            f"{BASE_URL}/api/datasources",
            json=TEST_SOURCE_CONFIG
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert data["success"] == True
        assert "source_id" in data
        assert "source" in data
        
        # Store source_id for subsequent tests
        TestDataSourcesCRUD.created_source_id = data["source_id"]
        
        # Verify source data
        source = data["source"]
        assert source["name"] == TEST_SOURCE_CONFIG["name"]
        assert source["source_type"] == TEST_SOURCE_CONFIG["source_type"]
        assert source["url"] == TEST_SOURCE_CONFIG["url"]
        assert source["method"] == TEST_SOURCE_CONFIG["method"]
        assert source["enabled"] == TEST_SOURCE_CONFIG["enabled"]
        
        print(f"✓ Created data source with ID: {data['source_id']}")
    
    def test_03_get_datasource_detail(self):
        """Test GET /api/datasources/{source_id} - 데이터 소스 상세 조회"""
        source_id = TestDataSourcesCRUD.created_source_id
        if not source_id:
            pytest.skip("No source_id available from previous test")
        
        response = requests.get(f"{BASE_URL}/api/datasources/{source_id}")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "source" in data
        assert "id" in data
        assert data["id"] == source_id
        
        # Verify source data
        source = data["source"]
        assert source["name"] == TEST_SOURCE_CONFIG["name"]
        assert source["url"] == TEST_SOURCE_CONFIG["url"]
        
        print(f"✓ Retrieved data source detail: {source['name']}")
    
    def test_04_get_datasource_not_found(self):
        """Test GET /api/datasources/{source_id} - 존재하지 않는 소스 조회"""
        response = requests.get(f"{BASE_URL}/api/datasources/nonexistent_id")
        assert response.status_code == 404
        print("✓ Correctly returned 404 for non-existent source")
    
    def test_05_update_datasource(self):
        """Test PUT /api/datasources/{source_id} - 데이터 소스 수정"""
        source_id = TestDataSourcesCRUD.created_source_id
        if not source_id:
            pytest.skip("No source_id available from previous test")
        
        updated_config = {
            **TEST_SOURCE_CONFIG,
            "name": "TEST_Updated API Source",
            "polling_interval": 120
        }
        
        response = requests.put(
            f"{BASE_URL}/api/datasources/{source_id}",
            json=updated_config
        )
        assert response.status_code == 200
        data = response.json()
        
        # Verify update success
        assert data["success"] == True
        assert "source" in data
        
        # Verify updated values
        source = data["source"]
        assert source["name"] == "TEST_Updated API Source"
        assert source["polling_interval"] == 120
        
        print(f"✓ Updated data source: {source['name']}")
    
    def test_06_update_datasource_not_found(self):
        """Test PUT /api/datasources/{source_id} - 존재하지 않는 소스 수정"""
        response = requests.put(
            f"{BASE_URL}/api/datasources/nonexistent_id",
            json=TEST_SOURCE_CONFIG
        )
        assert response.status_code == 404
        print("✓ Correctly returned 404 for updating non-existent source")


class TestDataSourcesFetch:
    """Data Sources fetch and collected data tests"""
    
    def test_01_fetch_datasource(self):
        """Test POST /api/datasources/{source_id}/fetch - 데이터 가져오기"""
        # First get a valid source_id
        list_response = requests.get(f"{BASE_URL}/api/datasources")
        sources = list_response.json().get("sources", [])
        
        # Find a source with valid URL (jsonplaceholder)
        valid_source = None
        for source in sources:
            if "jsonplaceholder" in (source.get("url") or ""):
                valid_source = source
                break
        
        if not valid_source:
            pytest.skip("No valid test source available")
        
        source_id = valid_source["id"]
        
        response = requests.post(f"{BASE_URL}/api/datasources/{source_id}/fetch")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        assert "source_id" in data
        
        if data["success"]:
            assert "raw_data" in data or "data" in data
            assert "extracted_value" in data
            print(f"✓ Fetched data successfully, extracted value: {data.get('extracted_value')}")
        else:
            print(f"✓ Fetch completed with error: {data.get('error')}")
    
    def test_02_fetch_datasource_not_found(self):
        """Test POST /api/datasources/{source_id}/fetch - 존재하지 않는 소스에서 가져오기"""
        response = requests.post(f"{BASE_URL}/api/datasources/nonexistent_id/fetch")
        assert response.status_code == 404
        print("✓ Correctly returned 404 for fetching from non-existent source")
    
    def test_03_get_collected_data(self):
        """Test GET /api/datasources/collected - 수집된 데이터 조회"""
        response = requests.get(f"{BASE_URL}/api/datasources/collected")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "data" in data
        assert "total" in data
        assert isinstance(data["data"], list)
        
        # If there's collected data, verify structure
        if data["data"]:
            item = data["data"][0]
            assert "source_id" in item
            assert "source_name" in item
            assert "timestamp" in item
            assert "extracted_value" in item
            print(f"✓ Found {data['total']} collected data records")
        else:
            print("✓ No collected data yet (empty list)")
    
    def test_04_get_collected_data_with_filter(self):
        """Test GET /api/datasources/collected with source_id filter"""
        # First get a valid source_id
        list_response = requests.get(f"{BASE_URL}/api/datasources")
        sources = list_response.json().get("sources", [])
        
        if not sources:
            pytest.skip("No sources available for filtering")
        
        source_id = sources[0]["id"]
        
        response = requests.get(
            f"{BASE_URL}/api/datasources/collected",
            params={"source_id_filter": source_id, "limit": 10}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert isinstance(data["data"], list)
        print(f"✓ Filtered collected data by source_id: {source_id}")
    
    def test_05_get_collected_data_with_limit(self):
        """Test GET /api/datasources/collected with limit parameter"""
        response = requests.get(
            f"{BASE_URL}/api/datasources/collected",
            params={"limit": 5}
        )
        assert response.status_code == 200
        data = response.json()
        
        assert "data" in data
        assert len(data["data"]) <= 5
        print(f"✓ Limited collected data to {len(data['data'])} records")


class TestDataSourcesDelete:
    """Data Sources delete tests - run last to clean up"""
    
    def test_01_delete_datasource(self):
        """Test DELETE /api/datasources/{source_id} - 데이터 소스 삭제"""
        # Get the test source we created
        list_response = requests.get(f"{BASE_URL}/api/datasources")
        sources = list_response.json().get("sources", [])
        
        # Find our test source
        test_source = None
        for source in sources:
            if source.get("name", "").startswith("TEST_"):
                test_source = source
                break
        
        if not test_source:
            pytest.skip("No test source to delete")
        
        source_id = test_source["id"]
        
        response = requests.delete(f"{BASE_URL}/api/datasources/{source_id}")
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] == True
        assert "deleted_source_id" in data
        assert data["deleted_source_id"] == source_id
        
        print(f"✓ Deleted data source: {source_id}")
        
        # Verify deletion
        verify_response = requests.get(f"{BASE_URL}/api/datasources/{source_id}")
        assert verify_response.status_code == 404
        print("✓ Verified source no longer exists")
    
    def test_02_delete_datasource_not_found(self):
        """Test DELETE /api/datasources/{source_id} - 존재하지 않는 소스 삭제"""
        response = requests.delete(f"{BASE_URL}/api/datasources/nonexistent_id")
        assert response.status_code == 404
        print("✓ Correctly returned 404 for deleting non-existent source")


class TestDataSourcesProcess:
    """Data Sources process tests"""
    
    def test_01_process_datasource(self):
        """Test POST /api/datasources/{source_id}/process - GVIC 처리"""
        # First get a valid source_id with collected data
        list_response = requests.get(f"{BASE_URL}/api/datasources")
        sources = list_response.json().get("sources", [])
        
        # Find a source with valid URL
        valid_source = None
        for source in sources:
            if "jsonplaceholder" in (source.get("url") or ""):
                valid_source = source
                break
        
        if not valid_source:
            pytest.skip("No valid test source available")
        
        source_id = valid_source["id"]
        
        # First fetch data
        fetch_response = requests.post(f"{BASE_URL}/api/datasources/{source_id}/fetch")
        
        # Then process
        response = requests.post(f"{BASE_URL}/api/datasources/{source_id}/process")
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "success" in data
        
        if data["success"]:
            assert "process_result" in data
            print(f"✓ Processed data source successfully")
        else:
            print(f"✓ Process completed with message: {data.get('message')}")
    
    def test_02_process_datasource_not_found(self):
        """Test POST /api/datasources/{source_id}/process - 존재하지 않는 소스 처리"""
        response = requests.post(f"{BASE_URL}/api/datasources/nonexistent_id/process")
        assert response.status_code == 404
        print("✓ Correctly returned 404 for processing non-existent source")


class TestDataSourcesPolling:
    """Data Sources start/stop polling tests"""
    
    def test_01_start_polling(self):
        """Test POST /api/datasources/{source_id}/start - 자동 수집 시작"""
        # Get a valid source
        list_response = requests.get(f"{BASE_URL}/api/datasources")
        sources = list_response.json().get("sources", [])
        
        valid_source = None
        for source in sources:
            if "jsonplaceholder" in (source.get("url") or ""):
                valid_source = source
                break
        
        if not valid_source:
            pytest.skip("No valid test source available")
        
        source_id = valid_source["id"]
        
        response = requests.post(f"{BASE_URL}/api/datasources/{source_id}/start")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        print(f"✓ Start polling response: {data}")
    
    def test_02_stop_polling(self):
        """Test POST /api/datasources/{source_id}/stop - 자동 수집 중지"""
        # Get a valid source
        list_response = requests.get(f"{BASE_URL}/api/datasources")
        sources = list_response.json().get("sources", [])
        
        valid_source = None
        for source in sources:
            if "jsonplaceholder" in (source.get("url") or ""):
                valid_source = source
                break
        
        if not valid_source:
            pytest.skip("No valid test source available")
        
        source_id = valid_source["id"]
        
        response = requests.post(f"{BASE_URL}/api/datasources/{source_id}/stop")
        assert response.status_code == 200
        data = response.json()
        
        assert "success" in data
        print(f"✓ Stop polling response: {data}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
