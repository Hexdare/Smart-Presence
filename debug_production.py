#!/usr/bin/env python3
"""
Debug script to test production environment file paths
"""

import requests
import json

def test_production_debug():
    """Test production backend with debug information"""
    
    # Test a simple endpoint to see if we can get any debug info
    try:
        # Try to register a test user to see if the backend is working
        backend_url = "https://smart-attendance-system-ur85.onrender.com/api"
        
        test_data = {
            "username": "debug_test_user_12345",
            "password": "testpass123",
            "role": "student",
            "student_id": "DEBUG001",
            "class_section": "A5",
            "full_name": "Debug Test User"
        }
        
        headers = {
            'Content-Type': 'application/json',
            'Origin': 'https://smart-presence-sacs.vercel.app'
        }
        
        print("Testing user registration to verify backend is working...")
        response = requests.post(f"{backend_url}/auth/register", json=test_data, headers=headers)
        
        print(f"Registration response: {response.status_code}")
        print(f"Registration body: {response.text}")
        
        if response.status_code in [200, 400]:  # 400 might be "user already exists"
            print("✅ Backend is working for regular operations")
        else:
            print("❌ Backend has issues with regular operations")
            
        # Now test admin login again with detailed output
        print("\nTesting admin login...")
        admin_data = {
            "username": "admin",
            "password": "admin123"
        }
        
        response = requests.post(f"{backend_url}/auth/login", json=admin_data, headers=headers)
        print(f"Admin login response: {response.status_code}")
        print(f"Admin login body: {response.text}")
        print(f"Admin login headers: {dict(response.headers)}")
        
        # Test with different credentials to see if it's a general auth issue
        print("\nTesting with wrong credentials to see error difference...")
        wrong_data = {
            "username": "wronguser",
            "password": "wrongpass"
        }
        
        response = requests.post(f"{backend_url}/auth/login", json=wrong_data, headers=headers)
        print(f"Wrong credentials response: {response.status_code}")
        print(f"Wrong credentials body: {response.text}")
        
    except Exception as e:
        print(f"Error during testing: {e}")

if __name__ == "__main__":
    test_production_debug()