#!/usr/bin/env python3
"""
Test the complete manager workflow to identify the issue
"""

import requests
import json
import uuid
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def test_complete_manager_workflow():
    """Test the complete manager workflow"""
    
    # Step 1: Create test employee
    employee_data = {
        "name": "Test Employee Manager Workflow",
        "email": f"test_mgr_{uuid.uuid4().hex[:8]}@test.com",
        "phone": f"555{uuid.uuid4().hex[:7]}",
        "password": "testpass123"
    }
    
    employee_response = requests.post(f"{API_BASE}/auth/register", json=employee_data)
    if employee_response.status_code != 200:
        print(f"Failed to create employee: {employee_response.text}")
        return
        
    employee_token = employee_response.json()["access_token"]
    employee_headers = {"Authorization": f"Bearer {employee_token}"}
    
    # Get employee ID
    me_response = requests.get(f"{API_BASE}/auth/me", headers=employee_headers)
    employee_id = me_response.json()["id"]
    print(f"Created employee with ID: {employee_id}")
    
    # Step 2: Login as admin
    admin_login = {
        "email": "admin@worktracker.com",
        "password": "admin123"
    }
    
    admin_response = requests.post(f"{API_BASE}/admin/auth/login", json=admin_login)
    if admin_response.status_code != 200:
        print(f"Failed to login as admin: {admin_response.text}")
        return
        
    admin_token = admin_response.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}
    
    # Step 3: Create a department
    dept_data = {
        "name": f"Test Workflow Dept {uuid.uuid4().hex[:8]}",
        "description": "Test department for workflow testing"
    }
    
    dept_response = requests.post(f"{API_BASE}/admin/create-department", json=dept_data, headers=admin_headers)
    if dept_response.status_code != 200:
        print(f"Failed to create department: {dept_response.text}")
        return
        
    dept_id = dept_response.json()["department_id"]
    print(f"Created department with ID: {dept_id}")
    
    # Step 4: Create another employee to be the manager
    manager_employee_data = {
        "name": "Manager Employee",
        "email": f"manager_{uuid.uuid4().hex[:8]}@test.com",
        "phone": f"555{uuid.uuid4().hex[:7]}",
        "password": "managerpass123"
    }
    
    manager_emp_response = requests.post(f"{API_BASE}/auth/register", json=manager_employee_data)
    if manager_emp_response.status_code != 200:
        print(f"Failed to create manager employee: {manager_emp_response.text}")
        return
        
    manager_token = manager_emp_response.json()["access_token"]
    manager_headers = {"Authorization": f"Bearer {manager_token}"}
    
    # Get manager employee ID
    manager_me_response = requests.get(f"{API_BASE}/auth/me", headers=manager_headers)
    manager_employee_id = manager_me_response.json()["id"]
    print(f"Created manager employee with ID: {manager_employee_id}")
    
    # Step 5: Assign the manager employee as manager of the department
    manager_data = {
        "employee_id": manager_employee_id,
        "department_id": dept_id
    }
    
    manager_assign_response = requests.post(f"{API_BASE}/admin/create-manager", json=manager_data, headers=admin_headers)
    if manager_assign_response.status_code != 200:
        print(f"Failed to assign manager: {manager_assign_response.text}")
        return
        
    manager_id = manager_assign_response.json()["manager_id"]
    print(f"Assigned manager with ID: {manager_id}")
    
    # Step 6: Check manager status for the manager employee
    manager_status_response = requests.get(f"{API_BASE}/employee/manager-status", headers=manager_headers)
    if manager_status_response.status_code == 200:
        status = manager_status_response.json()
        print(f"Manager status: {status}")
    else:
        print(f"Failed to get manager status: {manager_status_response.text}")
    
    # Step 7: Now we need to assign the regular employee to this department
    # But there's no API for this! This is the missing piece.
    print("\n=== ISSUE IDENTIFIED ===")
    print("There's no API to assign employees to departments!")
    print("The apply-leave API expects employees to have department assignments,")
    print("but there's no way to assign employees to departments in the current system.")
    
    # Step 8: Let's try to apply for leave anyway and see what happens
    leave_data = {
        "leave_type": "Casual Leave",
        "start_date": "2024-12-20",
        "end_date": "2024-12-20",
        "reason": "Testing workflow",
        "days_count": 1.0
    }
    
    leave_response = requests.post(f"{API_BASE}/employee/apply-leave", json=leave_data, headers=employee_headers)
    if leave_response.status_code == 200:
        leave_result = leave_response.json()
        leave_id = leave_result["id"]
        print(f"Leave application created with ID: {leave_id}")
        
        # Step 9: Check if the manager can see this leave request
        manager_requests_response = requests.get(f"{API_BASE}/manager/leave-requests", headers=manager_headers)
        if manager_requests_response.status_code == 200:
            pending_requests = manager_requests_response.json()
            print(f"Manager sees {len(pending_requests)} pending requests")
            
            # Look for our leave request
            our_request = None
            for req in pending_requests:
                if req.get("id") == leave_id:
                    our_request = req
                    break
            
            if our_request:
                print("✅ SUCCESS: Manager can see the leave request!")
            else:
                print("❌ ISSUE: Manager cannot see the leave request")
                print("This confirms that the manager_id is not being set correctly in leave applications")
        else:
            print(f"Failed to get manager requests: {manager_requests_response.text}")
    else:
        print(f"Failed to apply for leave: {leave_response.text}")

if __name__ == "__main__":
    test_complete_manager_workflow()