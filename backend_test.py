import requests
import sys
from datetime import datetime, timezone, timedelta
import json

class TaskManagerAPITester:
    def __init__(self, base_url="https://patentforge.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.created_tasks = []
        self.created_categories = []

    def run_test(self, name, method, endpoint, expected_status, data=None, params=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, params=params)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    print(f"   Response: {response.text}")
                except:
                    pass
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test root API endpoint"""
        success, response = self.run_test("Root Endpoint", "GET", "", 200)
        return success

    def test_category_crud(self):
        """Test category CRUD operations"""
        print("\n📁 Testing Category Operations...")
        
        # Create category
        category_data = {
            "name": "Test Work Category",
            "color": "blue"
        }
        success, response = self.run_test("Create Category", "POST", "categories", 200, category_data)
        if not success:
            return False
        
        category_id = response.get('id')
        if category_id:
            self.created_categories.append(category_id)
        
        # Get all categories
        success, response = self.run_test("Get All Categories", "GET", "categories", 200)
        if not success:
            return False
        
        # Update category
        update_data = {
            "name": "Updated Work Category",
            "color": "green"
        }
        success, response = self.run_test("Update Category", "PUT", f"categories/{category_id}", 200, update_data)
        if not success:
            return False
        
        return True

    def test_task_crud(self):
        """Test task CRUD operations"""
        print("\n📝 Testing Task Operations...")
        
        # Create task
        due_date = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
        task_data = {
            "title": "Test Task for API Testing",
            "description": "This is a test task created by automated testing",
            "status": "todo",
            "priority": "high",
            "due_date": due_date,
            "category_id": self.created_categories[0] if self.created_categories else None
        }
        success, response = self.run_test("Create Task", "POST", "tasks", 200, task_data)
        if not success:
            return False
        
        task_id = response.get('id')
        if task_id:
            self.created_tasks.append(task_id)
        
        # Get all tasks
        success, response = self.run_test("Get All Tasks", "GET", "tasks", 200)
        if not success:
            return False
        
        # Get single task
        success, response = self.run_test("Get Single Task", "GET", f"tasks/{task_id}", 200)
        if not success:
            return False
        
        # Update task
        update_data = {
            "title": "Updated Test Task",
            "status": "in_progress",
            "priority": "urgent"
        }
        success, response = self.run_test("Update Task", "PUT", f"tasks/{task_id}", 200, update_data)
        if not success:
            return False
        
        return True

    def test_task_filtering(self):
        """Test task filtering"""
        print("\n🔍 Testing Task Filtering...")
        
        # Filter by status
        success, response = self.run_test("Filter Tasks by Status", "GET", "tasks", 200, params={"status": "todo"})
        if not success:
            return False
        
        # Filter by priority
        success, response = self.run_test("Filter Tasks by Priority", "GET", "tasks", 200, params={"priority": "high"})
        if not success:
            return False
        
        return True

    def test_task_stats(self):
        """Test task statistics endpoint"""
        print("\n📊 Testing Task Statistics...")
        
        success, response = self.run_test("Get Task Stats", "GET", "tasks/stats/overview", 200)
        if not success:
            return False
        
        # Verify stats structure
        required_fields = ['total', 'todo', 'in_progress', 'done', 'overdue', 'due_soon']
        for field in required_fields:
            if field not in response:
                print(f"❌ Missing field in stats: {field}")
                return False
        
        print(f"✅ Stats structure valid: {response}")
        return True

    def test_error_handling(self):
        """Test error handling"""
        print("\n⚠️ Testing Error Handling...")
        
        # Test non-existent task
        success, response = self.run_test("Get Non-existent Task", "GET", "tasks/non-existent-id", 404)
        if not success:
            return False
        
        # Test non-existent category
        success, response = self.run_test("Get Non-existent Category", "PUT", "categories/non-existent-id", 404, {"name": "test"})
        if not success:
            return False
        
        # Test invalid task creation (empty title)
        invalid_task = {"title": "", "description": "test"}
        success, response = self.run_test("Create Invalid Task", "POST", "tasks", 422, invalid_task)
        if not success:
            return False
        
        return True

    def cleanup(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete created tasks
        for task_id in self.created_tasks:
            success, _ = self.run_test(f"Delete Task {task_id}", "DELETE", f"tasks/{task_id}", 200)
        
        # Delete created categories
        for category_id in self.created_categories:
            success, _ = self.run_test(f"Delete Category {category_id}", "DELETE", f"categories/{category_id}", 200)

def main():
    print("🚀 Starting Task Manager API Tests...")
    print("=" * 50)
    
    tester = TaskManagerAPITester()
    
    try:
        # Run all tests
        tests = [
            tester.test_root_endpoint,
            tester.test_category_crud,
            tester.test_task_crud,
            tester.test_task_filtering,
            tester.test_task_stats,
            tester.test_error_handling
        ]
        
        all_passed = True
        for test in tests:
            if not test():
                all_passed = False
        
        # Cleanup
        tester.cleanup()
        
        # Print results
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
        
        if all_passed:
            print("🎉 All API tests passed!")
            return 0
        else:
            print("❌ Some tests failed")
            return 1
            
    except Exception as e:
        print(f"💥 Test suite failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())