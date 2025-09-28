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
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Testing for Employee Dashboard and Leave Management")
        print(f"Backend URL: {BACKEND_URL}")
        
        # Setup test users
        if not self.setup_test_users():
            print("❌ Failed to setup test users. Aborting tests.")
            return
        
        # Run all API tests
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