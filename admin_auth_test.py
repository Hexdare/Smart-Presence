#!/usr/bin/env python3
"""
Comprehensive System Admin Authentication Test
Tests the updated environment variable-based authentication system
"""

import requests
import json
import os
from pathlib import Path
from dotenv import load_dotenv

def test_local_admin_auth():
    """Test local admin authentication with environment variables"""
    print("=== Testing Local Admin Authentication ===")
    
    # Load environment variables
    ROOT_DIR = Path(__file__).parent / "backend"
    env_file = ROOT_DIR / '.env'
    load_dotenv(env_file)
    
    # Verify environment variables are loaded
    username = os.environ.get("SYSTEM_ADMIN_USERNAME")
    password = os.environ.get("SYSTEM_ADMIN_PASSWORD")
    full_name = os.environ.get("SYSTEM_ADMIN_FULL_NAME")
    
    print(f"Environment Variables:")
    print(f"  SYSTEM_ADMIN_USERNAME: {username}")
    print(f"  SYSTEM_ADMIN_PASSWORD: {'*' * len(password) if password else 'NOT_SET'}")
    print(f"  SYSTEM_ADMIN_FULL_NAME: {full_name}")
    
    if not username or not password:
        print("❌ Environment variables not properly set")
        return False
    
    # Test login
    base_url = "http://127.0.0.1:8001/api"
    login_data = {
        "username": username,
        "password": password
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        print(f"\n1. Testing admin login at {base_url}/auth/login")
        response = requests.post(f"{base_url}/auth/login", json=login_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'access_token' in result and 'token_type' in result:
                print("✅ Admin login successful - received JWT token")
                token = result['access_token']
                
                # Test /auth/me endpoint
                print(f"\n2. Testing /auth/me endpoint with JWT token")
                auth_headers = {
                    'Authorization': f'Bearer {token}',
                    'Content-Type': 'application/json'
                }
                
                me_response = requests.get(f"{base_url}/auth/me", headers=auth_headers)
                
                if me_response.status_code == 200:
                    user_info = me_response.json()
                    print("✅ User info retrieval successful")
                    print(f"   Username: {user_info.get('username')}")
                    print(f"   Role: {user_info.get('role')}")
                    print(f"   Full Name: {user_info.get('full_name')}")
                    
                    # Verify correct admin info
                    if (user_info.get('username') == username and 
                        user_info.get('role') == 'system_admin' and
                        user_info.get('full_name') == full_name):
                        print("✅ Admin user info is correct")
                        return True
                    else:
                        print("❌ Admin user info is incorrect")
                        return False
                else:
                    print(f"❌ User info retrieval failed: {me_response.status_code}")
                    print(f"   Response: {me_response.text}")
                    return False
            else:
                print("❌ Login response missing token fields")
                print(f"   Response: {result}")
                return False
        else:
            print(f"❌ Admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_production_admin_auth():
    """Test production admin authentication"""
    print("\n=== Testing Production Admin Authentication ===")
    
    base_url = "https://smart-attendance-system-ur85.onrender.com/api"
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    headers = {'Content-Type': 'application/json'}
    
    try:
        print(f"Testing admin login at {base_url}/auth/login")
        response = requests.post(f"{base_url}/auth/login", json=login_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'access_token' in result:
                print("✅ Production admin login successful")
                return True
            else:
                print("❌ Production login response missing token")
                return False
        else:
            print(f"❌ Production admin login failed: {response.status_code}")
            print(f"   Response: {response.text}")
            print("   This indicates the production deployment doesn't have the updated environment variable code")
            return False
            
    except Exception as e:
        print(f"❌ Production request failed: {str(e)}")
        return False

def test_environment_variable_implementation():
    """Test that the backend code properly uses environment variables"""
    print("\n=== Testing Environment Variable Implementation ===")
    
    # Check if system_admin.json file still exists (should be removed or ignored)
    admin_file = Path("/app/backend/system_admin.json")
    if admin_file.exists():
        print("⚠️  system_admin.json file still exists but should be ignored")
        with open(admin_file, 'r') as f:
            content = f.read()
            print(f"   File content: {content}")
    else:
        print("✅ system_admin.json file does not exist (good for production)")
    
    # Verify environment variables are the source of truth
    ROOT_DIR = Path(__file__).parent / "backend"
    env_file = ROOT_DIR / '.env'
    load_dotenv(env_file)
    
    username = os.environ.get("SYSTEM_ADMIN_USERNAME")
    password = os.environ.get("SYSTEM_ADMIN_PASSWORD")
    
    if username == "admin" and password == "admin123":
        print("✅ Environment variables contain correct admin credentials")
        return True
    else:
        print("❌ Environment variables don't contain expected credentials")
        return False

def main():
    """Run all admin authentication tests"""
    print("SYSTEM ADMIN AUTHENTICATION TEST")
    print("=" * 50)
    
    results = []
    
    # Test environment variable implementation
    results.append(test_environment_variable_implementation())
    
    # Test local authentication
    results.append(test_local_admin_auth())
    
    # Test production authentication
    results.append(test_production_admin_auth())
    
    print("\n" + "=" * 50)
    print("TEST SUMMARY")
    print("=" * 50)
    
    passed = sum(results)
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    if passed == total:
        print("✅ All tests passed - Environment variable authentication is working locally")
        print("⚠️  Production deployment needs to be updated with the new code")
    else:
        print("❌ Some tests failed - Check the implementation")
    
    return passed == total

if __name__ == "__main__":
    main()