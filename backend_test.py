#!/usr/bin/env python3
"""
Backend API Testing Script for Smart Attendance System
Focus: CORS Configuration, Auth Registration, Login, and Protected Routes
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL - test local backend first, then production
def get_backend_url():
    # Test local backend first since that's what we can control
    local_url = "http://localhost:8001/api"
    
    # Also get production URL for reference
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    prod_url = line.split('=', 1)[1].strip().rstrip('/') + '/api'
                    print(f"Production URL from .env: {prod_url}")
                    break
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
    
    return local_url

BASE_URL = get_backend_url()
print(f"Testing backend at: {BASE_URL}")

class BackendTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.auth_token = None
        
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            'test': test_name,
            'success': success,
            'message': message,
            'details': details,
            'timestamp': datetime.now().isoformat()
        }
        self.test_results.append(result)
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_cors_preflight(self):
        """Test CORS preflight OPTIONS request"""
        print("\n=== Testing CORS Preflight (OPTIONS) ===")
        
        try:
            # Test preflight for registration endpoint
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.base_url}/auth/register", headers=headers)
            
            # Check response status
            if response.status_code not in [200, 204]:
                self.log_result("CORS Preflight", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
            
            # Check CORS headers
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Methods': response.headers.get('Access-Control-Allow-Methods'),
                'Access-Control-Allow-Headers': response.headers.get('Access-Control-Allow-Headers'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            missing_headers = []
            for header, value in cors_headers.items():
                if not value:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_result("CORS Preflight", False, 
                              f"Missing CORS headers: {missing_headers}", 
                              f"Present headers: {cors_headers}")
                return False
            
            # Verify origin is allowed
            allowed_origin = cors_headers['Access-Control-Allow-Origin']
            if allowed_origin not in ['*', 'https://code-pi-rust.vercel.app']:
                self.log_result("CORS Preflight", False, 
                              f"Origin not properly allowed: {allowed_origin}")
                return False
            
            self.log_result("CORS Preflight", True, 
                          "All CORS headers present and valid", 
                          f"Headers: {cors_headers}")
            return True
            
        except Exception as e:
            self.log_result("CORS Preflight", False, f"Request failed: {str(e)}")
            return False
    
    def test_cors_actual_request(self):
        """Test CORS headers on actual POST request"""
        print("\n=== Testing CORS on Actual Request ===")
        
        try:
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app',
                'Content-Type': 'application/json'
            }
            
            # Use invalid data to avoid creating actual user, just test CORS
            test_data = {
                "username": "cors_test_user",
                "password": "testpass123",
                "role": "student",
                "student_id": "CORS001",
                "class_section": "A5",
                "full_name": "CORS Test User"
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=test_data, headers=headers)
            
            # Check CORS headers in response (regardless of status code)
            cors_headers = {
                'Access-Control-Allow-Origin': response.headers.get('Access-Control-Allow-Origin'),
                'Access-Control-Allow-Credentials': response.headers.get('Access-Control-Allow-Credentials')
            }
            
            if not cors_headers['Access-Control-Allow-Origin']:
                self.log_result("CORS Actual Request", False, 
                              "Missing Access-Control-Allow-Origin header", 
                              f"Response headers: {dict(response.headers)}")
                return False
            
            self.log_result("CORS Actual Request", True, 
                          "CORS headers present in actual request", 
                          f"Status: {response.status_code}, CORS headers: {cors_headers}")
            return True
            
        except Exception as e:
            self.log_result("CORS Actual Request", False, f"Request failed: {str(e)}")
            return False
    
    def test_student_registration(self):
        """Test student registration endpoint"""
        print("\n=== Testing Student Registration ===")
        
        try:
            student_data = {
                "username": "student_test_user",
                "password": "testpass123",
                "role": "student",
                "student_id": "STU001",
                "class_section": "A5",
                "full_name": "Test Student User"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=student_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'user_id' in result:
                    self.log_result("Student Registration", True, 
                                  "Student registered successfully", 
                                  f"User ID: {result['user_id']}")
                    return True
                else:
                    self.log_result("Student Registration", False, 
                                  "Registration response missing user_id", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                result = response.json()
                if "already registered" in result.get('detail', ''):
                    self.log_result("Student Registration", True, 
                                  "User already exists (expected)", 
                                  f"Response: {result}")
                    return True
                else:
                    self.log_result("Student Registration", False, 
                                  f"Registration failed with validation error: {result.get('detail')}", 
                                  f"Full response: {result}")
                    return False
            else:
                self.log_result("Student Registration", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Student Registration", False, f"Request failed: {str(e)}")
            return False
    
    def test_teacher_registration(self):
        """Test teacher registration endpoint"""
        print("\n=== Testing Teacher Registration ===")
        
        try:
            teacher_data = {
                "username": "teacher_test_user",
                "password": "testpass123",
                "role": "teacher",
                "subjects": ["Mathematics", "Physics"],
                "full_name": "Test Teacher User"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=teacher_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'user_id' in result:
                    self.log_result("Teacher Registration", True, 
                                  "Teacher registered successfully", 
                                  f"User ID: {result['user_id']}")
                    return True
                else:
                    self.log_result("Teacher Registration", False, 
                                  "Registration response missing user_id", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                result = response.json()
                if "already registered" in result.get('detail', ''):
                    self.log_result("Teacher Registration", True, 
                                  "User already exists (expected)", 
                                  f"Response: {result}")
                    return True
                else:
                    self.log_result("Teacher Registration", False, 
                                  f"Registration failed with validation error: {result.get('detail')}", 
                                  f"Full response: {result}")
                    return False
            else:
                self.log_result("Teacher Registration", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Teacher Registration", False, f"Request failed: {str(e)}")
            return False
    
    def test_login(self):
        """Test login endpoint and get auth token"""
        print("\n=== Testing Login ===")
        
        try:
            # Try to login with the student user we registered
            login_data = {
                "username": "student_test_user",
                "password": "testpass123"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result and 'token_type' in result:
                    self.auth_token = result['access_token']
                    self.log_result("Login", True, 
                                  "Login successful, token received", 
                                  f"Token type: {result['token_type']}")
                    return True
                else:
                    self.log_result("Login", False, 
                                  "Login response missing token fields", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 401:
                # Try with teacher credentials
                teacher_login_data = {
                    "username": "teacher_test_user",
                    "password": "testpass123"
                }
                
                response = self.session.post(f"{self.base_url}/auth/login", 
                                           json=teacher_login_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'access_token' in result:
                        self.auth_token = result['access_token']
                        self.log_result("Login", True, 
                                      "Login successful with teacher credentials", 
                                      f"Token type: {result['token_type']}")
                        return True
                
                self.log_result("Login", False, 
                              "Login failed - invalid credentials", 
                              f"Response: {response.text}")
                return False
            else:
                self.log_result("Login", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Login", False, f"Request failed: {str(e)}")
            return False
    
    def test_protected_route(self):
        """Test protected route with Bearer token"""
        print("\n=== Testing Protected Route ===")
        
        if not self.auth_token:
            self.log_result("Protected Route", False, "No auth token available")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.auth_token}',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'username' in result and 'role' in result:
                    self.log_result("Protected Route", True, 
                                  "Protected route accessible with valid token", 
                                  f"User: {result['username']}, Role: {result['role']}")
                    return True
                else:
                    self.log_result("Protected Route", False, 
                                  "Protected route response missing user fields", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 401:
                self.log_result("Protected Route", False, 
                              "Protected route rejected valid token", 
                              f"Response: {response.text}")
                return False
            else:
                self.log_result("Protected Route", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Protected Route", False, f"Request failed: {str(e)}")
            return False
    
    def test_protected_route_without_token(self):
        """Test protected route without Bearer token (should fail)"""
        print("\n=== Testing Protected Route Without Token ===")
        
        try:
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code in [401, 403]:
                self.log_result("Protected Route (No Token)", True, 
                              "Protected route correctly rejected request without token", 
                              f"Response: {response.status_code}")
                return True
            else:
                self.log_result("Protected Route (No Token)", False, 
                              f"Protected route should return 401, got: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Protected Route (No Token)", False, f"Request failed: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n{'='*60}")
        print("SMART ATTENDANCE BACKEND API TESTING")
        print(f"{'='*60}")
        print(f"Backend URL: {self.base_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Run tests in order
        tests = [
            self.test_cors_preflight,
            self.test_cors_actual_request,
            self.test_student_registration,
            self.test_teacher_registration,
            self.test_login,
            self.test_protected_route,
            self.test_protected_route_without_token
        ]
        
        passed = 0
        total = len(tests)
        
        for test in tests:
            try:
                if test():
                    passed += 1
            except Exception as e:
                print(f"Test {test.__name__} crashed: {e}")
        
        # Summary
        print(f"\n{'='*60}")
        print("TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = BackendTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)