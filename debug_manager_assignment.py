#!/usr/bin/env python3
"""
Debug script to check manager assignment logic
"""

import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')

# Get backend URL from environment
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

def debug_manager_assignment():
    """Debug the manager assignment issue"""
    
    # Login as admin to check data
    admin_login = {
        "email": "admin@worktracker.com",
        "password": "admin123"
    }
    
    try:
        login_response = requests.post(f"{API_BASE}/admin/auth/login", json=admin_login)
        if login_response.status_code != 200:
            print(f"Failed to login as admin: {login_response.text}")
            return
            
        admin_token = login_response.json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Get all departments
        print("=== Departments ===")
        dept_response = requests.get(f"{API_BASE}/admin/departments", headers=admin_headers)
        if dept_response.status_code == 200:
            departments = dept_response.json()
            for dept in departments:
                print(f"Department: {dept['name']} (ID: {dept['id']})")
        else:
            print(f"Failed to get departments: {dept_response.text}")
        
        # Get all managers
        print("\n=== Managers ===")
        manager_response = requests.get(f"{API_BASE}/admin/managers", headers=admin_headers)
        if manager_response.status_code == 200:
            managers = manager_response.json()
            for manager in managers:
                print(f"Manager: {manager['employee_name']} (Employee ID: {manager['employee_id']}, Department: {manager['department_name']})")
        else:
            print(f"Failed to get managers: {manager_response.text}")
        
        # Get all employees
        print("\n=== Employees ===")
        emp_response = requests.get(f"{API_BASE}/admin/employees", headers=admin_headers)
        if emp_response.status_code == 200:
            employees = emp_response.json()
            for emp in employees[:5]:  # Show first 5 employees
                print(f"Employee: {emp['name']} (ID: {emp['id']}, Department: {emp.get('department', 'None')})")
        else:
            print(f"Failed to get employees: {emp_response.text}")
            
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    debug_manager_assignment()