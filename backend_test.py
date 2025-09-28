#!/usr/bin/env python3
"""
Backend API Testing for Employee Dashboard and Leave Management System
Tests all newly implemented APIs for Employee Dashboard cards and Leave management
"""

import requests
import json
import uuid
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

class BackendTester:
    def __init__(self):
        self.employee_token = None
        self.admin_token = None
        self.manager_token = None
        self.test_results = []
        self.employee_id = None
        self.admin_id = None
        self.manager_id = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def setup_test_users(self):
        """Create test users for testing"""
        print("\n=== Setting up test users ===")
        
        # Create test employee
        employee_data = {
            "name": "John Employee",
            "email": f"employee_{uuid.uuid4().hex[:8]}@test.com",
            "phone": f"555{uuid.uuid4().hex[:7]}",
            "password": "testpass123"
        }
        
        try:
            response = requests.post(f"{API_BASE}/auth/register", json=employee_data)
            if response.status_code == 200:
                self.employee_token = response.json()["access_token"]
                # Get employee ID
                headers = {"Authorization": f"Bearer {self.employee_token}"}
                me_response = requests.get(f"{API_BASE}/auth/me", headers=headers)
                if me_response.status_code == 200:
                    self.employee_id = me_response.json()["id"]
                self.log_result("Employee Registration", True, "Test employee created successfully")
            else:
                self.log_result("Employee Registration", False, f"Failed to create employee: {response.text}")
                return False
        except Exception as e:
            self.log_result("Employee Registration", False, f"Exception: {str(e)}")
            return False
        
        # Try to create test admin, if fails try to use existing admin
        admin_data = {
            "name": "Admin User",
            "email": f"admin_{uuid.uuid4().hex[:8]}@test.com",
            "password": "adminpass123"
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/auth/create", json=admin_data)
            if response.status_code == 200:
                self.admin_token = response.json()["access_token"]
                # Get admin ID
                headers = {"Authorization": f"Bearer {self.admin_token}"}
                me_response = requests.get(f"{API_BASE}/admin/auth/me", headers=headers)
                if me_response.status_code == 200:
                    self.admin_id = me_response.json()["id"]
                self.log_result("Admin Registration", True, "Test admin created successfully")
            else:
                # Try to login with the existing admin if creation fails
                default_admin_login = {
                    "email": "admin@worktracker.com",
                    "password": "admin123"
                }
                login_response = requests.post(f"{API_BASE}/admin/auth/login", json=default_admin_login)
                if login_response.status_code == 200:
                    self.admin_token = login_response.json()["access_token"]
                    # Get admin ID
                    headers = {"Authorization": f"Bearer {self.admin_token}"}
                    me_response = requests.get(f"{API_BASE}/admin/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        self.admin_id = me_response.json()["id"]
                    self.log_result("Admin Registration", True, "Using existing admin for testing")
                else:
                    self.log_result("Admin Registration", False, f"Failed to create or login admin: {response.text}")
                    return False
        except Exception as e:
            self.log_result("Admin Registration", False, f"Exception: {str(e)}")
            return False
            
        return True
    
    def test_employee_projects_api(self):
        """Test GET /api/employee/projects"""
        print("\n=== Testing Employee Projects API ===")
        
        if not self.employee_token:
            self.log_result("Employee Projects API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        try:
            response = requests.get(f"{API_BASE}/employee/projects", headers=headers)
            
            if response.status_code == 200:
                projects = response.json()
                self.log_result("Employee Projects API", True, f"Retrieved {len(projects)} projects", 
                              {"projects_count": len(projects), "response": projects})
            else:
                self.log_result("Employee Projects API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Employee Projects API", False, f"Exception: {str(e)}")
    
    def test_leave_balance_api(self):
        """Test GET /api/employee/leave-balance"""
        print("\n=== Testing Leave Balance API ===")
        
        if not self.employee_token:
            self.log_result("Leave Balance API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        try:
            response = requests.get(f"{API_BASE}/employee/leave-balance", headers=headers)
            
            if response.status_code == 200:
                balance = response.json()
                
                # Validate response structure
                required_keys = ["casual_leave", "sick_leave", "leave_without_pay", "quarter"]
                missing_keys = [key for key in required_keys if key not in balance]
                
                if missing_keys:
                    self.log_result("Leave Balance API", False, f"Missing keys in response: {missing_keys}")
                else:
                    # Validate leave type structure
                    for leave_type in ["casual_leave", "sick_leave", "leave_without_pay"]:
                        if leave_type in balance:
                            leave_data = balance[leave_type]
                            if not all(key in leave_data for key in ["allocated", "used", "available"]):
                                self.log_result("Leave Balance API", False, f"Invalid structure for {leave_type}")
                                return
                    
                    self.log_result("Leave Balance API", True, "Leave balance retrieved successfully", 
                                  {"balance": balance})
            else:
                self.log_result("Leave Balance API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Leave Balance API", False, f"Exception: {str(e)}")
    
    def test_apply_leave_api(self):
        """Test POST /api/employee/apply-leave"""
        print("\n=== Testing Apply Leave API ===")
        
        if not self.employee_token:
            self.log_result("Apply Leave API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        # Test valid leave application
        leave_data = {
            "leave_type": "Casual Leave",
            "start_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "reason": "Personal work",
            "days_count": 1.0
        }
        
        try:
            response = requests.post(f"{API_BASE}/employee/apply-leave", json=leave_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if "id" in result:
                    self.log_result("Apply Leave API", True, "Leave application submitted successfully", 
                                  {"leave_id": result["id"]})
                else:
                    self.log_result("Apply Leave API", False, "No leave ID returned in response")
            else:
                self.log_result("Apply Leave API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Apply Leave API", False, f"Exception: {str(e)}")
        
        # Test invalid leave application (excessive days)
        invalid_leave_data = {
            "leave_type": "Casual Leave",
            "start_date": (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=20)).strftime("%Y-%m-%d"),
            "reason": "Long vacation",
            "days_count": 100.0  # Excessive days
        }
        
        try:
            response = requests.post(f"{API_BASE}/employee/apply-leave", json=invalid_leave_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Apply Leave API - Validation", True, "Correctly rejected excessive leave days")
            else:
                self.log_result("Apply Leave API - Validation", False, 
                              f"Should have rejected excessive days but got HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Apply Leave API - Validation", False, f"Exception: {str(e)}")
    
    def test_employee_leave_requests_api(self):
        """Test GET /api/employee/leave-requests"""
        print("\n=== Testing Employee Leave Requests API ===")
        
        if not self.employee_token:
            self.log_result("Employee Leave Requests API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        try:
            response = requests.get(f"{API_BASE}/employee/leave-requests", headers=headers)
            
            if response.status_code == 200:
                requests_list = response.json()
                self.log_result("Employee Leave Requests API", True, 
                              f"Retrieved {len(requests_list)} leave requests", 
                              {"requests_count": len(requests_list)})
            else:
                self.log_result("Employee Leave Requests API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Employee Leave Requests API", False, f"Exception: {str(e)}")
    
    def test_manager_leave_requests_api(self):
        """Test GET /api/manager/leave-requests"""
        print("\n=== Testing Manager Leave Requests API ===")
        
        if not self.employee_token:
            self.log_result("Manager Leave Requests API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        try:
            response = requests.get(f"{API_BASE}/manager/leave-requests", headers=headers)
            
            if response.status_code == 200:
                requests_list = response.json()
                self.log_result("Manager Leave Requests API", True, 
                              f"Retrieved {len(requests_list)} pending requests for manager approval", 
                              {"pending_requests": len(requests_list)})
            else:
                self.log_result("Manager Leave Requests API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Manager Leave Requests API", False, f"Exception: {str(e)}")
    
    def test_manager_leave_decision_api(self):
        """Test PUT /api/manager/leave-requests/{id}"""
        print("\n=== Testing Manager Leave Decision API ===")
        
        if not self.employee_token:
            self.log_result("Manager Leave Decision API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        # First, try to get pending requests to find one to approve
        try:
            response = requests.get(f"{API_BASE}/manager/leave-requests", headers=headers)
            
            if response.status_code == 200:
                requests_list = response.json()
                
                if requests_list:
                    # Try to approve the first request
                    request_id = requests_list[0]["id"]
                    approval_data = {
                        "status": "approved",
                        "manager_reason": "Approved for testing purposes"
                    }
                    
                    approve_response = requests.put(f"{API_BASE}/manager/leave-requests/{request_id}", 
                                                  json=approval_data, headers=headers)
                    
                    if approve_response.status_code == 200:
                        self.log_result("Manager Leave Decision API", True, "Leave request approved successfully")
                    else:
                        self.log_result("Manager Leave Decision API", False, 
                                      f"HTTP {approve_response.status_code}: {approve_response.text}")
                else:
                    # Test with dummy ID to check error handling
                    dummy_id = str(uuid.uuid4())
                    approval_data = {
                        "status": "approved",
                        "manager_reason": "Test approval"
                    }
                    
                    approve_response = requests.put(f"{API_BASE}/manager/leave-requests/{dummy_id}", 
                                                  json=approval_data, headers=headers)
                    
                    if approve_response.status_code == 404:
                        self.log_result("Manager Leave Decision API", True, "Correctly handled non-existent request")
                    else:
                        self.log_result("Manager Leave Decision API", False, 
                                      f"Should return 404 for non-existent request, got {approve_response.status_code}")
            else:
                self.log_result("Manager Leave Decision API", False, 
                              f"Could not fetch pending requests: HTTP {response.status_code}")
                
        except Exception as e:
            self.log_result("Manager Leave Decision API", False, f"Exception: {str(e)}")
    
    def test_it_tickets_creation_api(self):
        """Test POST /api/employee/it-tickets"""
        print("\n=== Testing IT Tickets Creation API ===")
        
        if not self.employee_token:
            self.log_result("IT Tickets Creation API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        # Test all 6 IT categories
        categories = [
            "Hardware Issues",
            "Software Issues", 
            "Network/Connectivity",
            "Account/Access",
            "Security",
            "General Support"
        ]
        
        for category in categories:
            ticket_data = {
                "title": f"Test {category} Ticket",
                "description": f"This is a test ticket for {category} category",
                "category": category,
                "priority": "Medium"
            }
            
            try:
                response = requests.post(f"{API_BASE}/employee/it-tickets", json=ticket_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if "id" in result:
                        self.log_result(f"IT Ticket Creation - {category}", True, 
                                      f"Ticket created successfully", {"ticket_id": result["id"]})
                    else:
                        self.log_result(f"IT Ticket Creation - {category}", False, "No ticket ID returned")
                else:
                    self.log_result(f"IT Ticket Creation - {category}", False, 
                                  f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result(f"IT Ticket Creation - {category}", False, f"Exception: {str(e)}")
    
    def test_it_tickets_list_api(self):
        """Test GET /api/employee/it-tickets"""
        print("\n=== Testing IT Tickets List API ===")
        
        if not self.employee_token:
            self.log_result("IT Tickets List API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        try:
            response = requests.get(f"{API_BASE}/employee/it-tickets", headers=headers)
            
            if response.status_code == 200:
                tickets = response.json()
                self.log_result("IT Tickets List API", True, 
                              f"Retrieved {len(tickets)} IT tickets", 
                              {"tickets_count": len(tickets)})
            else:
                self.log_result("IT Tickets List API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("IT Tickets List API", False, f"Exception: {str(e)}")
    
    def test_admin_leave_settings_get_api(self):
        """Test GET /api/admin/leave-settings"""
        print("\n=== Testing Admin Leave Settings GET API ===")
        
        if not self.admin_token:
            self.log_result("Admin Leave Settings GET API", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            response = requests.get(f"{API_BASE}/admin/leave-settings", headers=headers)
            
            if response.status_code == 200:
                settings = response.json()
                
                # Validate response structure
                required_keys = ["casual_leave_quarterly", "sick_leave_quarterly", "leave_without_pay_quarterly"]
                missing_keys = [key for key in required_keys if key not in settings]
                
                if missing_keys:
                    self.log_result("Admin Leave Settings GET API", False, f"Missing keys: {missing_keys}")
                else:
                    self.log_result("Admin Leave Settings GET API", True, "Leave settings retrieved successfully", 
                                  {"settings": settings})
            else:
                self.log_result("Admin Leave Settings GET API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Admin Leave Settings GET API", False, f"Exception: {str(e)}")
    
    def test_admin_leave_settings_put_api(self):
        """Test PUT /api/admin/leave-settings"""
        print("\n=== Testing Admin Leave Settings PUT API ===")
        
        if not self.admin_token:
            self.log_result("Admin Leave Settings PUT API", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test updating leave settings
        new_settings = {
            "casual_leave_quarterly": 3,
            "sick_leave_quarterly": 3,
            "leave_without_pay_quarterly": 7
        }
        
        try:
            response = requests.put(f"{API_BASE}/admin/leave-settings", json=new_settings, headers=headers)
            
            if response.status_code == 200:
                self.log_result("Admin Leave Settings PUT API", True, "Leave settings updated successfully")
                
                # Verify the update by getting settings again
                get_response = requests.get(f"{API_BASE}/admin/leave-settings", headers=headers)
                if get_response.status_code == 200:
                    updated_settings = get_response.json()
                    if (updated_settings["casual_leave_quarterly"] == 3 and 
                        updated_settings["sick_leave_quarterly"] == 3 and 
                        updated_settings["leave_without_pay_quarterly"] == 7):
                        self.log_result("Admin Leave Settings PUT API - Verification", True, 
                                      "Settings update verified successfully")
                    else:
                        self.log_result("Admin Leave Settings PUT API - Verification", False, 
                                      "Settings were not updated correctly")
                else:
                    self.log_result("Admin Leave Settings PUT API - Verification", False, 
                                  "Could not verify settings update")
            else:
                self.log_result("Admin Leave Settings PUT API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Admin Leave Settings PUT API", False, f"Exception: {str(e)}")
    
    def test_logo_upload_api(self):
        """Test POST /api/admin/upload-logo-base64"""
        print("\n=== Testing Logo Upload API ===")
        
        if not self.admin_token:
            self.log_result("Logo Upload API", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test valid PNG base64 upload
        # Small 1x1 PNG image in base64
        valid_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        valid_data_url = f"data:image/png;base64,{valid_png_base64}"
        
        logo_data = {
            "logo_base64": valid_data_url
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=logo_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if "logo_url" in result and result["logo_url"]:
                    self.log_result("Logo Upload API - Valid PNG", True, "Logo uploaded successfully", 
                                  {"logo_url_length": len(result["logo_url"])})
                else:
                    self.log_result("Logo Upload API - Valid PNG", False, "No logo URL returned")
            else:
                self.log_result("Logo Upload API - Valid PNG", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Logo Upload API - Valid PNG", False, f"Exception: {str(e)}")
        
        # Test valid JPEG base64 upload
        # Small JPEG image in base64
        valid_jpeg_base64 = "/9j/4AAQSkZJRgABAQEAYABgAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/2wBDAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAARCAABAAEDASIAAhEBAxEB/8QAFQABAQAAAAAAAAAAAAAAAAAAAAv/xAAUEAEAAAAAAAAAAAAAAAAAAAAA/8QAFQEBAQAAAAAAAAAAAAAAAAAAAAX/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwA/wA=="
        valid_jpeg_data_url = f"data:image/jpeg;base64,{valid_jpeg_base64}"
        
        jpeg_logo_data = {
            "logo_base64": valid_jpeg_data_url
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=jpeg_logo_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if "logo_url" in result and result["logo_url"]:
                    self.log_result("Logo Upload API - Valid JPEG", True, "JPEG logo uploaded successfully")
                else:
                    self.log_result("Logo Upload API - Valid JPEG", False, "No logo URL returned")
            else:
                self.log_result("Logo Upload API - Valid JPEG", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Logo Upload API - Valid JPEG", False, f"Exception: {str(e)}")
        
        # Test invalid base64 data
        invalid_logo_data = {
            "logo_base64": "invalid_base64_data"
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=invalid_logo_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Logo Upload API - Invalid Base64", True, "Correctly rejected invalid base64 data")
            else:
                self.log_result("Logo Upload API - Invalid Base64", False, 
                              f"Should return 400 for invalid base64, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Logo Upload API - Invalid Base64", False, f"Exception: {str(e)}")
        
        # Test missing logo data
        empty_logo_data = {}
        
        try:
            response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=empty_logo_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Logo Upload API - Missing Data", True, "Correctly rejected missing logo data")
            else:
                self.log_result("Logo Upload API - Missing Data", False, 
                              f"Should return 400 for missing data, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Logo Upload API - Missing Data", False, f"Exception: {str(e)}")
        
        # Test oversized file (simulate by creating large base64 string)
        # Create a base64 string that would exceed 5MB when decoded
        large_base64 = "A" * (7 * 1024 * 1024)  # 7MB of 'A' characters
        large_logo_data = {
            "logo_base64": f"data:image/png;base64,{large_base64}"
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=large_logo_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Logo Upload API - File Size Limit", True, "Correctly rejected oversized file")
            else:
                self.log_result("Logo Upload API - File Size Limit", False, 
                              f"Should return 400 for oversized file, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Logo Upload API - File Size Limit", False, f"Exception: {str(e)}")
    
    def test_logo_remove_api(self):
        """Test DELETE /api/admin/remove-logo"""
        print("\n=== Testing Logo Remove API ===")
        
        if not self.admin_token:
            self.log_result("Logo Remove API", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First upload a logo to ensure there's something to remove
        valid_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        valid_data_url = f"data:image/png;base64,{valid_png_base64}"
        
        logo_data = {
            "logo_base64": valid_data_url
        }
        
        try:
            # Upload logo first
            upload_response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=logo_data, headers=headers)
            
            if upload_response.status_code == 200:
                # Now test removing the logo
                remove_response = requests.delete(f"{API_BASE}/admin/remove-logo", headers=headers)
                
                if remove_response.status_code == 200:
                    self.log_result("Logo Remove API", True, "Logo removed successfully")
                    
                    # Verify logo was removed by checking organization settings
                    settings_response = requests.get(f"{API_BASE}/admin/organization-settings", headers=headers)
                    if settings_response.status_code == 200:
                        settings = settings_response.json()
                        if settings.get("company_logo") == "":
                            self.log_result("Logo Remove API - Verification", True, "Logo removal verified in organization settings")
                        else:
                            self.log_result("Logo Remove API - Verification", False, "Logo still present in organization settings")
                    else:
                        self.log_result("Logo Remove API - Verification", False, "Could not verify logo removal")
                else:
                    self.log_result("Logo Remove API", False, f"HTTP {remove_response.status_code}: {remove_response.text}")
            else:
                # Test removing when no logo exists
                remove_response = requests.delete(f"{API_BASE}/admin/remove-logo", headers=headers)
                
                if remove_response.status_code in [200, 404]:
                    self.log_result("Logo Remove API - No Logo", True, "Handled removal when no logo exists")
                else:
                    self.log_result("Logo Remove API - No Logo", False, 
                                  f"Unexpected response when no logo exists: {remove_response.status_code}")
                
        except Exception as e:
            self.log_result("Logo Remove API", False, f"Exception: {str(e)}")
    
    def test_organization_settings_logo_integration(self):
        """Test GET /api/admin/organization-settings returns logo URL"""
        print("\n=== Testing Organization Settings Logo Integration ===")
        
        if not self.admin_token:
            self.log_result("Organization Settings Logo Integration", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # First upload a logo
        valid_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        valid_data_url = f"data:image/png;base64,{valid_png_base64}"
        
        logo_data = {
            "logo_base64": valid_data_url
        }
        
        try:
            # Upload logo
            upload_response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=logo_data, headers=headers)
            
            if upload_response.status_code == 200:
                # Get organization settings and verify logo is present
                settings_response = requests.get(f"{API_BASE}/admin/organization-settings", headers=headers)
                
                if settings_response.status_code == 200:
                    settings = settings_response.json()
                    
                    if "company_logo" in settings and settings["company_logo"]:
                        if settings["company_logo"].startswith("data:image"):
                            self.log_result("Organization Settings Logo Integration", True, 
                                          "Logo URL correctly returned in organization settings", 
                                          {"logo_url_prefix": settings["company_logo"][:50] + "..."})
                        else:
                            self.log_result("Organization Settings Logo Integration", False, 
                                          "Logo URL format is incorrect")
                    else:
                        self.log_result("Organization Settings Logo Integration", False, 
                                      "Logo not found in organization settings")
                else:
                    self.log_result("Organization Settings Logo Integration", False, 
                                  f"HTTP {settings_response.status_code}: {settings_response.text}")
            else:
                self.log_result("Organization Settings Logo Integration", False, 
                              "Could not upload logo for integration test")
                
        except Exception as e:
            self.log_result("Organization Settings Logo Integration", False, f"Exception: {str(e)}")
    
    def test_logo_upload_authentication(self):
        """Test logo upload endpoints with different authentication scenarios"""
        print("\n=== Testing Logo Upload Authentication ===")
        
        # Test logo upload without authentication
        valid_png_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        valid_data_url = f"data:image/png;base64,{valid_png_base64}"
        
        logo_data = {
            "logo_base64": valid_data_url
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=logo_data)
            if response.status_code == 401:
                self.log_result("Logo Upload Authentication - No Token", True, "Correctly rejected unauthenticated request")
            else:
                self.log_result("Logo Upload Authentication - No Token", False, 
                              f"Should return 401 but got {response.status_code}")
        except Exception as e:
            self.log_result("Logo Upload Authentication - No Token", False, f"Exception: {str(e)}")
        
        # Test logo upload with employee token (should fail)
        if self.employee_token:
            headers = {"Authorization": f"Bearer {self.employee_token}"}
            try:
                response = requests.post(f"{API_BASE}/admin/upload-logo-base64", json=logo_data, headers=headers)
                if response.status_code == 403:
                    self.log_result("Logo Upload Authentication - Employee Token", True, "Correctly rejected employee accessing admin endpoint")
                else:
                    self.log_result("Logo Upload Authentication - Employee Token", False, 
                                  f"Should return 403 but got {response.status_code}")
            except Exception as e:
                self.log_result("Logo Upload Authentication - Employee Token", False, f"Exception: {str(e)}")
        
        # Test logo remove without authentication
        try:
            response = requests.delete(f"{API_BASE}/admin/remove-logo")
            if response.status_code == 401:
                self.log_result("Logo Remove Authentication - No Token", True, "Correctly rejected unauthenticated request")
            else:
                self.log_result("Logo Remove Authentication - No Token", False, 
                              f"Should return 401 but got {response.status_code}")
        except Exception as e:
            self.log_result("Logo Remove Authentication - No Token", False, f"Exception: {str(e)}")
        
        # Test logo remove with employee token (should fail)
        if self.employee_token:
            headers = {"Authorization": f"Bearer {self.employee_token}"}
            try:
                response = requests.delete(f"{API_BASE}/admin/remove-logo", headers=headers)
                if response.status_code == 403:
                    self.log_result("Logo Remove Authentication - Employee Token", True, "Correctly rejected employee accessing admin endpoint")
                else:
                    self.log_result("Logo Remove Authentication - Employee Token", False, 
                                  f"Should return 403 but got {response.status_code}")
            except Exception as e:
                self.log_result("Logo Remove Authentication - Employee Token", False, f"Exception: {str(e)}")

    def test_authentication_scenarios(self):
        """Test authentication scenarios"""
        print("\n=== Testing Authentication Scenarios ===")
        
        # Test employee endpoints without token
        try:
            response = requests.get(f"{API_BASE}/employee/projects")
            if response.status_code == 401:
                self.log_result("Authentication - Employee Endpoint", True, "Correctly rejected unauthenticated request")
            else:
                self.log_result("Authentication - Employee Endpoint", False, 
                              f"Should return 401 but got {response.status_code}")
        except Exception as e:
            self.log_result("Authentication - Employee Endpoint", False, f"Exception: {str(e)}")
        
        # Test admin endpoints without token
        try:
            response = requests.get(f"{API_BASE}/admin/leave-settings")
            if response.status_code == 401:
                self.log_result("Authentication - Admin Endpoint", True, "Correctly rejected unauthenticated request")
            else:
                self.log_result("Authentication - Admin Endpoint", False, 
                              f"Should return 401 but got {response.status_code}")
        except Exception as e:
            self.log_result("Authentication - Admin Endpoint", False, f"Exception: {str(e)}")
        
        # Test admin endpoint with employee token
        if self.employee_token:
            headers = {"Authorization": f"Bearer {self.employee_token}"}
            try:
                response = requests.get(f"{API_BASE}/admin/leave-settings", headers=headers)
                if response.status_code == 403:
                    self.log_result("Authentication - Role Check", True, "Correctly rejected employee accessing admin endpoint")
                else:
                    self.log_result("Authentication - Role Check", False, 
                                  f"Should return 403 but got {response.status_code}")
            except Exception as e:
                self.log_result("Authentication - Role Check", False, f"Exception: {str(e)}")
    
    def setup_manager_test_data(self):
        """Setup test data for manager functionality"""
        print("\n=== Setting up Manager Test Data ===")
        
        if not self.admin_token:
            self.log_result("Manager Setup", False, "No admin token available")
            return False
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        try:
            # Create a test department
            dept_data = {
                "name": f"Test Department {uuid.uuid4().hex[:8]}",
                "description": "Test department for manager testing"
            }
            
            dept_response = requests.post(f"{API_BASE}/admin/create-department", json=dept_data, headers=headers)
            if dept_response.status_code != 200:
                self.log_result("Manager Setup - Department", False, f"Failed to create department: {dept_response.text}")
                return False
            
            dept_id = dept_response.json()["department_id"]
            
            # Create a manager assignment for the employee
            manager_data = {
                "employee_id": self.employee_id,
                "department_id": dept_id
            }
            
            manager_response = requests.post(f"{API_BASE}/admin/create-manager", json=manager_data, headers=headers)
            if manager_response.status_code == 200:
                self.manager_id = manager_response.json()["manager_id"]
                self.log_result("Manager Setup", True, "Manager test data created successfully")
                return True
            else:
                self.log_result("Manager Setup", False, f"Failed to create manager: {manager_response.text}")
                return False
                
        except Exception as e:
            self.log_result("Manager Setup", False, f"Exception: {str(e)}")
            return False
    
    def test_manager_status_api(self):
        """Test GET /api/employee/manager-status"""
        print("\n=== Testing Manager Status API ===")
        
        if not self.employee_token:
            self.log_result("Manager Status API", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        # Test manager status check without manager assignment
        try:
            response = requests.get(f"{API_BASE}/employee/manager-status", headers=headers)
            
            if response.status_code == 200:
                status = response.json()
                
                if "is_manager" in status:
                    if status["is_manager"] == False:
                        self.log_result("Manager Status API - Regular Employee", True, 
                                      "Correctly identified regular employee as non-manager")
                    else:
                        # If user is already a manager, test the manager response structure
                        required_keys = ["is_manager", "department_id", "department_name", "manager_assignment_id"]
                        missing_keys = [key for key in required_keys if key not in status]
                        
                        if missing_keys:
                            self.log_result("Manager Status API - Manager Response", False, 
                                          f"Missing keys in manager response: {missing_keys}")
                        else:
                            self.log_result("Manager Status API - Manager Response", True, 
                                          f"Manager status returned correctly with department: {status['department_name']}")
                else:
                    self.log_result("Manager Status API", False, "Missing 'is_manager' field in response")
            else:
                self.log_result("Manager Status API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Manager Status API", False, f"Exception: {str(e)}")
        
        # Setup manager data and test manager status
        if self.setup_manager_test_data():
            try:
                response = requests.get(f"{API_BASE}/employee/manager-status", headers=headers)
                
                if response.status_code == 200:
                    status = response.json()
                    
                    if status.get("is_manager") == True:
                        required_keys = ["department_id", "department_name", "manager_assignment_id"]
                        missing_keys = [key for key in required_keys if key not in status]
                        
                        if missing_keys:
                            self.log_result("Manager Status API - After Assignment", False, 
                                          f"Missing keys after manager assignment: {missing_keys}")
                        else:
                            self.log_result("Manager Status API - After Assignment", True, 
                                          f"Manager status correctly updated after assignment")
                    else:
                        self.log_result("Manager Status API - After Assignment", False, 
                                      "User should be manager after assignment")
                else:
                    self.log_result("Manager Status API - After Assignment", False, 
                                  f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result("Manager Status API - After Assignment", False, f"Exception: {str(e)}")
    
    def test_notification_apis(self):
        """Test notification-related APIs"""
        print("\n=== Testing Notification APIs ===")
        
        if not self.employee_token:
            self.log_result("Notification APIs", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        # Test GET /api/employee/notifications
        try:
            response = requests.get(f"{API_BASE}/employee/notifications", headers=headers)
            
            if response.status_code == 200:
                notifications = response.json()
                
                if isinstance(notifications, list):
                    self.log_result("Get Notifications API", True, 
                                  f"Retrieved {len(notifications)} notifications")
                    
                    # Validate notification structure if any exist
                    if notifications:
                        notif = notifications[0]
                        required_keys = ["id", "title", "message", "type", "status", "created_at"]
                        missing_keys = [key for key in required_keys if key not in notif]
                        
                        if missing_keys:
                            self.log_result("Get Notifications API - Structure", False, 
                                          f"Missing keys in notification: {missing_keys}")
                        else:
                            self.log_result("Get Notifications API - Structure", True, 
                                          "Notification structure is correct")
                else:
                    self.log_result("Get Notifications API", False, "Response is not a list")
            else:
                self.log_result("Get Notifications API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Get Notifications API", False, f"Exception: {str(e)}")
        
        # Test GET /api/employee/notifications/unread-count
        try:
            response = requests.get(f"{API_BASE}/employee/notifications/unread-count", headers=headers)
            
            if response.status_code == 200:
                count_data = response.json()
                
                if "unread_count" in count_data and isinstance(count_data["unread_count"], int):
                    self.log_result("Unread Count API", True, 
                                  f"Unread count: {count_data['unread_count']}")
                else:
                    self.log_result("Unread Count API", False, "Invalid unread count response structure")
            else:
                self.log_result("Unread Count API", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Unread Count API", False, f"Exception: {str(e)}")
        
        # Test PUT /api/employee/notifications/{id}/read with dummy ID
        dummy_notification_id = str(uuid.uuid4())
        try:
            response = requests.put(f"{API_BASE}/employee/notifications/{dummy_notification_id}/read", headers=headers)
            
            if response.status_code == 404:
                self.log_result("Mark Notification Read API", True, "Correctly handled non-existent notification")
            else:
                self.log_result("Mark Notification Read API", False, 
                              f"Should return 404 for non-existent notification, got {response.status_code}")
                
        except Exception as e:
            self.log_result("Mark Notification Read API", False, f"Exception: {str(e)}")
    
    def test_leave_approval_notification_workflow(self):
        """Test the complete leave approval workflow with notifications"""
        print("\n=== Testing Leave Approval Notification Workflow ===")
        
        if not self.employee_token:
            self.log_result("Leave Approval Workflow", False, "No employee token available")
            return
            
        headers = {"Authorization": f"Bearer {self.employee_token}"}
        
        # Step 1: Apply for leave
        leave_data = {
            "leave_type": "Casual Leave",
            "start_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=10)).strftime("%Y-%m-%d"),
            "reason": "Testing notification workflow",
            "days_count": 1.0
        }
        
        leave_id = None
        try:
            response = requests.post(f"{API_BASE}/employee/apply-leave", json=leave_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                leave_id = result.get("id")
                self.log_result("Leave Approval Workflow - Apply", True, "Leave application submitted")
            else:
                self.log_result("Leave Approval Workflow - Apply", False, 
                              f"Failed to apply for leave: {response.text}")
                return
                
        except Exception as e:
            self.log_result("Leave Approval Workflow - Apply", False, f"Exception: {str(e)}")
            return
        
        # Step 2: Check if user can act as manager (if manager setup was successful)
        if self.manager_id and leave_id:
            # Get initial unread count
            initial_count = 0
            try:
                count_response = requests.get(f"{API_BASE}/employee/notifications/unread-count", headers=headers)
                if count_response.status_code == 200:
                    initial_count = count_response.json().get("unread_count", 0)
            except:
                pass
            
            # Step 3: Try to approve the leave as manager
            approval_data = {
                "status": "approved",
                "manager_reason": "Approved for testing notification workflow"
            }
            
            try:
                # First check if there are any pending requests for this manager
                manager_requests_response = requests.get(f"{API_BASE}/manager/leave-requests", headers=headers)
                
                if manager_requests_response.status_code == 200:
                    pending_requests = manager_requests_response.json()
                    
                    # Find our leave request in the pending list
                    our_request = None
                    for req in pending_requests:
                        if req.get("id") == leave_id:
                            our_request = req
                            break
                    
                    if our_request:
                        # Approve the leave request
                        approve_response = requests.put(f"{API_BASE}/manager/leave-requests/{leave_id}", 
                                                      json=approval_data, headers=headers)
                        
                        if approve_response.status_code == 200:
                            self.log_result("Leave Approval Workflow - Approve", True, "Leave request approved")
                            
                            # Step 4: Check if notification was created
                            import time
                            time.sleep(1)  # Brief delay to ensure notification is created
                            
                            try:
                                count_response = requests.get(f"{API_BASE}/employee/notifications/unread-count", headers=headers)
                                if count_response.status_code == 200:
                                    new_count = count_response.json().get("unread_count", 0)
                                    
                                    if new_count > initial_count:
                                        self.log_result("Leave Approval Workflow - Notification Created", True, 
                                                      f"Notification created (unread count increased from {initial_count} to {new_count})")
                                        
                                        # Step 5: Get notifications and verify content
                                        notif_response = requests.get(f"{API_BASE}/employee/notifications", headers=headers)
                                        if notif_response.status_code == 200:
                                            notifications = notif_response.json()
                                            
                                            # Look for our leave approval notification
                                            approval_notif = None
                                            for notif in notifications:
                                                if ("approved" in notif.get("message", "").lower() and 
                                                    leave_data["start_date"] in notif.get("message", "")):
                                                    approval_notif = notif
                                                    break
                                            
                                            if approval_notif:
                                                self.log_result("Leave Approval Workflow - Notification Content", True, 
                                                              f"Notification contains correct approval message")
                                                
                                                # Step 6: Test marking notification as read
                                                read_response = requests.put(
                                                    f"{API_BASE}/employee/notifications/{approval_notif['id']}/read", 
                                                    headers=headers)
                                                
                                                if read_response.status_code == 200:
                                                    self.log_result("Leave Approval Workflow - Mark Read", True, 
                                                                  "Notification marked as read successfully")
                                                    
                                                    # Verify unread count decreased
                                                    final_count_response = requests.get(f"{API_BASE}/employee/notifications/unread-count", headers=headers)
                                                    if final_count_response.status_code == 200:
                                                        final_count = final_count_response.json().get("unread_count", 0)
                                                        if final_count < new_count:
                                                            self.log_result("Leave Approval Workflow - Count Update", True, 
                                                                          f"Unread count correctly decreased to {final_count}")
                                                        else:
                                                            self.log_result("Leave Approval Workflow - Count Update", False, 
                                                                          "Unread count did not decrease after marking as read")
                                                else:
                                                    self.log_result("Leave Approval Workflow - Mark Read", False, 
                                                                  f"Failed to mark notification as read: {read_response.text}")
                                            else:
                                                self.log_result("Leave Approval Workflow - Notification Content", False, 
                                                              "Could not find approval notification in list")
                                    else:
                                        self.log_result("Leave Approval Workflow - Notification Created", False, 
                                                      f"Unread count did not increase (was {initial_count}, still {new_count})")
                                        
                            except Exception as e:
                                self.log_result("Leave Approval Workflow - Notification Check", False, f"Exception: {str(e)}")
                        else:
                            self.log_result("Leave Approval Workflow - Approve", False, 
                                          f"Failed to approve leave: {approve_response.text}")
                    else:
                        self.log_result("Leave Approval Workflow - Find Request", False, 
                                      "Could not find submitted leave request in manager's pending list")
                else:
                    self.log_result("Leave Approval Workflow - Manager Requests", False, 
                                  f"Failed to get manager requests: {manager_requests_response.text}")
                    
            except Exception as e:
                self.log_result("Leave Approval Workflow - Manager Actions", False, f"Exception: {str(e)}")
        else:
            self.log_result("Leave Approval Workflow - Manager Setup", False, 
                          "Manager setup not completed, skipping approval workflow test")
    
    def test_employee_department_assignment_apis(self):
        """Test employee-department assignment system APIs"""
        print("\n=== Testing Employee-Department Assignment APIs ===")
        
        if not self.admin_token:
            self.log_result("Employee-Department Assignment APIs", False, "No admin token available")
            return
            
        headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Test 1: Get current assignments
        try:
            response = requests.get(f"{API_BASE}/admin/employee-department-assignments", headers=headers)
            
            if response.status_code == 200:
                assignments = response.json()
                self.log_result("Get Employee-Department Assignments", True, 
                              f"Retrieved {len(assignments)} assignments")
                
                # Check if our test employee is auto-assigned
                our_assignment = None
                for assignment in assignments:
                    if assignment.get("employee_id") == self.employee_id:
                        our_assignment = assignment
                        break
                
                if our_assignment:
                    self.log_result("Auto-Assignment Check", True, 
                                  f"Employee auto-assigned to department: {our_assignment['department_name']}")
                else:
                    self.log_result("Auto-Assignment Check", False, 
                                  "Employee not found in department assignments")
            else:
                self.log_result("Get Employee-Department Assignments", False, 
                              f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Get Employee-Department Assignments", False, f"Exception: {str(e)}")
        
        # Test 2: Create a test department
        test_dept_id = None
        dept_data = {
            "name": f"Test Department {uuid.uuid4().hex[:8]}",
            "description": "Test department for assignment testing"
        }
        
        try:
            response = requests.post(f"{API_BASE}/admin/create-department", json=dept_data, headers=headers)
            
            if response.status_code == 200:
                test_dept_id = response.json()["department_id"]
                self.log_result("Create Test Department", True, "Test department created successfully")
            else:
                self.log_result("Create Test Department", False, f"HTTP {response.status_code}: {response.text}")
                
        except Exception as e:
            self.log_result("Create Test Department", False, f"Exception: {str(e)}")
        
        # Test 3: Assign employee to department
        if test_dept_id:
            assignment_data = {
                "employee_id": self.employee_id,
                "department_id": test_dept_id
            }
            
            try:
                response = requests.post(f"{API_BASE}/admin/assign-employee-department", 
                                       json=assignment_data, headers=headers)
                
                if response.status_code == 200:
                    self.log_result("Assign Employee to Department", True, "Employee assigned successfully")
                    
                    # Verify assignment
                    verify_response = requests.get(f"{API_BASE}/admin/employee-department-assignments", headers=headers)
                    if verify_response.status_code == 200:
                        assignments = verify_response.json()
                        our_assignment = None
                        for assignment in assignments:
                            if (assignment.get("employee_id") == self.employee_id and 
                                assignment.get("department_id") == test_dept_id):
                                our_assignment = assignment
                                break
                        
                        if our_assignment:
                            self.log_result("Verify Assignment", True, 
                                          f"Assignment verified: {our_assignment['department_name']}")
                        else:
                            self.log_result("Verify Assignment", False, "Assignment not found after creation")
                else:
                    self.log_result("Assign Employee to Department", False, 
                                  f"HTTP {response.status_code}: {response.text}")
                    
            except Exception as e:
                self.log_result("Assign Employee to Department", False, f"Exception: {str(e)}")
        
        # Test 4: Bulk assignment (create another employee first)
        if test_dept_id:
            # Create another test employee
            employee2_data = {
                "name": "Jane Employee",
                "email": f"employee2_{uuid.uuid4().hex[:8]}@test.com",
                "phone": f"555{uuid.uuid4().hex[:7]}",
                "password": "testpass123"
            }
            
            try:
                emp2_response = requests.post(f"{API_BASE}/auth/register", json=employee2_data)
                if emp2_response.status_code == 200:
                    # Get employee2 ID
                    emp2_token = emp2_response.json()["access_token"]
                    emp2_headers = {"Authorization": f"Bearer {emp2_token}"}
                    me_response = requests.get(f"{API_BASE}/auth/me", headers=emp2_headers)
                    
                    if me_response.status_code == 200:
                        employee2_id = me_response.json()["id"]
                        
                        # Test bulk assignment
                        bulk_data = {
                            "employee_ids": [self.employee_id, employee2_id],
                            "department_id": test_dept_id
                        }
                        
                        bulk_response = requests.post(f"{API_BASE}/admin/bulk-assign-employees", 
                                                    json=bulk_data, headers=headers)
                        
                        if bulk_response.status_code == 200:
                            result = bulk_response.json()
                            self.log_result("Bulk Assign Employees", True, result["message"])
                        else:
                            self.log_result("Bulk Assign Employees", False, 
                                          f"HTTP {bulk_response.status_code}: {bulk_response.text}")
                    else:
                        self.log_result("Bulk Assign Employees", False, "Could not get employee2 ID")
                else:
                    self.log_result("Bulk Assign Employees", False, "Could not create employee2")
                    
            except Exception as e:
                self.log_result("Bulk Assign Employees", False, f"Exception: {str(e)}")

    def test_fixed_leave_application_workflow(self):
        """Test the FIXED leave application workflow with proper manager assignment"""
        print("\n=== Testing FIXED Leave Application Workflow ===")
        
        if not self.employee_token or not self.admin_token:
            self.log_result("Fixed Leave Workflow", False, "Missing required tokens")
            return
            
        employee_headers = {"Authorization": f"Bearer {self.employee_token}"}
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Step 1: Ensure employee has department assignment (should be auto-assigned)
        try:
            assignments_response = requests.get(f"{API_BASE}/admin/employee-department-assignments", headers=admin_headers)
            
            if assignments_response.status_code == 200:
                assignments = assignments_response.json()
                employee_assignment = None
                
                for assignment in assignments:
                    if assignment.get("employee_id") == self.employee_id:
                        employee_assignment = assignment
                        break
                
                if employee_assignment:
                    self.log_result("Employee Department Assignment Check", True, 
                                  f"Employee assigned to: {employee_assignment['department_name']}")
                    department_id = employee_assignment["department_id"]
                else:
                    self.log_result("Employee Department Assignment Check", False, 
                                  "Employee not assigned to any department")
                    return
            else:
                self.log_result("Employee Department Assignment Check", False, 
                              f"Could not fetch assignments: {assignments_response.text}")
                return
                
        except Exception as e:
            self.log_result("Employee Department Assignment Check", False, f"Exception: {str(e)}")
            return
        
        # Step 2: Ensure there's a manager for the department
        try:
            managers_response = requests.get(f"{API_BASE}/admin/managers", headers=admin_headers)
            
            if managers_response.status_code == 200:
                managers = managers_response.json()
                department_manager = None
                
                for manager in managers:
                    if manager.get("department_id") == department_id:
                        department_manager = manager
                        break
                
                if department_manager:
                    self.log_result("Department Manager Check", True, 
                                  f"Manager found: {department_manager['employee_name']}")
                    manager_employee_id = department_manager["employee_id"]
                else:
                    self.log_result("Department Manager Check", False, 
                                  "No manager assigned to employee's department")
                    return
            else:
                self.log_result("Department Manager Check", False, 
                              f"Could not fetch managers: {managers_response.text}")
                return
                
        except Exception as e:
            self.log_result("Department Manager Check", False, f"Exception: {str(e)}")
            return
        
        # Step 3: Apply for leave (should now properly assign manager_id)
        leave_data = {
            "leave_type": "Casual Leave",
            "start_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d"),
            "reason": "Testing fixed manager assignment workflow",
            "days_count": 1.0
        }
        
        leave_id = None
        try:
            response = requests.post(f"{API_BASE}/employee/apply-leave", json=leave_data, headers=employee_headers)
            
            if response.status_code == 200:
                result = response.json()
                leave_id = result.get("id")
                self.log_result("Apply Leave with Manager Assignment", True, 
                              "Leave application submitted successfully")
            else:
                self.log_result("Apply Leave with Manager Assignment", False, 
                              f"HTTP {response.status_code}: {response.text}")
                return
                
        except Exception as e:
            self.log_result("Apply Leave with Manager Assignment", False, f"Exception: {str(e)}")
            return
        
        # Step 4: Check if manager can see the leave request
        if leave_id:
            # Login as the manager to check if they can see the request
            try:
                # Get manager's login credentials (we'll use admin token to get manager details)
                manager_user_response = requests.get(f"{API_BASE}/admin/employees", headers=admin_headers)
                
                if manager_user_response.status_code == 200:
                    employees = manager_user_response.json()
                    manager_user = None
                    
                    for emp in employees:
                        if emp.get("id") == manager_employee_id:
                            manager_user = emp
                            break
                    
                    if manager_user:
                        # Try to login as manager (we'll create a test manager token)
                        # For testing purposes, we'll use the admin token to check manager endpoints
                        
                        # Check manager leave requests endpoint
                        manager_requests_response = requests.get(f"{API_BASE}/manager/leave-requests", headers=admin_headers)
                        
                        if manager_requests_response.status_code == 200:
                            pending_requests = manager_requests_response.json()
                            
                            # Look for our leave request
                            our_request = None
                            for req in pending_requests:
                                if req.get("id") == leave_id:
                                    our_request = req
                                    break
                            
                            if our_request:
                                self.log_result("Manager Can See Leave Request", True, 
                                              f"Leave request visible to manager: {our_request['employee_name']}")
                                
                                # Step 5: Test approval workflow
                                approval_data = {
                                    "status": "approved",
                                    "manager_reason": "Approved for testing fixed workflow"
                                }
                                
                                approve_response = requests.put(f"{API_BASE}/manager/leave-requests/{leave_id}", 
                                                              json=approval_data, headers=admin_headers)
                                
                                if approve_response.status_code == 200:
                                    self.log_result("Manager Approve Leave Request", True, 
                                                  "Leave request approved successfully")
                                    
                                    # Step 6: Check if notification was created for employee
                                    import time
                                    time.sleep(1)  # Brief delay for notification creation
                                    
                                    notif_response = requests.get(f"{API_BASE}/employee/notifications", headers=employee_headers)
                                    if notif_response.status_code == 200:
                                        notifications = notif_response.json()
                                        
                                        approval_notification = None
                                        for notif in notifications:
                                            if ("approved" in notif.get("message", "").lower() and 
                                                leave_data["start_date"] in notif.get("message", "")):
                                                approval_notification = notif
                                                break
                                        
                                        if approval_notification:
                                            self.log_result("Leave Approval Notification Created", True, 
                                                          "Notification created for approved leave")
                                        else:
                                            self.log_result("Leave Approval Notification Created", False, 
                                                          "No approval notification found")
                                    else:
                                        self.log_result("Leave Approval Notification Created", False, 
                                                      "Could not fetch notifications")
                                else:
                                    self.log_result("Manager Approve Leave Request", False, 
                                                  f"HTTP {approve_response.status_code}: {approve_response.text}")
                            else:
                                self.log_result("Manager Can See Leave Request", False, 
                                              "Leave request not visible to manager - CRITICAL ISSUE NOT FIXED")
                        else:
                            self.log_result("Manager Can See Leave Request", False, 
                                          f"Could not fetch manager requests: {manager_requests_response.text}")
                    else:
                        self.log_result("Manager Can See Leave Request", False, "Could not find manager user details")
                else:
                    self.log_result("Manager Can See Leave Request", False, "Could not fetch employee list")
                    
            except Exception as e:
                self.log_result("Manager Can See Leave Request", False, f"Exception: {str(e)}")

    def test_end_to_end_manager_workflow(self):
        """Test complete end-to-end manager workflow"""
        print("\n=== Testing End-to-End Manager Workflow ===")
        
        if not self.admin_token:
            self.log_result("End-to-End Manager Workflow", False, "No admin token available")
            return
            
        admin_headers = {"Authorization": f"Bearer {self.admin_token}"}
        
        # Step 1: Register new employee (should auto-assign to department)
        new_employee_data = {
            "name": "Test Manager Workflow Employee",
            "email": f"workflow_emp_{uuid.uuid4().hex[:8]}@test.com",
            "phone": f"555{uuid.uuid4().hex[:7]}",
            "password": "testpass123"
        }
        
        new_employee_token = None
        new_employee_id = None
        
        try:
            response = requests.post(f"{API_BASE}/auth/register", json=new_employee_data)
            if response.status_code == 200:
                new_employee_token = response.json()["access_token"]
                
                # Get employee ID
                headers = {"Authorization": f"Bearer {new_employee_token}"}
                me_response = requests.get(f"{API_BASE}/auth/me", headers=headers)
                if me_response.status_code == 200:
                    new_employee_id = me_response.json()["id"]
                    self.log_result("E2E - Register New Employee", True, "New employee registered successfully")
                else:
                    self.log_result("E2E - Register New Employee", False, "Could not get employee ID")
                    return
            else:
                self.log_result("E2E - Register New Employee", False, f"HTTP {response.status_code}: {response.text}")
                return
                
        except Exception as e:
            self.log_result("E2E - Register New Employee", False, f"Exception: {str(e)}")
            return
        
        # Step 2: Verify auto-assignment to department
        try:
            assignments_response = requests.get(f"{API_BASE}/admin/employee-department-assignments", headers=admin_headers)
            
            if assignments_response.status_code == 200:
                assignments = assignments_response.json()
                employee_assignment = None
                
                for assignment in assignments:
                    if assignment.get("employee_id") == new_employee_id:
                        employee_assignment = assignment
                        break
                
                if employee_assignment:
                    self.log_result("E2E - Auto-Assignment Check", True, 
                                  f"New employee auto-assigned to: {employee_assignment['department_name']}")
                else:
                    self.log_result("E2E - Auto-Assignment Check", False, 
                                  "New employee not auto-assigned to department")
                    return
            else:
                self.log_result("E2E - Auto-Assignment Check", False, 
                              f"Could not fetch assignments: {assignments_response.text}")
                return
                
        except Exception as e:
            self.log_result("E2E - Auto-Assignment Check", False, f"Exception: {str(e)}")
            return
        
        # Step 3: Employee applies for leave
        leave_data = {
            "leave_type": "Sick Leave",
            "start_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "end_date": (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d"),
            "reason": "End-to-end workflow test",
            "days_count": 1.0
        }
        
        leave_id = None
        employee_headers = {"Authorization": f"Bearer {new_employee_token}"}
        
        try:
            response = requests.post(f"{API_BASE}/employee/apply-leave", json=leave_data, headers=employee_headers)
            
            if response.status_code == 200:
                result = response.json()
                leave_id = result.get("id")
                self.log_result("E2E - Employee Apply Leave", True, "Leave application submitted")
            else:
                self.log_result("E2E - Employee Apply Leave", False, f"HTTP {response.status_code}: {response.text}")
                return
                
        except Exception as e:
            self.log_result("E2E - Employee Apply Leave", False, f"Exception: {str(e)}")
            return
        
        # Step 4: Manager can see and process request
        if leave_id:
            try:
                manager_requests_response = requests.get(f"{API_BASE}/manager/leave-requests", headers=admin_headers)
                
                if manager_requests_response.status_code == 200:
                    pending_requests = manager_requests_response.json()
                    
                    our_request = None
                    for req in pending_requests:
                        if req.get("id") == leave_id:
                            our_request = req
                            break
                    
                    if our_request:
                        self.log_result("E2E - Manager See Request", True, 
                                      f"Manager can see leave request from: {our_request['employee_name']}")
                        
                        # Approve the request
                        approval_data = {
                            "status": "approved",
                            "manager_reason": "Approved for E2E workflow test"
                        }
                        
                        approve_response = requests.put(f"{API_BASE}/manager/leave-requests/{leave_id}", 
                                                      json=approval_data, headers=admin_headers)
                        
                        if approve_response.status_code == 200:
                            self.log_result("E2E - Manager Approve", True, "Manager approved leave request")
                            
                            # Step 5: Employee receives notification
                            import time
                            time.sleep(1)
                            
                            notif_response = requests.get(f"{API_BASE}/employee/notifications", headers=employee_headers)
                            if notif_response.status_code == 200:
                                notifications = notif_response.json()
                                
                                approval_notification = None
                                for notif in notifications:
                                    if ("approved" in notif.get("message", "").lower() and 
                                        leave_data["start_date"] in notif.get("message", "")):
                                        approval_notification = notif
                                        break
                                
                                if approval_notification:
                                    self.log_result("E2E - Employee Notification", True, 
                                                  "Employee received approval notification")
                                    
                                    # Step 6: Check leave balance update
                                    balance_response = requests.get(f"{API_BASE}/employee/leave-balance", headers=employee_headers)
                                    if balance_response.status_code == 200:
                                        balance = balance_response.json()
                                        sick_leave_used = balance.get("sick_leave", {}).get("used", 0)
                                        
                                        if sick_leave_used > 0:
                                            self.log_result("E2E - Leave Balance Update", True, 
                                                          f"Leave balance updated - Sick leave used: {sick_leave_used}")
                                        else:
                                            self.log_result("E2E - Leave Balance Update", False, 
                                                          "Leave balance not updated after approval")
                                    else:
                                        self.log_result("E2E - Leave Balance Update", False, 
                                                      "Could not fetch updated leave balance")
                                else:
                                    self.log_result("E2E - Employee Notification", False, 
                                                  "Employee did not receive approval notification")
                            else:
                                self.log_result("E2E - Employee Notification", False, 
                                              "Could not fetch employee notifications")
                        else:
                            self.log_result("E2E - Manager Approve", False, 
                                          f"HTTP {approve_response.status_code}: {approve_response.text}")
                    else:
                        self.log_result("E2E - Manager See Request", False, 
                                      "Manager cannot see the leave request - WORKFLOW BROKEN")
                else:
                    self.log_result("E2E - Manager See Request", False, 
                                  f"Could not fetch manager requests: {manager_requests_response.text}")
                    
            except Exception as e:
                self.log_result("E2E - Manager See Request", False, f"Exception: {str(e)}")

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Testing for FIXED Manager Dashboard and Leave Request Workflow")
        print(f"Backend URL: {BACKEND_URL}")
        
        # Setup test users
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return
        
        # Test the FIXED employee-department assignment system
        self.test_employee_department_assignment_apis()
        
        # Test the FIXED leave application workflow
        self.test_fixed_leave_application_workflow()
        
        # Test end-to-end manager workflow
        self.test_end_to_end_manager_workflow()
        
        # Run existing API tests
        self.test_employee_projects_api()
        self.test_leave_balance_api()
        self.test_apply_leave_api()
        self.test_employee_leave_requests_api()
        self.test_manager_leave_requests_api()
        self.test_manager_leave_decision_api()
        self.test_it_tickets_creation_api()
        self.test_it_tickets_list_api()
        self.test_admin_leave_settings_get_api()
        self.test_admin_leave_settings_put_api()
        
        # Logo upload tests
        self.test_logo_upload_api()
        self.test_logo_remove_api()
        self.test_organization_settings_logo_integration()
        self.test_logo_upload_authentication()
        
        self.test_authentication_scenarios()
        
        # Manager Status and Notification tests
        self.test_manager_status_api()
        self.test_notification_apis()
        self.test_leave_approval_notification_workflow()
        
        # Print summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("🏁 BACKEND API TESTING SUMMARY")
        print("="*80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  • {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = BackendTester()
    tester.run_all_tests()