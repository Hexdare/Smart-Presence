#!/usr/bin/env python3
"""
Focused Admin Login Test for Smart Attendance System
Testing the specific issue reported by the user
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL - use the external URL from frontend .env
def get_backend_url():
    try:
        # Read the backend URL from frontend .env file
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    backend_base = line.split('=', 1)[1].strip()
                    backend_url = f"{backend_base}/api"
                    print(f"Backend URL from .env: {backend_url}")
                    return backend_url
    except Exception as e:
        print(f"Could not read backend URL from .env: {e}")
    
    # Fallback to local URL
    backend_url = "http://127.0.0.1:8001/api"
    print(f"Fallback Backend URL: {backend_url}")
    return backend_url

BASE_URL = get_backend_url()

def test_admin_login():
    """Test admin login with exact credentials from user report"""
    print(f"\n{'='*60}")
    print("ADMIN LOGIN SPECIFIC TEST")
    print(f"{'='*60}")
    print(f"Backend URL: {BASE_URL}")
    print(f"Testing admin login with credentials: admin/admin123")
    
    # Test 1: Check if system_admin.json exists
    print("\n1. Checking system_admin.json file...")
    try:
        with open('/app/backend/system_admin.json', 'r') as f:
            admin_data = json.load(f)
            print(f"✅ system_admin.json exists")
            print(f"   Username: {admin_data['system_admin']['username']}")
            print(f"   Password: {admin_data['system_admin']['password']}")
            print(f"   Role: {admin_data['system_admin']['role']}")
    except Exception as e:
        print(f"❌ system_admin.json file issue: {e}")
        return False
    
    # Test 2: Test the login endpoint accessibility
    print("\n2. Testing login endpoint accessibility...")
    try:
        # Test with a simple GET to see if endpoint exists
        response = requests.get(f"{BASE_URL}/auth/login")
        if response.status_code == 405:  # Method not allowed is expected for GET on POST endpoint
            print("✅ Login endpoint is accessible (405 Method Not Allowed for GET is expected)")
        else:
            print(f"⚠️  Unexpected response for GET: {response.status_code}")
    except Exception as e:
        print(f"❌ Cannot reach login endpoint: {e}")
        return False
    
    # Test 3: Test admin login with exact credentials
    print("\n3. Testing admin login with credentials admin/admin123...")
    try:
        login_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=headers)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Admin login successful!")
            print(f"   Access Token: {result.get('access_token', 'Missing')[:50]}...")
            print(f"   Token Type: {result.get('token_type', 'Missing')}")
            
            # Test 4: Verify admin user info
            print("\n4. Testing admin user info retrieval...")
            if 'access_token' in result:
                auth_headers = {
                    'Authorization': f'Bearer {result["access_token"]}',
                    'Content-Type': 'application/json'
                }
                
                me_response = requests.get(f"{BASE_URL}/auth/me", headers=auth_headers)
                print(f"   Status Code: {me_response.status_code}")
                
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print(f"✅ Admin user info retrieved successfully!")
                    print(f"   Username: {user_info.get('username')}")
                    print(f"   Role: {user_info.get('role')}")
                    print(f"   Full Name: {user_info.get('full_name')}")
                    
                    if user_info.get('role') == 'system_admin' and user_info.get('username') == 'admin':
                        print("✅ All admin login functionality working correctly!")
                        return True
                    else:
                        print(f"❌ User info mismatch. Expected role: system_admin, username: admin")
                        return False
                else:
                    print(f"❌ Failed to get user info: {me_response.text}")
                    return False
            else:
                print("❌ No access token in login response")
                return False
                
        elif response.status_code == 401:
            print(f"❌ Admin login failed with 401 Unauthorized")
            print(f"   Response: {response.text}")
            
            # Additional debugging
            print("\n   DEBUGGING INFO:")
            print("   - Checking if backend is reading system_admin.json correctly...")
            print("   - This suggests the system_admin.json file check in backend is not working")
            return False
        else:
            print(f"❌ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Login request failed: {e}")
        return False

def test_other_endpoints():
    """Test other API endpoints to ensure backend is working"""
    print(f"\n5. Testing other API endpoints to verify backend functionality...")
    
    # Test registration endpoint
    try:
        test_user = {
            "username": "test_connectivity_user",
            "password": "testpass123",
            "role": "student",
            "student_id": "TEST001",
            "class_section": "A5",
            "full_name": "Test Connectivity User"
        }
        
        headers = {'Content-Type': 'application/json'}
        response = requests.post(f"{BASE_URL}/auth/register", json=test_user, headers=headers)
        
        if response.status_code in [200, 400]:  # 200 = success, 400 = already exists
            print("✅ Registration endpoint is working")
            
            # Try login with this user
            login_data = {
                "username": "test_connectivity_user",
                "password": "testpass123"
            }
            
            login_response = requests.post(f"{BASE_URL}/auth/login", json=login_data, headers=headers)
            
            if login_response.status_code == 200:
                print("✅ Regular user login is working")
                return True
            else:
                print(f"⚠️  Regular user login failed: {login_response.status_code}")
                print(f"   Response: {login_response.text}")
                return False
        else:
            print(f"⚠️  Registration endpoint issue: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Other endpoints test failed: {e}")
        return False

if __name__ == "__main__":
    print("Starting focused admin login test...")
    
    admin_success = test_admin_login()
    other_success = test_other_endpoints()
    
    print(f"\n{'='*60}")
    print("TEST RESULTS SUMMARY")
    print(f"{'='*60}")
    print(f"Admin Login Test: {'✅ PASS' if admin_success else '❌ FAIL'}")
    print(f"Other Endpoints Test: {'✅ PASS' if other_success else '❌ FAIL'}")
    
    if admin_success:
        print("\n🎉 CONCLUSION: Admin login is working correctly!")
        print("   The user should be able to login with admin/admin123")
    else:
        print("\n❌ CONCLUSION: Admin login is NOT working!")
        print("   There is an issue with the system admin authentication")
    
    sys.exit(0 if admin_success else 1)