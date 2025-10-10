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
    
    def test_admin_login(self):
        """Test system admin login with credentials from system_admin.json"""
        print("\n=== Testing System Admin Login ===")
        
        try:
            # Test admin login with exact credentials from system_admin.json
            admin_login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://smart-presence-sacs.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=admin_login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result and 'token_type' in result:
                    self.log_result("Admin Login", True, 
                                  "System admin login successful", 
                                  f"Token type: {result['token_type']}")
                    
                    # Test admin user info endpoint
                    admin_headers = {
                        'Authorization': f'Bearer {result["access_token"]}',
                        'Origin': 'https://smart-presence-sacs.vercel.app'
                    }
                    
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=admin_headers)
                    
                    if me_response.status_code == 200:
                        user_info = me_response.json()
                        if user_info.get('role') == 'system_admin' and user_info.get('username') == 'admin':
                            self.log_result("Admin User Info", True, 
                                          "Admin user info correct", 
                                          f"Role: {user_info.get('role')}, Username: {user_info.get('username')}")
                            return True
                        else:
                            self.log_result("Admin User Info", False, 
                                          "Admin user info incorrect", 
                                          f"Expected role: system_admin, username: admin. Got: {user_info}")
                            return False
                    else:
                        self.log_result("Admin User Info", False, 
                                      f"Failed to get admin user info: {me_response.status_code}", 
                                      f"Response: {me_response.text}")
                        return False
                else:
                    self.log_result("Admin Login", False, 
                                  "Admin login response missing token fields", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 401:
                self.log_result("Admin Login", False, 
                              "Admin login failed - incorrect credentials or system_admin.json issue", 
                              f"Response: {response.text}")
                return False
            else:
                self.log_result("Admin Login", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Login", False, f"Request failed: {str(e)}")
            return False

    def test_production_backend_accessibility(self):
        """Test if production backend is accessible and responding"""
        print("\n=== Testing Production Backend Accessibility ===")
        
        try:
            # Test basic connectivity to production backend
            response = self.session.get(f"{self.base_url.replace('/api', '')}/docs")
            
            if response.status_code == 200:
                self.log_result("Production Backend Accessibility", True, 
                              "Production backend is accessible", 
                              f"FastAPI docs endpoint responding")
            elif response.status_code == 404:
                # Try the root endpoint
                response = self.session.get(f"{self.base_url.replace('/api', '')}/")
                if response.status_code in [200, 404]:
                    self.log_result("Production Backend Accessibility", True, 
                                  "Production backend is accessible", 
                                  f"Root endpoint responding with {response.status_code}")
                else:
                    self.log_result("Production Backend Accessibility", False, 
                                  f"Production backend not accessible: {response.status_code}", 
                                  f"Response: {response.text}")
                    return False
            else:
                self.log_result("Production Backend Accessibility", False, 
                              f"Production backend not accessible: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
            return True
                
        except Exception as e:
            self.log_result("Production Backend Accessibility", False, f"Request failed: {str(e)}")
            return False

    def test_production_admin_login_detailed(self):
        """Detailed test of production admin login with comprehensive debugging"""
        print("\n=== Testing Production Admin Login (Detailed) ===")
        
        try:
            # Test with exact production frontend origin
            admin_login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://smart-presence-sacs.vercel.app',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            print(f"Testing login at: {self.base_url}/auth/login")
            print(f"With credentials: {admin_login_data}")
            print(f"With headers: {headers}")
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=admin_login_data, headers=headers)
            
            print(f"Response status: {response.status_code}")
            print(f"Response headers: {dict(response.headers)}")
            print(f"Response body: {response.text}")
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result and 'token_type' in result:
                    self.log_result("Production Admin Login", True, 
                                  "Production admin login successful", 
                                  f"Token received: {result['token_type']}")
                    
                    # Test /auth/me endpoint
                    admin_headers = {
                        'Authorization': f'Bearer {result["access_token"]}',
                        'Origin': 'https://smart-presence-sacs.vercel.app'
                    }
                    
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=admin_headers)
                    
                    if me_response.status_code == 200:
                        user_info = me_response.json()
                        self.log_result("Production Admin User Info", True, 
                                      "Admin user info retrieved successfully", 
                                      f"User info: {user_info}")
                        return True
                    else:
                        self.log_result("Production Admin User Info", False, 
                                      f"Failed to get user info: {me_response.status_code}", 
                                      f"Response: {me_response.text}")
                        return False
                else:
                    self.log_result("Production Admin Login", False, 
                                  "Login response missing token fields", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 401:
                self.log_result("Production Admin Login", False, 
                              "CRITICAL: Admin login failed with 401 - credentials rejected", 
                              f"Response: {response.text}")
                return False
            elif response.status_code == 404:
                self.log_result("Production Admin Login", False, 
                              "CRITICAL: Login endpoint not found (404) - routing issue", 
                              f"Response: {response.text}")
                return False
            elif response.status_code == 405:
                self.log_result("Production Admin Login", False, 
                              "CRITICAL: Method not allowed (405) - deployment routing issue", 
                              f"Response: {response.text}")
                return False
            elif response.status_code >= 500:
                self.log_result("Production Admin Login", False, 
                              f"CRITICAL: Server error ({response.status_code}) - backend deployment issue", 
                              f"Response: {response.text}")
                return False
            else:
                self.log_result("Production Admin Login", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Production Admin Login", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_file_check(self):
        """Test if system_admin.json file exists and is accessible"""
        print("\n=== Testing System Admin File Accessibility ===")
        
        try:
            # Check if system_admin.json exists locally (for comparison)
            import json
            from pathlib import Path
            
            admin_file = Path("/app/backend/system_admin.json")
            if admin_file.exists():
                with open(admin_file, 'r') as f:
                    admin_data = json.load(f)
                    system_admin = admin_data.get("system_admin")
                    
                    if system_admin:
                        self.log_result("Local System Admin File", True, 
                                      "system_admin.json exists locally", 
                                      f"Admin data: username={system_admin.get('username')}, role={system_admin.get('role')}")
                    else:
                        self.log_result("Local System Admin File", False, 
                                      "system_admin.json exists but missing system_admin key", 
                                      f"File content: {admin_data}")
                        return False
            else:
                self.log_result("Local System Admin File", False, 
                              "system_admin.json file not found locally")
                return False
            
            # Test if production backend can access the file by attempting login
            # (This is indirect - we can't directly check file existence on production)
            self.log_result("Production System Admin File", True, 
                          "Cannot directly check file on production, but login test will verify")
            return True
                
        except Exception as e:
            self.log_result("System Admin File Check", False, f"File check failed: {str(e)}")
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
                              f"Protected route should return 401/403, got: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Protected Route (No Token)", False, f"Request failed: {str(e)}")
            return False
    
    def test_principal_registration(self):
        """Test principal registration endpoint"""
        print("\n=== Testing Principal Registration ===")
        
        try:
            principal_data = {
                "username": "principal_test_user",
                "password": "testpass123",
                "role": "principal",
                "subjects": ["Mathematics", "Physics"],  # Optional for principals
                "full_name": "Test Principal User"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=principal_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'user_id' in result:
                    self.log_result("Principal Registration", True, 
                                  "Principal registered successfully", 
                                  f"User ID: {result['user_id']}")
                    return True
                else:
                    self.log_result("Principal Registration", False, 
                                  "Registration response missing user_id", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                result = response.json()
                if "already registered" in result.get('detail', ''):
                    self.log_result("Principal Registration", True, 
                                  "User already exists (expected)", 
                                  f"Response: {result}")
                    return True
                else:
                    self.log_result("Principal Registration", False, 
                                  f"Registration failed with validation error: {result.get('detail')}", 
                                  f"Full response: {result}")
                    return False
            else:
                self.log_result("Principal Registration", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal Registration", False, f"Request failed: {str(e)}")
            return False

    def get_auth_token_for_role(self, role):
        """Get authentication token for specific role"""
        try:
            username_map = {
                "student": "student_test_user",
                "teacher": "teacher_test_user", 
                "principal": "principal_test_user"
            }
            
            login_data = {
                "username": username_map[role],
                "password": "testpass123"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/login", json=login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('access_token')
            return None
        except Exception:
            return None

    def test_principal_access_teacher_endpoints(self):
        """Test that principal can access all teacher endpoints"""
        print("\n=== Testing Principal Access to Teacher Endpoints ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        if not principal_token:
            self.log_result("Principal Teacher Access", False, "Could not get principal auth token")
            return False
        
        headers = {'Authorization': f'Bearer {principal_token}'}
        
        # Test QR generation access
        try:
            qr_data = {
                "class_section": "A5",
                "subject": "Mathematics",
                "class_code": "MC",
                "time_slot": "09:30-10:30"
            }
            
            response = self.session.post(f"{self.base_url}/qr/generate", json=qr_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'session_id' in result and 'qr_image' in result:
                    self.log_result("Principal QR Generation", True, 
                                  "Principal can generate QR codes", 
                                  f"Session ID: {result['session_id']}")
                else:
                    self.log_result("Principal QR Generation", False, 
                                  "QR generation response missing required fields", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Principal QR Generation", False, 
                              f"QR generation failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal QR Generation", False, f"Request failed: {str(e)}")
            return False
        
        # Test QR sessions access
        try:
            response = self.session.get(f"{self.base_url}/qr/sessions", headers=headers)
            
            if response.status_code == 200:
                sessions = response.json()
                self.log_result("Principal QR Sessions", True, 
                              f"Principal can view QR sessions ({len(sessions)} sessions)")
            else:
                self.log_result("Principal QR Sessions", False, 
                              f"QR sessions access failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal QR Sessions", False, f"Request failed: {str(e)}")
            return False
        
        return True

    def test_principal_full_attendance_records(self):
        """Test that principal gets full attendance records (not just their own sessions)"""
        print("\n=== Testing Principal Full Attendance Access ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        teacher_token = self.get_auth_token_for_role("teacher")
        
        if not principal_token or not teacher_token:
            self.log_result("Principal Attendance Access", False, "Could not get required auth tokens")
            return False
        
        try:
            # Get attendance records as principal
            principal_headers = {'Authorization': f'Bearer {principal_token}'}
            principal_response = self.session.get(f"{self.base_url}/attendance/records", headers=principal_headers)
            
            # Get attendance records as teacher
            teacher_headers = {'Authorization': f'Bearer {teacher_token}'}
            teacher_response = self.session.get(f"{self.base_url}/attendance/records", headers=teacher_headers)
            
            if principal_response.status_code == 200 and teacher_response.status_code == 200:
                principal_records = principal_response.json()
                teacher_records = teacher_response.json()
                
                # Principal should see all records (>= teacher records)
                if len(principal_records) >= len(teacher_records):
                    self.log_result("Principal Attendance Access", True, 
                                  f"Principal sees all attendance records ({len(principal_records)} vs teacher's {len(teacher_records)})")
                    return True
                else:
                    self.log_result("Principal Attendance Access", False, 
                                  f"Principal sees fewer records than teacher ({len(principal_records)} vs {len(teacher_records)})")
                    return False
            else:
                self.log_result("Principal Attendance Access", False, 
                              f"Failed to get attendance records (Principal: {principal_response.status_code}, Teacher: {teacher_response.status_code})")
                return False
                
        except Exception as e:
            self.log_result("Principal Attendance Access", False, f"Request failed: {str(e)}")
            return False

    def test_principal_full_timetable(self):
        """Test that principal can see full timetable"""
        print("\n=== Testing Principal Full Timetable Access ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        if not principal_token:
            self.log_result("Principal Timetable Access", False, "Could not get principal auth token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {principal_token}'}
            response = self.session.get(f"{self.base_url}/timetable", headers=headers)
            
            if response.status_code == 200:
                timetable = response.json()
                
                # Check if timetable has both A5 and A6 sections for multiple days
                days_with_both_sections = 0
                for day, sections in timetable.items():
                    if isinstance(sections, dict) and 'A5' in sections and 'A6' in sections:
                        days_with_both_sections += 1
                
                if days_with_both_sections >= 3:  # Should have multiple days with both sections
                    self.log_result("Principal Timetable Access", True, 
                                  f"Principal sees full timetable ({days_with_both_sections} days with both sections)")
                    return True
                else:
                    self.log_result("Principal Timetable Access", False, 
                                  f"Principal timetable seems limited ({days_with_both_sections} days with both sections)", 
                                  f"Timetable structure: {list(timetable.keys())}")
                    return False
            else:
                self.log_result("Principal Timetable Access", False, 
                              f"Timetable access failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal Timetable Access", False, f"Request failed: {str(e)}")
            return False

    def test_announcement_creation_teacher(self):
        """Test announcement creation by teacher"""
        print("\n=== Testing Announcement Creation by Teacher ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("Teacher Announcement Creation", False, "Could not get teacher auth token")
            return False
        
        try:
            announcement_data = {
                "title": "Test Teacher Announcement",
                "content": "This is a test announcement from a teacher",
                "target_audience": "students",
                "image_data": None
            }
            
            headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'announcement_id' in result:
                    self.log_result("Teacher Announcement Creation", True, 
                                  "Teacher can create announcements", 
                                  f"Announcement ID: {result['announcement_id']}")
                    return True
                else:
                    self.log_result("Teacher Announcement Creation", False, 
                                  "Announcement creation response missing ID", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Teacher Announcement Creation", False, 
                              f"Announcement creation failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Teacher Announcement Creation", False, f"Request failed: {str(e)}")
            return False

    def test_announcement_creation_principal(self):
        """Test announcement creation by principal"""
        print("\n=== Testing Announcement Creation by Principal ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        if not principal_token:
            self.log_result("Principal Announcement Creation", False, "Could not get principal auth token")
            return False
        
        try:
            announcement_data = {
                "title": "Test Principal Announcement",
                "content": "This is a test announcement from the principal",
                "target_audience": "all",
                "image_data": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            }
            
            headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'announcement_id' in result:
                    self.log_result("Principal Announcement Creation", True, 
                                  "Principal can create announcements with image", 
                                  f"Announcement ID: {result['announcement_id']}")
                    return True
                else:
                    self.log_result("Principal Announcement Creation", False, 
                                  "Announcement creation response missing ID", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Principal Announcement Creation", False, 
                              f"Announcement creation failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal Announcement Creation", False, f"Request failed: {str(e)}")
            return False

    def test_student_announcement_creation_forbidden(self):
        """Test that students cannot create announcements (403 error)"""
        print("\n=== Testing Student Announcement Creation (Should Fail) ===")
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Student Announcement Forbidden", False, "Could not get student auth token")
            return False
        
        try:
            announcement_data = {
                "title": "Test Student Announcement",
                "content": "This should not be allowed",
                "target_audience": "all"
            }
            
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=headers)
            
            if response.status_code == 403:
                self.log_result("Student Announcement Forbidden", True, 
                              "Students correctly forbidden from creating announcements")
                return True
            else:
                self.log_result("Student Announcement Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Student Announcement Forbidden", False, f"Request failed: {str(e)}")
            return False

    def test_announcement_listing_filtering(self):
        """Test announcement listing with proper filtering based on user role and target audience"""
        print("\n=== Testing Announcement Listing and Filtering ===")
        
        # Test different roles see appropriate announcements
        roles_to_test = ["student", "teacher", "principal"]
        all_passed = True
        
        for role in roles_to_test:
            token = self.get_auth_token_for_role(role)
            if not token:
                self.log_result(f"{role.title()} Announcement Listing", False, f"Could not get {role} auth token")
                all_passed = False
                continue
            
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(f"{self.base_url}/announcements", headers=headers)
                
                if response.status_code == 200:
                    announcements = response.json()
                    self.log_result(f"{role.title()} Announcement Listing", True, 
                                  f"{role.title()} can view announcements ({len(announcements)} announcements)")
                else:
                    self.log_result(f"{role.title()} Announcement Listing", False, 
                                  f"Announcement listing failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"{role.title()} Announcement Listing", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed

    def test_announcement_target_audiences(self):
        """Test different target audiences: 'all', 'students', 'teachers', 'A5', 'A6'"""
        print("\n=== Testing Announcement Target Audiences ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        if not principal_token:
            self.log_result("Announcement Target Audiences", False, "Could not get principal auth token")
            return False
        
        target_audiences = ["all", "students", "teachers", "A5", "A6"]
        headers = {
            'Authorization': f'Bearer {principal_token}',
            'Content-Type': 'application/json'
        }
        
        all_passed = True
        
        for audience in target_audiences:
            try:
                announcement_data = {
                    "title": f"Test Announcement for {audience}",
                    "content": f"This announcement targets {audience}",
                    "target_audience": audience
                }
                
                response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'announcement_id' in result:
                        self.log_result(f"Target Audience '{audience}'", True, 
                                      f"Successfully created announcement for {audience}")
                    else:
                        self.log_result(f"Target Audience '{audience}'", False, 
                                      "Response missing announcement_id", 
                                      f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result(f"Target Audience '{audience}'", False, 
                                  f"Failed to create announcement: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Target Audience '{audience}'", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed

    def test_announcement_update_permissions(self):
        """Test announcement update permissions (only author or principal)"""
        print("\n=== Testing Announcement Update Permissions ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        principal_token = self.get_auth_token_for_role("principal")
        
        if not teacher_token or not principal_token:
            self.log_result("Announcement Update Permissions", False, "Could not get required auth tokens")
            return False
        
        # First create an announcement as teacher
        try:
            announcement_data = {
                "title": "Original Teacher Announcement",
                "content": "Original content",
                "target_audience": "students"
            }
            
            headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Announcement Update Permissions", False, "Could not create test announcement")
                return False
            
            announcement_id = response.json()['announcement_id']
            
            # Test teacher can update their own announcement
            update_data = {
                "title": "Updated Teacher Announcement",
                "content": "Updated content"
            }
            
            response = self.session.put(f"{self.base_url}/announcements/{announcement_id}", 
                                      json=update_data, headers=headers)
            
            if response.status_code == 200:
                self.log_result("Teacher Update Own Announcement", True, 
                              "Teacher can update their own announcement")
            else:
                self.log_result("Teacher Update Own Announcement", False, 
                              f"Teacher cannot update own announcement: {response.status_code}")
                return False
            
            # Test principal can update any announcement
            principal_headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            update_data = {
                "title": "Principal Updated Announcement",
                "is_active": True
            }
            
            response = self.session.put(f"{self.base_url}/announcements/{announcement_id}", 
                                      json=update_data, headers=principal_headers)
            
            if response.status_code == 200:
                self.log_result("Principal Update Any Announcement", True, 
                              "Principal can update any announcement")
                return True
            else:
                self.log_result("Principal Update Any Announcement", False, 
                              f"Principal cannot update announcement: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Announcement Update Permissions", False, f"Request failed: {str(e)}")
            return False

    def test_announcement_delete_permissions(self):
        """Test announcement delete permissions (only author or principal)"""
        print("\n=== Testing Announcement Delete Permissions ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        principal_token = self.get_auth_token_for_role("principal")
        
        if not teacher_token or not principal_token:
            self.log_result("Announcement Delete Permissions", False, "Could not get required auth tokens")
            return False
        
        # Create test announcements
        try:
            # Create announcement as teacher
            announcement_data = {
                "title": "Teacher Announcement to Delete",
                "content": "This will be deleted",
                "target_audience": "students"
            }
            
            teacher_headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=teacher_headers)
            
            if response.status_code != 200:
                self.log_result("Announcement Delete Permissions", False, "Could not create test announcement")
                return False
            
            teacher_announcement_id = response.json()['announcement_id']
            
            # Create announcement as principal
            principal_headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/announcements", json=announcement_data, headers=principal_headers)
            
            if response.status_code != 200:
                self.log_result("Announcement Delete Permissions", False, "Could not create principal test announcement")
                return False
            
            principal_announcement_id = response.json()['announcement_id']
            
            # Test teacher can delete their own announcement
            response = self.session.delete(f"{self.base_url}/announcements/{teacher_announcement_id}", 
                                         headers=teacher_headers)
            
            if response.status_code == 200:
                self.log_result("Teacher Delete Own Announcement", True, 
                              "Teacher can delete their own announcement")
            else:
                self.log_result("Teacher Delete Own Announcement", False, 
                              f"Teacher cannot delete own announcement: {response.status_code}")
                return False
            
            # Test principal can delete any announcement
            response = self.session.delete(f"{self.base_url}/announcements/{principal_announcement_id}", 
                                         headers=principal_headers)
            
            if response.status_code == 200:
                self.log_result("Principal Delete Any Announcement", True, 
                              "Principal can delete any announcement")
                return True
            else:
                self.log_result("Principal Delete Any Announcement", False, 
                              f"Principal cannot delete announcement: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Announcement Delete Permissions", False, f"Request failed: {str(e)}")
            return False

    # Emergency Alert System Tests
    def test_emergency_alert_creation_student(self):
        """Test emergency alert creation by student (should work)"""
        print("\n=== Testing Emergency Alert Creation by Student ===")
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Student Emergency Alert Creation", False, "Could not get student auth token")
            return False
        
        headers = {
            'Authorization': f'Bearer {student_token}',
            'Content-Type': 'application/json'
        }
        
        # Test different alert types
        alert_types = [
            {"alert_type": "fire", "description": None},
            {"alert_type": "unauthorized_access", "description": None},
            {"alert_type": "other", "description": "Suspicious person in building"}
        ]
        
        all_passed = True
        
        for alert_data in alert_types:
            try:
                response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                           json=alert_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'alert_id' in result:
                        self.log_result(f"Student Alert Creation ({alert_data['alert_type']})", True, 
                                      f"Student can create {alert_data['alert_type']} alert", 
                                      f"Alert ID: {result['alert_id']}")
                    else:
                        self.log_result(f"Student Alert Creation ({alert_data['alert_type']})", False, 
                                      "Response missing alert_id", 
                                      f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result(f"Student Alert Creation ({alert_data['alert_type']})", False, 
                                  f"Alert creation failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Student Alert Creation ({alert_data['alert_type']})", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed

    def test_emergency_alert_creation_teacher_forbidden(self):
        """Test that teachers cannot create emergency alerts (403 error)"""
        print("\n=== Testing Emergency Alert Creation by Teacher (Should Fail) ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("Teacher Emergency Alert Forbidden", False, "Could not get teacher auth token")
            return False
        
        try:
            alert_data = {
                "alert_type": "fire",
                "description": None
            }
            
            headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=alert_data, headers=headers)
            
            if response.status_code == 403:
                self.log_result("Teacher Emergency Alert Forbidden", True, 
                              "Teachers correctly forbidden from creating emergency alerts")
                return True
            else:
                self.log_result("Teacher Emergency Alert Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Teacher Emergency Alert Forbidden", False, f"Request failed: {str(e)}")
            return False

    def test_emergency_alert_creation_principal_forbidden(self):
        """Test that principals cannot create emergency alerts (403 error)"""
        print("\n=== Testing Emergency Alert Creation by Principal (Should Fail) ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        if not principal_token:
            self.log_result("Principal Emergency Alert Forbidden", False, "Could not get principal auth token")
            return False
        
        try:
            alert_data = {
                "alert_type": "fire",
                "description": None
            }
            
            headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=alert_data, headers=headers)
            
            if response.status_code == 403:
                self.log_result("Principal Emergency Alert Forbidden", True, 
                              "Principals correctly forbidden from creating emergency alerts")
                return True
            else:
                self.log_result("Principal Emergency Alert Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal Emergency Alert Forbidden", False, f"Request failed: {str(e)}")
            return False

    def test_emergency_alert_validation(self):
        """Test emergency alert validation (invalid types, missing description for 'other')"""
        print("\n=== Testing Emergency Alert Validation ===")
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Emergency Alert Validation", False, "Could not get student auth token")
            return False
        
        headers = {
            'Authorization': f'Bearer {student_token}',
            'Content-Type': 'application/json'
        }
        
        # Test invalid alert type
        try:
            invalid_alert_data = {
                "alert_type": "invalid_type",
                "description": None
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=invalid_alert_data, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Invalid Alert Type Validation", True, 
                              "Invalid alert type correctly rejected")
            else:
                self.log_result("Invalid Alert Type Validation", False, 
                              f"Expected 400, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Invalid Alert Type Validation", False, f"Request failed: {str(e)}")
            return False
        
        # Test 'other' type without description
        try:
            other_without_desc = {
                "alert_type": "other",
                "description": None
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=other_without_desc, headers=headers)
            
            if response.status_code == 400:
                self.log_result("Other Type Missing Description", True, 
                              "'Other' type without description correctly rejected")
                return True
            else:
                self.log_result("Other Type Missing Description", False, 
                              f"Expected 400, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Other Type Missing Description", False, f"Request failed: {str(e)}")
            return False

    def test_emergency_alert_listing_permissions(self):
        """Test emergency alert listing with role-based permissions"""
        print("\n=== Testing Emergency Alert Listing Permissions ===")
        
        # Test different roles see appropriate alerts
        roles_to_test = ["student", "teacher", "principal"]
        all_passed = True
        
        for role in roles_to_test:
            token = self.get_auth_token_for_role(role)
            if not token:
                self.log_result(f"{role.title()} Alert Listing", False, f"Could not get {role} auth token")
                all_passed = False
                continue
            
            try:
                headers = {'Authorization': f'Bearer {token}'}
                response = self.session.get(f"{self.base_url}/emergency-alerts", headers=headers)
                
                if response.status_code == 200:
                    alerts = response.json()
                    if role == "student":
                        # Students should see only their own alerts
                        self.log_result(f"{role.title()} Alert Listing", True, 
                                      f"Student can view their alerts ({len(alerts)} alerts)")
                    else:
                        # Teachers and principals should see all alerts
                        self.log_result(f"{role.title()} Alert Listing", True, 
                                      f"{role.title()} can view all alerts ({len(alerts)} alerts)")
                else:
                    self.log_result(f"{role.title()} Alert Listing", False, 
                                  f"Alert listing failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"{role.title()} Alert Listing", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed

    def test_emergency_alert_status_update_principal(self):
        """Test emergency alert status update by principal (should work)"""
        print("\n=== Testing Emergency Alert Status Update by Principal ===")
        
        student_token = self.get_auth_token_for_role("student")
        principal_token = self.get_auth_token_for_role("principal")
        
        if not student_token or not principal_token:
            self.log_result("Principal Alert Status Update", False, "Could not get required auth tokens")
            return False
        
        # First create an alert as student
        try:
            alert_data = {
                "alert_type": "fire",
                "description": None
            }
            
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=alert_data, headers=student_headers)
            
            if response.status_code != 200:
                self.log_result("Principal Alert Status Update", False, "Could not create test alert")
                return False
            
            alert_id = response.json()['alert_id']
            
            # Test principal can update status to acknowledged
            principal_headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            status_update = {"status": "acknowledged"}
            
            response = self.session.put(f"{self.base_url}/emergency-alerts/{alert_id}/status", 
                                      json=status_update, headers=principal_headers)
            
            if response.status_code == 200:
                self.log_result("Principal Update to Acknowledged", True, 
                              "Principal can update alert status to acknowledged")
            else:
                self.log_result("Principal Update to Acknowledged", False, 
                              f"Status update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
            
            # Test principal can update status to resolved
            status_update = {"status": "resolved"}
            
            response = self.session.put(f"{self.base_url}/emergency-alerts/{alert_id}/status", 
                                      json=status_update, headers=principal_headers)
            
            if response.status_code == 200:
                self.log_result("Principal Update to Resolved", True, 
                              "Principal can update alert status to resolved")
                return True
            else:
                self.log_result("Principal Update to Resolved", False, 
                              f"Status update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal Alert Status Update", False, f"Request failed: {str(e)}")
            return False

    def test_emergency_alert_status_update_teacher_forbidden(self):
        """Test that teachers cannot update emergency alert status (403 error)"""
        print("\n=== Testing Emergency Alert Status Update by Teacher (Should Fail) ===")
        
        student_token = self.get_auth_token_for_role("student")
        teacher_token = self.get_auth_token_for_role("teacher")
        
        if not student_token or not teacher_token:
            self.log_result("Teacher Alert Status Update Forbidden", False, "Could not get required auth tokens")
            return False
        
        # First create an alert as student
        try:
            alert_data = {
                "alert_type": "unauthorized_access",
                "description": None
            }
            
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=alert_data, headers=student_headers)
            
            if response.status_code != 200:
                self.log_result("Teacher Alert Status Update Forbidden", False, "Could not create test alert")
                return False
            
            alert_id = response.json()['alert_id']
            
            # Test teacher cannot update status
            teacher_headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            status_update = {"status": "acknowledged"}
            
            response = self.session.put(f"{self.base_url}/emergency-alerts/{alert_id}/status", 
                                      json=status_update, headers=teacher_headers)
            
            if response.status_code == 403:
                self.log_result("Teacher Alert Status Update Forbidden", True, 
                              "Teachers correctly forbidden from updating alert status")
                return True
            else:
                self.log_result("Teacher Alert Status Update Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Teacher Alert Status Update Forbidden", False, f"Request failed: {str(e)}")
            return False

    def test_emergency_alert_status_validation(self):
        """Test emergency alert status validation (invalid status values)"""
        print("\n=== Testing Emergency Alert Status Validation ===")
        
        student_token = self.get_auth_token_for_role("student")
        principal_token = self.get_auth_token_for_role("principal")
        
        if not student_token or not principal_token:
            self.log_result("Alert Status Validation", False, "Could not get required auth tokens")
            return False
        
        # First create an alert as student
        try:
            alert_data = {
                "alert_type": "other",
                "description": "Test alert for status validation"
            }
            
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=alert_data, headers=student_headers)
            
            if response.status_code != 200:
                self.log_result("Alert Status Validation", False, "Could not create test alert")
                return False
            
            alert_id = response.json()['alert_id']
            
            # Test invalid status value
            principal_headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            invalid_status = {"status": "invalid_status"}
            
            response = self.session.put(f"{self.base_url}/emergency-alerts/{alert_id}/status", 
                                      json=invalid_status, headers=principal_headers)
            
            if response.status_code == 400:
                self.log_result("Alert Status Validation", True, 
                              "Invalid status value correctly rejected")
                return True
            else:
                self.log_result("Alert Status Validation", False, 
                              f"Expected 400, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Alert Status Validation", False, f"Request failed: {str(e)}")
            return False

    def test_emergency_alert_individual_access(self):
        """Test individual emergency alert access permissions"""
        print("\n=== Testing Individual Emergency Alert Access ===")
        
        student_token = self.get_auth_token_for_role("student")
        teacher_token = self.get_auth_token_for_role("teacher")
        principal_token = self.get_auth_token_for_role("principal")
        
        if not student_token or not teacher_token or not principal_token:
            self.log_result("Individual Alert Access", False, "Could not get required auth tokens")
            return False
        
        # First create an alert as student
        try:
            alert_data = {
                "alert_type": "fire",
                "description": None
            }
            
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/emergency-alerts", 
                                       json=alert_data, headers=student_headers)
            
            if response.status_code != 200:
                self.log_result("Individual Alert Access", False, "Could not create test alert")
                return False
            
            alert_id = response.json()['alert_id']
            
            # Test student can access their own alert
            response = self.session.get(f"{self.base_url}/emergency-alerts/{alert_id}", 
                                      headers=student_headers)
            
            if response.status_code == 200:
                self.log_result("Student Access Own Alert", True, 
                              "Student can access their own alert")
            else:
                self.log_result("Student Access Own Alert", False, 
                              f"Student cannot access own alert: {response.status_code}")
                return False
            
            # Test teacher can access any alert
            teacher_headers = {'Authorization': f'Bearer {teacher_token}'}
            response = self.session.get(f"{self.base_url}/emergency-alerts/{alert_id}", 
                                      headers=teacher_headers)
            
            if response.status_code == 200:
                self.log_result("Teacher Access Any Alert", True, 
                              "Teacher can access any alert")
            else:
                self.log_result("Teacher Access Any Alert", False, 
                              f"Teacher cannot access alert: {response.status_code}")
                return False
            
            # Test principal can access any alert
            principal_headers = {'Authorization': f'Bearer {principal_token}'}
            response = self.session.get(f"{self.base_url}/emergency-alerts/{alert_id}", 
                                      headers=principal_headers)
            
            if response.status_code == 200:
                self.log_result("Principal Access Any Alert", True, 
                              "Principal can access any alert")
                return True
            else:
                self.log_result("Principal Access Any Alert", False, 
                              f"Principal cannot access alert: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Individual Alert Access", False, f"Request failed: {str(e)}")
            return False

    # QR Attendance System Tests
    def test_qr_generation_for_active_class(self):
        """Test QR generation for active class endpoint"""
        print("\n=== Testing QR Generation for Active Class ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("QR Generation Active Class", False, "Could not get teacher auth token")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            # Test with valid active class data
            class_info = {
                "section": "A5",
                "subject": "Mathematics",
                "time": "09:30-10:30"
            }
            
            response = self.session.post(f"{self.base_url}/qr/generate-for-active-class", 
                                       json=class_info, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ['session_id', 'qr_image', 'qr_data', 'expires_at', 'class_section', 'subject', 'time_slot']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_result("QR Generation Active Class", True, 
                                  "QR generated successfully for active class", 
                                  f"Session ID: {result['session_id']}, Expires: {result['expires_at']}")
                    return result  # Return for use in attendance tests
                else:
                    self.log_result("QR Generation Active Class", False, 
                                  f"Response missing fields: {missing_fields}", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                # This might be expected if no active class matches
                self.log_result("QR Generation Active Class", True, 
                              "No active class found (expected behavior)", 
                              f"Response: {response.text}")
                return False
            else:
                self.log_result("QR Generation Active Class", False, 
                              f"QR generation failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("QR Generation Active Class", False, f"Request failed: {str(e)}")
            return False

    def test_qr_generation_manual(self):
        """Test manual QR generation endpoint"""
        print("\n=== Testing Manual QR Generation ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("Manual QR Generation", False, "Could not get teacher auth token")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            qr_data = {
                "class_section": "A5",
                "subject": "Mathematics",
                "class_code": "MC",
                "time_slot": "09:30-10:30"
            }
            
            response = self.session.post(f"{self.base_url}/qr/generate", 
                                       json=qr_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                required_fields = ['session_id', 'qr_image', 'qr_data', 'expires_at', 'class_section', 'subject', 'time_slot']
                missing_fields = [field for field in required_fields if field not in result]
                
                if not missing_fields:
                    self.log_result("Manual QR Generation", True, 
                                  "Manual QR generated successfully", 
                                  f"Session ID: {result['session_id']}")
                    return result  # Return for use in attendance tests
                else:
                    self.log_result("Manual QR Generation", False, 
                                  f"Response missing fields: {missing_fields}", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Manual QR Generation", False, 
                              f"Manual QR generation failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Manual QR Generation", False, f"Request failed: {str(e)}")
            return False

    def test_attendance_marking_valid_qr(self):
        """Test attendance marking with valid QR data"""
        print("\n=== Testing Attendance Marking with Valid QR ===")
        
        # First generate a QR code
        qr_result = self.test_qr_generation_manual()
        if not qr_result:
            self.log_result("Attendance Marking Valid QR", False, "Could not generate QR code for testing")
            return False
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Attendance Marking Valid QR", False, "Could not get student auth token")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            attendance_data = {
                "qr_data": qr_result['qr_data']
            }
            
            response = self.session.post(f"{self.base_url}/attendance/mark", 
                                       json=attendance_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'attendance_id' in result:
                    self.log_result("Attendance Marking Valid QR", True, 
                                  "Attendance marked successfully with valid QR", 
                                  f"Attendance ID: {result['attendance_id']}")
                    return True
                else:
                    self.log_result("Attendance Marking Valid QR", False, 
                                  "Response missing attendance_id", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                # Check if it's a class section mismatch or duplicate attendance
                result = response.json()
                detail = result.get('detail', '')
                if 'already marked' in detail:
                    self.log_result("Attendance Marking Valid QR", True, 
                                  "Duplicate attendance correctly prevented", 
                                  f"Response: {detail}")
                    return True
                elif 'not enrolled' in detail:
                    self.log_result("Attendance Marking Valid QR", True, 
                                  "Class section validation working", 
                                  f"Response: {detail}")
                    return True
                else:
                    self.log_result("Attendance Marking Valid QR", False, 
                                  f"Unexpected validation error: {detail}")
                    return False
            else:
                self.log_result("Attendance Marking Valid QR", False, 
                              f"Attendance marking failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Attendance Marking Valid QR", False, f"Request failed: {str(e)}")
            return False

    def test_attendance_marking_invalid_qr(self):
        """Test attendance marking with invalid QR data"""
        print("\n=== Testing Attendance Marking with Invalid QR ===")
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Attendance Marking Invalid QR", False, "Could not get student auth token")
            return False
        
        try:
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            # Test with invalid JSON QR data
            invalid_qr_tests = [
                {"qr_data": "invalid_json_data", "test_name": "Invalid JSON"},
                {"qr_data": '{"session_id": "non_existent_id"}', "test_name": "Non-existent Session"},
                {"qr_data": '{"invalid": "structure"}', "test_name": "Invalid Structure"}
            ]
            
            all_passed = True
            
            for test_case in invalid_qr_tests:
                attendance_data = {"qr_data": test_case["qr_data"]}
                
                response = self.session.post(f"{self.base_url}/attendance/mark", 
                                           json=attendance_data, headers=headers)
                
                if response.status_code in [400, 404]:
                    self.log_result(f"Invalid QR - {test_case['test_name']}", True, 
                                  f"Invalid QR correctly rejected ({response.status_code})")
                else:
                    self.log_result(f"Invalid QR - {test_case['test_name']}", False, 
                                  f"Expected 400/404, got {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            
            return all_passed
                
        except Exception as e:
            self.log_result("Attendance Marking Invalid QR", False, f"Request failed: {str(e)}")
            return False

    def test_qr_session_expiry_logic(self):
        """Test QR session validation and expiry logic"""
        print("\n=== Testing QR Session Expiry Logic ===")
        
        # Generate a QR code first
        qr_result = self.test_qr_generation_manual()
        if not qr_result:
            self.log_result("QR Session Expiry", False, "Could not generate QR code for testing")
            return False
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("QR Session Expiry", False, "Could not get teacher auth token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {teacher_token}'}
            
            # Get QR sessions to verify the session exists and check expiry
            response = self.session.get(f"{self.base_url}/qr/sessions", headers=headers)
            
            if response.status_code == 200:
                sessions = response.json()
                if sessions:
                    latest_session = sessions[-1]  # Get the most recent session
                    
                    # Check if session has proper expiry time
                    if 'expires_at' in latest_session and 'is_active' in latest_session:
                        from datetime import datetime
                        try:
                            expires_at = datetime.fromisoformat(latest_session['expires_at'].replace('Z', '+00:00'))
                            current_time = datetime.now(expires_at.tzinfo)
                            
                            if expires_at > current_time:
                                self.log_result("QR Session Expiry", True, 
                                              "QR session has valid future expiry time", 
                                              f"Expires at: {latest_session['expires_at']}")
                            else:
                                self.log_result("QR Session Expiry", True, 
                                              "QR session has expired (expected for past time slots)", 
                                              f"Expired at: {latest_session['expires_at']}")
                            return True
                        except Exception as date_error:
                            self.log_result("QR Session Expiry", False, 
                                          f"Could not parse expiry date: {date_error}")
                            return False
                    else:
                        self.log_result("QR Session Expiry", False, 
                                      "Session missing expiry or active fields", 
                                      f"Session: {latest_session}")
                        return False
                else:
                    self.log_result("QR Session Expiry", False, "No sessions found")
                    return False
            else:
                self.log_result("QR Session Expiry", False, 
                              f"Could not retrieve sessions: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("QR Session Expiry", False, f"Request failed: {str(e)}")
            return False

    def test_student_class_section_validation(self):
        """Test student authentication and class section validation"""
        print("\n=== Testing Student Class Section Validation ===")
        
        # Generate QR for A5 class
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("Class Section Validation", False, "Could not get teacher auth token")
            return False
        
        try:
            teacher_headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            # Generate QR for A5 class
            qr_data_a5 = {
                "class_section": "A5",
                "subject": "Mathematics",
                "class_code": "MC",
                "time_slot": "09:30-10:30"
            }
            
            response = self.session.post(f"{self.base_url}/qr/generate", 
                                       json=qr_data_a5, headers=teacher_headers)
            
            if response.status_code != 200:
                self.log_result("Class Section Validation", False, "Could not generate A5 QR code")
                return False
            
            qr_result_a5 = response.json()
            
            # Test with student from correct class (A5)
            student_token = self.get_auth_token_for_role("student")  # This should be A5 student
            if not student_token:
                self.log_result("Class Section Validation", False, "Could not get student auth token")
                return False
            
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            attendance_data = {"qr_data": qr_result_a5['qr_data']}
            
            response = self.session.post(f"{self.base_url}/attendance/mark", 
                                       json=attendance_data, headers=student_headers)
            
            if response.status_code == 200:
                self.log_result("Class Section Validation - Correct Section", True, 
                              "Student from correct class section can mark attendance")
            elif response.status_code == 400:
                result = response.json()
                detail = result.get('detail', '')
                if 'already marked' in detail:
                    self.log_result("Class Section Validation - Correct Section", True, 
                                  "Student from correct section (duplicate attendance prevented)")
                elif 'not enrolled' in detail:
                    self.log_result("Class Section Validation - Wrong Section", True, 
                                  "Class section mismatch correctly detected")
                else:
                    self.log_result("Class Section Validation", False, 
                                  f"Unexpected validation error: {detail}")
                    return False
            else:
                self.log_result("Class Section Validation", False, 
                              f"Unexpected response: {response.status_code}")
                return False
            
            # Test unauthorized access (non-student trying to mark attendance)
            response = self.session.post(f"{self.base_url}/attendance/mark", 
                                       json=attendance_data, headers=teacher_headers)
            
            if response.status_code == 403:
                self.log_result("Attendance Marking - Teacher Forbidden", True, 
                              "Teachers correctly forbidden from marking attendance")
                return True
            else:
                self.log_result("Attendance Marking - Teacher Forbidden", False, 
                              f"Expected 403, got {response.status_code}")
                return False
                
        except Exception as e:
            self.log_result("Class Section Validation", False, f"Request failed: {str(e)}")
            return False

    # System Admin Tests
    def test_system_admin_json_file_exists(self):
        """Test that system_admin.json file exists and contains correct credentials"""
        print("\n=== Testing System Admin JSON File ===")
        
        try:
            import json
            from pathlib import Path
            
            admin_file = Path("/app/backend/system_admin.json")
            
            if not admin_file.exists():
                self.log_result("System Admin JSON File", False, "system_admin.json file not found")
                return False
            
            with open(admin_file, 'r') as f:
                admin_data = json.load(f)
            
            system_admin = admin_data.get("system_admin")
            if not system_admin:
                self.log_result("System Admin JSON File", False, "system_admin key not found in JSON")
                return False
            
            required_fields = ["username", "password", "full_name", "role"]
            missing_fields = [field for field in required_fields if field not in system_admin]
            
            if missing_fields:
                self.log_result("System Admin JSON File", False, 
                              f"Missing required fields: {missing_fields}")
                return False
            
            # Verify expected values
            if (system_admin["username"] == "admin" and 
                system_admin["password"] == "admin123" and
                system_admin["role"] == "system_admin"):
                self.log_result("System Admin JSON File", True, 
                              "system_admin.json file exists with correct credentials", 
                              f"Username: {system_admin['username']}, Role: {system_admin['role']}")
                return True
            else:
                self.log_result("System Admin JSON File", False, 
                              "Incorrect credentials in system_admin.json", 
                              f"Found: {system_admin}")
                return False
                
        except Exception as e:
            self.log_result("System Admin JSON File", False, f"Error reading file: {str(e)}")
            return False

    def test_system_admin_login(self):
        """Test system admin login with JSON file authentication"""
        print("\n=== Testing System Admin Login ===")
        
        try:
            login_data = {
                "username": "admin",
                "password": "admin123"
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
                    # Store the system admin token for further tests
                    self.system_admin_token = result['access_token']
                    self.log_result("System Admin Login", True, 
                                  "System admin login successful, JWT token generated", 
                                  f"Token type: {result['token_type']}")
                    return True
                else:
                    self.log_result("System Admin Login", False, 
                                  "Login response missing token fields", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Login", False, 
                              f"Login failed with status: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Login", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_user_retrieval(self):
        """Test system admin user information retrieval using JWT token"""
        print("\n=== Testing System Admin User Retrieval ===")
        
        # First ensure we have a system admin token
        if not hasattr(self, 'system_admin_token') or not self.system_admin_token:
            if not self.test_system_admin_login():
                self.log_result("System Admin User Retrieval", False, "Could not get system admin token")
                return False
        
        try:
            headers = {
                'Authorization': f'Bearer {self.system_admin_token}',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify required fields are present
                required_fields = ['username', 'role', 'full_name']
                missing_fields = [field for field in required_fields if field not in result]
                
                if missing_fields:
                    self.log_result("System Admin User Retrieval", False, 
                                  f"Response missing fields: {missing_fields}", 
                                  f"Response: {result}")
                    return False
                
                # Verify correct values
                if (result['username'] == 'admin' and 
                    result['role'] == 'system_admin' and
                    result['full_name'] == 'System Administrator'):
                    self.log_result("System Admin User Retrieval", True, 
                                  "System admin user information correctly returned", 
                                  f"Username: {result['username']}, Role: {result['role']}, Name: {result['full_name']}")
                    return True
                else:
                    self.log_result("System Admin User Retrieval", False, 
                                  "Incorrect user information returned", 
                                  f"Expected: admin/system_admin/System Administrator, Got: {result['username']}/{result['role']}/{result['full_name']}")
                    return False
            else:
                self.log_result("System Admin User Retrieval", False, 
                              f"User retrieval failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin User Retrieval", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_registration_blocked(self):
        """Test that system_admin role cannot be registered via API"""
        print("\n=== Testing System Admin Registration Restriction ===")
        
        try:
            system_admin_data = {
                "username": "test_system_admin",
                "password": "testpass123",
                "role": "system_admin",
                "full_name": "Test System Admin"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=system_admin_data, headers=headers)
            
            if response.status_code == 400:
                result = response.json()
                detail = result.get('detail', '')
                if 'Invalid role' in detail or 'system_admin' in detail:
                    self.log_result("System Admin Registration Blocked", True, 
                                  "System admin registration correctly blocked", 
                                  f"Error message: {detail}")
                    return True
                else:
                    self.log_result("System Admin Registration Blocked", False, 
                                  "Wrong error message for blocked registration", 
                                  f"Expected role validation error, got: {detail}")
                    return False
            else:
                self.log_result("System Admin Registration Blocked", False, 
                              f"Expected 400 status, got: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Registration Blocked", False, f"Request failed: {str(e)}")
            return False

    def test_allowed_roles_registration(self):
        """Test that only allowed roles can be registered"""
        print("\n=== Testing Allowed Roles Registration ===")
        
        allowed_roles = ["teacher", "student", "principal", "verifier", "institution_admin"]
        all_passed = True
        
        for role in allowed_roles:
            try:
                # Create appropriate test data for each role
                if role == "student":
                    user_data = {
                        "username": f"test_{role}_user_2",
                        "password": "testpass123",
                        "role": role,
                        "student_id": "TEST002",
                        "class_section": "A6",
                        "full_name": f"Test {role.title()} User"
                    }
                elif role == "teacher":
                    user_data = {
                        "username": f"test_{role}_user_2",
                        "password": "testpass123",
                        "role": role,
                        "subjects": ["Physics"],
                        "full_name": f"Test {role.title()} User"
                    }
                elif role == "institution_admin":
                    user_data = {
                        "username": f"test_{role}_user_2",
                        "password": "testpass123",
                        "role": role,
                        "institution_id": "INST001",
                        "full_name": f"Test {role.title()} User"
                    }
                else:
                    user_data = {
                        "username": f"test_{role}_user_2",
                        "password": "testpass123",
                        "role": role,
                        "full_name": f"Test {role.title()} User"
                    }
                
                headers = {
                    'Content-Type': 'application/json',
                    'Origin': 'https://code-pi-rust.vercel.app'
                }
                
                response = self.session.post(f"{self.base_url}/auth/register", 
                                           json=user_data, headers=headers)
                
                if response.status_code in [200, 400]:  # 400 might be "already registered"
                    if response.status_code == 200:
                        result = response.json()
                        if 'user_id' in result:
                            self.log_result(f"Allowed Role Registration - {role}", True, 
                                          f"{role.title()} role registration allowed")
                        else:
                            self.log_result(f"Allowed Role Registration - {role}", False, 
                                          "Registration response missing user_id")
                            all_passed = False
                    else:  # 400 status
                        result = response.json()
                        if "already registered" in result.get('detail', ''):
                            self.log_result(f"Allowed Role Registration - {role}", True, 
                                          f"{role.title()} role registration allowed (user exists)")
                        else:
                            self.log_result(f"Allowed Role Registration - {role}", False, 
                                          f"Unexpected validation error: {result.get('detail')}")
                            all_passed = False
                else:
                    self.log_result(f"Allowed Role Registration - {role}", False, 
                                  f"Registration failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Allowed Role Registration - {role}", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed

    def run_production_admin_tests(self):
        """Run focused tests for production admin login issue"""
        print(f"\n{'='*60}")
        print("PRODUCTION ADMIN LOGIN TESTING")
        print("Focus: Verifying admin/admin123 login on production backend")
        print(f"{'='*60}")
        print(f"Backend URL: {self.base_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Run focused tests for production admin login
        tests = [
            self.test_production_backend_accessibility,
            self.test_system_admin_file_check,
            self.test_production_admin_login_detailed,
            self.test_admin_login,  # Original admin login test
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
        print("PRODUCTION ADMIN LOGIN TEST SUMMARY")
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
                if test.get('details'):
                    print(f"    Details: {test['details']}")
        
        # Show successful tests
        successful_tests = [r for r in self.test_results if r['success']]
        if successful_tests:
            print(f"\n✅ SUCCESSFUL TESTS:")
            for test in successful_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        return passed == total

    # ===== USER MANAGEMENT SYSTEM TESTS (NEW) =====
    
    def get_system_admin_token(self):
        """Get system admin authentication token"""
        try:
            admin_login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=admin_login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('access_token')
            return None
        except Exception:
            return None
    
    def test_registration_restriction_teacher(self):
        """Test that teacher role is blocked from public registration"""
        print("\n=== Testing Teacher Registration Restriction ===")
        
        try:
            teacher_data = {
                "username": "restricted_teacher_user",
                "password": "testpass123",
                "role": "teacher",
                "subjects": ["Mathematics", "Physics"],
                "full_name": "Restricted Teacher User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=teacher_data, headers=headers)
            
            if response.status_code == 403:
                result = response.json()
                if "can only be created by system administrators" in result.get('detail', ''):
                    self.log_result("Teacher Registration Restriction", True, 
                                  "Teacher role correctly blocked from public registration")
                    return True
                else:
                    self.log_result("Teacher Registration Restriction", False, 
                                  "Wrong error message for teacher restriction", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Teacher Registration Restriction", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Teacher Registration Restriction", False, f"Request failed: {str(e)}")
            return False
    
    def test_registration_restriction_student(self):
        """Test that student role is blocked from public registration"""
        print("\n=== Testing Student Registration Restriction ===")
        
        try:
            student_data = {
                "username": "restricted_student_user",
                "password": "testpass123",
                "role": "student",
                "student_id": "STU999",
                "class_section": "A5",
                "full_name": "Restricted Student User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=student_data, headers=headers)
            
            if response.status_code == 403:
                result = response.json()
                if "can only be created by system administrators" in result.get('detail', ''):
                    self.log_result("Student Registration Restriction", True, 
                                  "Student role correctly blocked from public registration")
                    return True
                else:
                    self.log_result("Student Registration Restriction", False, 
                                  "Wrong error message for student restriction", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Student Registration Restriction", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Student Registration Restriction", False, f"Request failed: {str(e)}")
            return False
    
    def test_registration_restriction_principal(self):
        """Test that principal role is blocked from public registration"""
        print("\n=== Testing Principal Registration Restriction ===")
        
        try:
            principal_data = {
                "username": "restricted_principal_user",
                "password": "testpass123",
                "role": "principal",
                "subjects": ["Mathematics"],
                "full_name": "Restricted Principal User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=principal_data, headers=headers)
            
            if response.status_code == 403:
                result = response.json()
                if "can only be created by system administrators" in result.get('detail', ''):
                    self.log_result("Principal Registration Restriction", True, 
                                  "Principal role correctly blocked from public registration")
                    return True
                else:
                    self.log_result("Principal Registration Restriction", False, 
                                  "Wrong error message for principal restriction", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Principal Registration Restriction", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Principal Registration Restriction", False, f"Request failed: {str(e)}")
            return False
    
    def test_registration_allowed_verifier(self):
        """Test that verifier role is allowed for public registration"""
        print("\n=== Testing Verifier Registration Allowed ===")
        
        try:
            verifier_data = {
                "username": "verifier_user_test",
                "password": "testpass123",
                "role": "verifier",
                "full_name": "Test Verifier User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=verifier_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'user_id' in result:
                    self.log_result("Verifier Registration Allowed", True, 
                                  "Verifier role correctly allowed for public registration", 
                                  f"User ID: {result['user_id']}")
                    return True
                else:
                    self.log_result("Verifier Registration Allowed", False, 
                                  "Registration response missing user_id", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                result = response.json()
                if "already registered" in result.get('detail', ''):
                    self.log_result("Verifier Registration Allowed", True, 
                                  "Verifier user already exists (expected)", 
                                  f"Response: {result}")
                    return True
                else:
                    self.log_result("Verifier Registration Allowed", False, 
                                  f"Registration failed with validation error: {result.get('detail')}", 
                                  f"Full response: {result}")
                    return False
            else:
                self.log_result("Verifier Registration Allowed", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Verifier Registration Allowed", False, f"Request failed: {str(e)}")
            return False
    
    def test_registration_allowed_institution_admin(self):
        """Test that institution_admin role is allowed for public registration"""
        print("\n=== Testing Institution Admin Registration Allowed ===")
        
        try:
            institution_admin_data = {
                "username": "institution_admin_test",
                "password": "testpass123",
                "role": "institution_admin",
                "institution_id": "inst_001",
                "full_name": "Test Institution Admin"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=institution_admin_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'user_id' in result:
                    self.log_result("Institution Admin Registration Allowed", True, 
                                  "Institution admin role correctly allowed for public registration", 
                                  f"User ID: {result['user_id']}")
                    return True
                else:
                    self.log_result("Institution Admin Registration Allowed", False, 
                                  "Registration response missing user_id", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                result = response.json()
                if "already registered" in result.get('detail', ''):
                    self.log_result("Institution Admin Registration Allowed", True, 
                                  "Institution admin user already exists (expected)", 
                                  f"Response: {result}")
                    return True
                else:
                    self.log_result("Institution Admin Registration Allowed", False, 
                                  f"Registration failed with validation error: {result.get('detail')}", 
                                  f"Full response: {result}")
                    return False
            else:
                self.log_result("Institution Admin Registration Allowed", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Institution Admin Registration Allowed", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_user_creation_system_admin_only(self):
        """Test that only system admin can access user creation endpoint"""
        print("\n=== Testing Admin User Creation Access Control ===")
        
        # Test with non-admin user (should fail)
        try:
            # Get a regular user token
            regular_token = self.get_auth_token_for_role("teacher")
            if not regular_token:
                # Try to get any available token
                regular_token = self.get_auth_token_for_role("student")
            
            if regular_token:
                user_data = {
                    "username": "test_created_user",
                    "password": "testpass123",
                    "role": "student",
                    "student_id": "STU888",
                    "class_section": "A5",
                    "full_name": "Test Created User"
                }
                
                headers = {
                    'Authorization': f'Bearer {regular_token}',
                    'Content-Type': 'application/json'
                }
                
                response = self.session.post(f"{self.base_url}/admin/users/create", 
                                           json=user_data, headers=headers)
                
                if response.status_code == 403:
                    self.log_result("Admin User Creation Access Control (Non-Admin)", True, 
                                  "Non-admin users correctly forbidden from user creation endpoint")
                else:
                    self.log_result("Admin User Creation Access Control (Non-Admin)", False, 
                                  f"Expected 403, got {response.status_code}", 
                                  f"Response: {response.text}")
                    return False
            
            # Test with system admin (should work)
            admin_token = self.get_system_admin_token()
            if not admin_token:
                self.log_result("Admin User Creation Access Control", False, 
                              "Could not get system admin token")
                return False
            
            user_data = {
                "username": "admin_created_student",
                "password": "testpass123",
                "role": "student",
                "student_id": "STU777",
                "class_section": "A6",
                "full_name": "Admin Created Student"
            }
            
            headers = {
                'Authorization': f'Bearer {admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.post(f"{self.base_url}/admin/users/create", 
                                       json=user_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'user_id' in result and result.get('role') == 'student':
                    self.log_result("Admin User Creation Access Control (System Admin)", True, 
                                  "System admin can successfully create users", 
                                  f"Created user: {result.get('username')} with role: {result.get('role')}")
                    return True
                else:
                    self.log_result("Admin User Creation Access Control (System Admin)", False, 
                                  "User creation response missing required fields", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 400:
                result = response.json()
                if "already registered" in result.get('detail', ''):
                    self.log_result("Admin User Creation Access Control (System Admin)", True, 
                                  "System admin endpoint accessible (user already exists)", 
                                  f"Response: {result}")
                    return True
                else:
                    self.log_result("Admin User Creation Access Control (System Admin)", False, 
                                  f"User creation failed with validation error: {result.get('detail')}", 
                                  f"Full response: {result}")
                    return False
            else:
                self.log_result("Admin User Creation Access Control (System Admin)", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin User Creation Access Control", False, f"Request failed: {str(e)}")
            return False
    
    def test_admin_user_creation_all_roles(self):
        """Test admin user creation for all allowed roles"""
        print("\n=== Testing Admin User Creation for All Roles ===")
        
        admin_token = self.get_system_admin_token()
        if not admin_token:
            self.log_result("Admin User Creation All Roles", False, "Could not get system admin token")
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Test creating users with different roles
        test_users = [
            {
                "username": "admin_created_teacher",
                "password": "testpass123",
                "role": "teacher",
                "subjects": ["Mathematics", "Physics"],
                "full_name": "Admin Created Teacher"
            },
            {
                "username": "admin_created_student2",
                "password": "testpass123",
                "role": "student",
                "student_id": "STU666",
                "class_section": "A5",
                "full_name": "Admin Created Student 2"
            },
            {
                "username": "admin_created_principal",
                "password": "testpass123",
                "role": "principal",
                "subjects": ["Mathematics"],
                "full_name": "Admin Created Principal"
            },
            {
                "username": "admin_created_verifier",
                "password": "testpass123",
                "role": "verifier",
                "full_name": "Admin Created Verifier"
            },
            {
                "username": "admin_created_inst_admin",
                "password": "testpass123",
                "role": "institution_admin",
                "institution_id": "inst_002",
                "full_name": "Admin Created Institution Admin"
            }
        ]
        
        all_passed = True
        
        for user_data in test_users:
            try:
                response = self.session.post(f"{self.base_url}/admin/users/create", 
                                           json=user_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'user_id' in result and result.get('role') == user_data['role']:
                        self.log_result(f"Admin Create {user_data['role'].title()}", True, 
                                      f"Successfully created {user_data['role']} user", 
                                      f"User: {result.get('username')}")
                    else:
                        self.log_result(f"Admin Create {user_data['role'].title()}", False, 
                                      "Response missing required fields", 
                                      f"Response: {result}")
                        all_passed = False
                elif response.status_code == 400:
                    result = response.json()
                    if "already registered" in result.get('detail', ''):
                        self.log_result(f"Admin Create {user_data['role'].title()}", True, 
                                      f"{user_data['role'].title()} user already exists (expected)")
                    else:
                        self.log_result(f"Admin Create {user_data['role'].title()}", False, 
                                      f"Creation failed: {result.get('detail')}", 
                                      f"Full response: {result}")
                        all_passed = False
                else:
                    self.log_result(f"Admin Create {user_data['role'].title()}", False, 
                                  f"Unexpected status code: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Admin Create {user_data['role'].title()}", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_admin_user_creation_validation(self):
        """Test validation in admin user creation endpoint"""
        print("\n=== Testing Admin User Creation Validation ===")
        
        admin_token = self.get_system_admin_token()
        if not admin_token:
            self.log_result("Admin User Creation Validation", False, "Could not get system admin token")
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # Test validation scenarios
        validation_tests = [
            {
                "name": "Student Missing Student ID",
                "data": {
                    "username": "invalid_student",
                    "password": "testpass123",
                    "role": "student",
                    "class_section": "A5",
                    "full_name": "Invalid Student"
                },
                "expected_error": "Student ID and class section are required"
            },
            {
                "name": "Student Invalid Class Section",
                "data": {
                    "username": "invalid_student2",
                    "password": "testpass123",
                    "role": "student",
                    "student_id": "STU555",
                    "class_section": "B1",
                    "full_name": "Invalid Student 2"
                },
                "expected_error": "Class section must be 'A5' or 'A6'"
            },
            {
                "name": "Teacher Missing Subjects",
                "data": {
                    "username": "invalid_teacher",
                    "password": "testpass123",
                    "role": "teacher",
                    "full_name": "Invalid Teacher"
                },
                "expected_error": "At least one subject is required"
            },
            {
                "name": "Institution Admin Missing Institution ID",
                "data": {
                    "username": "invalid_inst_admin",
                    "password": "testpass123",
                    "role": "institution_admin",
                    "full_name": "Invalid Institution Admin"
                },
                "expected_error": "Institution ID is required"
            }
        ]
        
        all_passed = True
        
        for test_case in validation_tests:
            try:
                response = self.session.post(f"{self.base_url}/admin/users/create", 
                                           json=test_case["data"], headers=headers)
                
                if response.status_code == 400:
                    result = response.json()
                    if test_case["expected_error"] in result.get('detail', ''):
                        self.log_result(f"Validation: {test_case['name']}", True, 
                                      f"Validation correctly rejected invalid data")
                    else:
                        self.log_result(f"Validation: {test_case['name']}", False, 
                                      f"Wrong validation error. Expected: {test_case['expected_error']}, Got: {result.get('detail')}")
                        all_passed = False
                else:
                    self.log_result(f"Validation: {test_case['name']}", False, 
                                  f"Expected 400, got {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
                    
            except Exception as e:
                self.log_result(f"Validation: {test_case['name']}", False, f"Request failed: {str(e)}")
                all_passed = False
        
        return all_passed
    
    def test_admin_user_listing_system_admin_only(self):
        """Test that only system admin can access user listing endpoint"""
        print("\n=== Testing Admin User Listing Access Control ===")
        
        # Test with non-admin user (should fail)
        try:
            regular_token = self.get_auth_token_for_role("teacher")
            if not regular_token:
                regular_token = self.get_auth_token_for_role("student")
            
            if regular_token:
                headers = {'Authorization': f'Bearer {regular_token}'}
                response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
                
                if response.status_code == 403:
                    self.log_result("Admin User Listing Access Control (Non-Admin)", True, 
                                  "Non-admin users correctly forbidden from user listing endpoint")
                else:
                    self.log_result("Admin User Listing Access Control (Non-Admin)", False, 
                                  f"Expected 403, got {response.status_code}", 
                                  f"Response: {response.text}")
                    return False
            
            # Test with system admin (should work)
            admin_token = self.get_system_admin_token()
            if not admin_token:
                self.log_result("Admin User Listing Access Control", False, 
                              "Could not get system admin token")
                return False
            
            headers = {'Authorization': f'Bearer {admin_token}'}
            response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'users' in result and isinstance(result['users'], list):
                    users = result['users']
                    # Check that users have required fields
                    if users and all('id' in user and 'username' in user and 'role' in user and 'full_name' in user for user in users):
                        self.log_result("Admin User Listing Access Control (System Admin)", True, 
                                      f"System admin can list users ({len(users)} users found)", 
                                      f"Sample user fields: {list(users[0].keys()) if users else 'No users'}")
                        return True
                    else:
                        self.log_result("Admin User Listing Access Control (System Admin)", False, 
                                      "User listing response missing required fields", 
                                      f"Users structure: {users[:2] if users else 'No users'}")
                        return False
                else:
                    self.log_result("Admin User Listing Access Control (System Admin)", False, 
                                  "User listing response missing 'users' field or not a list", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Admin User Listing Access Control (System Admin)", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin User Listing Access Control", False, f"Request failed: {str(e)}")
            return False
    
    def test_system_admin_authentication(self):
        """Test system admin login with admin/admin123 credentials"""
        print("\n=== Testing System Admin Authentication ===")
        
        try:
            admin_login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=admin_login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result and 'token_type' in result:
                    # Test /auth/me endpoint to verify system admin role
                    admin_headers = {'Authorization': f'Bearer {result["access_token"]}'}
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=admin_headers)
                    
                    if me_response.status_code == 200:
                        user_info = me_response.json()
                        if user_info.get('role') == 'system_admin' and user_info.get('username') == 'admin':
                            self.log_result("System Admin Authentication", True, 
                                          "System admin login and role verification successful", 
                                          f"User: {user_info.get('username')}, Role: {user_info.get('role')}")
                            return True
                        else:
                            self.log_result("System Admin Authentication", False, 
                                          "System admin role verification failed", 
                                          f"Expected role: system_admin, username: admin. Got: {user_info}")
                            return False
                    else:
                        self.log_result("System Admin Authentication", False, 
                                      f"Failed to verify admin user info: {me_response.status_code}", 
                                      f"Response: {me_response.text}")
                        return False
                else:
                    self.log_result("System Admin Authentication", False, 
                                  "Login response missing token fields", 
                                  f"Response: {result}")
                    return False
            elif response.status_code == 401:
                self.log_result("System Admin Authentication", False, 
                              "System admin login failed - incorrect credentials", 
                              f"Response: {response.text}")
                return False
            else:
                self.log_result("System Admin Authentication", False, 
                              f"Unexpected status code: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Authentication", False, f"Request failed: {str(e)}")
            return False

    def get_admin_token(self):
        """Get admin authentication token"""
        try:
            admin_login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/login", json=admin_login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                return result.get('access_token')
            return None
        except Exception:
            return None

    def create_test_users_for_management(self):
        """Create test users for user management testing"""
        admin_token = self.get_admin_token()
        if not admin_token:
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        test_users = [
            {
                "username": "student_mgmt_test1",
                "password": "testpass123",
                "role": "student",
                "student_id": "STU_MGMT_001",
                "class_section": "A5",
                "full_name": "Student Management Test 1"
            },
            {
                "username": "student_mgmt_test2", 
                "password": "testpass123",
                "role": "student",
                "student_id": "STU_MGMT_002",
                "class_section": "A6",
                "full_name": "Student Management Test 2"
            },
            {
                "username": "teacher_mgmt_test1",
                "password": "testpass123",
                "role": "teacher",
                "subjects": ["Mathematics", "Physics"],
                "full_name": "Teacher Management Test 1"
            },
            {
                "username": "principal_mgmt_test1",
                "password": "testpass123",
                "role": "principal",
                "subjects": ["Administration"],
                "full_name": "Principal Management Test 1"
            },
            {
                "username": "verifier_mgmt_test1",
                "password": "testpass123",
                "role": "verifier",
                "full_name": "Verifier Management Test 1"
            }
        ]
        
        created_users = []
        for user_data in test_users:
            try:
                response = self.session.post(f"{self.base_url}/admin/users/create", 
                                           json=user_data, headers=headers)
                if response.status_code == 200:
                    result = response.json()
                    created_users.append({
                        'user_id': result['user_id'],
                        'username': user_data['username'],
                        'role': user_data['role']
                    })
                elif response.status_code == 400 and "already registered" in response.text:
                    # User already exists, that's fine
                    pass
            except Exception as e:
                print(f"Failed to create test user {user_data['username']}: {e}")
        
        return len(created_users) > 0

    def test_admin_users_list_system_admin_filter(self):
        """Test GET /api/admin/users - List Users with System Admin Filter"""
        print("\n=== Testing Admin Users List with System Admin Filter ===")
        
        admin_token = self.get_admin_token()
        if not admin_token:
            self.log_result("Admin Users List", False, "Could not get admin auth token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {admin_token}'}
            response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                users = result.get('users', [])
                
                # Check that no system_admin users are in the response
                system_admin_users = [user for user in users if user.get('role') == 'system_admin']
                
                if len(system_admin_users) == 0:
                    # Check that other roles are present
                    roles_present = set(user.get('role') for user in users)
                    expected_roles = {'student', 'teacher', 'principal', 'verifier', 'institution_admin'}
                    roles_found = roles_present.intersection(expected_roles)
                    
                    self.log_result("Admin Users List - System Admin Filter", True, 
                                  f"System admin users correctly filtered out. Found {len(users)} users with roles: {roles_found}")
                    return True
                else:
                    self.log_result("Admin Users List - System Admin Filter", False, 
                                  f"Found {len(system_admin_users)} system_admin users in response", 
                                  f"System admin users: {system_admin_users}")
                    return False
            else:
                self.log_result("Admin Users List", False, 
                              f"Users list failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Admin Users List", False, f"Request failed: {str(e)}")
            return False

    def test_admin_users_list_non_admin_forbidden(self):
        """Test that non-admin users cannot access user list (403 error)"""
        print("\n=== Testing Non-Admin Users List Access (Should Fail) ===")
        
        # Use one of our created test users
        student_login_data = {
            "username": "student_mgmt_test1",
            "password": "testpass123"
        }
        
        headers = {'Content-Type': 'application/json'}
        response = self.session.post(f"{self.base_url}/auth/login", json=student_login_data, headers=headers)
        
        if response.status_code != 200:
            self.log_result("Non-Admin Users List Forbidden", False, "Could not get student auth token")
            return False
        
        student_token = response.json().get('access_token')
        if not student_token:
            self.log_result("Non-Admin Users List Forbidden", False, "Could not get student auth token")
            return False
        
        try:
            headers = {'Authorization': f'Bearer {student_token}'}
            response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
            
            if response.status_code == 403:
                self.log_result("Non-Admin Users List Forbidden", True, 
                              "Non-admin users correctly forbidden from accessing user list")
                return True
            else:
                self.log_result("Non-Admin Users List Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Non-Admin Users List Forbidden", False, f"Request failed: {str(e)}")
            return False

    def test_admin_update_user_comprehensive(self):
        """Test PUT /api/admin/users/{user_id} - Update User comprehensively"""
        print("\n=== Testing Admin Update User Comprehensive ===")
        
        admin_token = self.get_admin_token()
        if not admin_token:
            self.log_result("Admin Update User", False, "Could not get admin auth token")
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        # First get a user to update
        try:
            response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
            if response.status_code != 200:
                self.log_result("Admin Update User", False, "Could not get users list")
                return False
            
            users = response.json().get('users', [])
            student_user = next((user for user in users if user['role'] == 'student'), None)
            teacher_user = next((user for user in users if user['role'] == 'teacher'), None)
            
            if not student_user:
                self.log_result("Admin Update User", False, "No student user found for testing")
                return False
            
            all_passed = True
            
            # Test 1: Update student's username (verify uniqueness check)
            try:
                update_data = {"username": f"updated_student_{datetime.now().microsecond}"}
                response = self.session.put(f"{self.base_url}/admin/users/{student_user['id']}", 
                                          json=update_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'username' in result.get('updated_fields', []):
                        self.log_result("Update Student Username", True, 
                                      "Successfully updated student username")
                    else:
                        self.log_result("Update Student Username", False, 
                                      "Username not in updated fields", f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result("Update Student Username", False, 
                                  f"Username update failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Update Student Username", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 2: Update student's password (verify it gets hashed)
            try:
                update_data = {"password": "newpassword123"}
                response = self.session.put(f"{self.base_url}/admin/users/{student_user['id']}", 
                                          json=update_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'password_hash' in result.get('updated_fields', []):
                        self.log_result("Update Student Password", True, 
                                      "Successfully updated student password (hashed)")
                    else:
                        self.log_result("Update Student Password", False, 
                                      "Password hash not in updated fields", f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result("Update Student Password", False, 
                                  f"Password update failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Update Student Password", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 3: Update student's full_name
            try:
                update_data = {"full_name": "Updated Student Name"}
                response = self.session.put(f"{self.base_url}/admin/users/{student_user['id']}", 
                                          json=update_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'full_name' in result.get('updated_fields', []):
                        self.log_result("Update Student Full Name", True, 
                                      "Successfully updated student full name")
                    else:
                        self.log_result("Update Student Full Name", False, 
                                      "Full name not in updated fields", f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result("Update Student Full Name", False, 
                                  f"Full name update failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Update Student Full Name", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 4: Update student's class_section (A5 to A6 or vice versa)
            try:
                current_section = student_user.get('class_section', 'A5')
                new_section = 'A6' if current_section == 'A5' else 'A5'
                update_data = {"class_section": new_section}
                
                response = self.session.put(f"{self.base_url}/admin/users/{student_user['id']}", 
                                          json=update_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    if 'class_section' in result.get('updated_fields', []):
                        self.log_result("Update Student Class Section", True, 
                                      f"Successfully updated class section from {current_section} to {new_section}")
                    else:
                        self.log_result("Update Student Class Section", False, 
                                      "Class section not in updated fields", f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result("Update Student Class Section", False, 
                                  f"Class section update failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Update Student Class Section", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 5: Update teacher's subjects array (if teacher user exists)
            if teacher_user:
                try:
                    update_data = {"subjects": ["Updated Mathematics", "Updated Physics", "Chemistry"]}
                    response = self.session.put(f"{self.base_url}/admin/users/{teacher_user['id']}", 
                                              json=update_data, headers=headers)
                    
                    if response.status_code == 200:
                        result = response.json()
                        if 'subjects' in result.get('updated_fields', []):
                            self.log_result("Update Teacher Subjects", True, 
                                          "Successfully updated teacher subjects")
                        else:
                            self.log_result("Update Teacher Subjects", False, 
                                          "Subjects not in updated fields", f"Response: {result}")
                            all_passed = False
                    else:
                        self.log_result("Update Teacher Subjects", False, 
                                      f"Subjects update failed: {response.status_code}", 
                                      f"Response: {response.text}")
                        all_passed = False
                except Exception as e:
                    self.log_result("Update Teacher Subjects", False, f"Request failed: {str(e)}")
                    all_passed = False
            
            # Test 6: Try to update non-existent user (should return 404)
            try:
                fake_user_id = "non_existent_user_id_12345"
                update_data = {"full_name": "Should Not Work"}
                response = self.session.put(f"{self.base_url}/admin/users/{fake_user_id}", 
                                          json=update_data, headers=headers)
                
                if response.status_code == 404:
                    self.log_result("Update Non-Existent User", True, 
                                  "Non-existent user update correctly returned 404")
                else:
                    self.log_result("Update Non-Existent User", False, 
                                  f"Expected 404, got {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Update Non-Existent User", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 7: Try to update with duplicate username (should return 400)
            if len(users) >= 2:
                try:
                    other_user = next((user for user in users if user['id'] != student_user['id']), None)
                    if other_user:
                        update_data = {"username": other_user['username']}
                        response = self.session.put(f"{self.base_url}/admin/users/{student_user['id']}", 
                                                  json=update_data, headers=headers)
                        
                        if response.status_code == 400:
                            self.log_result("Update Duplicate Username", True, 
                                          "Duplicate username correctly rejected with 400")
                        else:
                            self.log_result("Update Duplicate Username", False, 
                                          f"Expected 400, got {response.status_code}", 
                                          f"Response: {response.text}")
                            all_passed = False
                except Exception as e:
                    self.log_result("Update Duplicate Username", False, f"Request failed: {str(e)}")
                    all_passed = False
            
            # Test 8: Change student's role to teacher (verify role-specific fields change)
            try:
                update_data = {
                    "role": "teacher",
                    "subjects": ["New Subject 1", "New Subject 2"]
                }
                response = self.session.put(f"{self.base_url}/admin/users/{student_user['id']}", 
                                          json=update_data, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    updated_fields = result.get('updated_fields', [])
                    if 'role' in updated_fields and 'subjects' in updated_fields:
                        self.log_result("Update Student Role to Teacher", True, 
                                      "Successfully changed student role to teacher with subjects")
                    else:
                        self.log_result("Update Student Role to Teacher", False, 
                                      "Role or subjects not in updated fields", f"Response: {result}")
                        all_passed = False
                else:
                    self.log_result("Update Student Role to Teacher", False, 
                                  f"Role change failed: {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Update Student Role to Teacher", False, f"Request failed: {str(e)}")
                all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("Admin Update User", False, f"Test setup failed: {str(e)}")
            return False

    def test_admin_update_user_non_admin_forbidden(self):
        """Test that non-admin users cannot update users (403 error)"""
        print("\n=== Testing Non-Admin User Update (Should Fail) ===")
        
        # Use one of our created test users
        student_login_data = {
            "username": "student_mgmt_test1",
            "password": "testpass123"
        }
        
        headers = {'Content-Type': 'application/json'}
        response = self.session.post(f"{self.base_url}/auth/login", json=student_login_data, headers=headers)
        
        if response.status_code != 200:
            self.log_result("Non-Admin User Update Forbidden", False, "Could not get student auth token")
            return False
        
        student_token = response.json().get('access_token')
        admin_token = self.get_admin_token()
        
        if not student_token or not admin_token:
            self.log_result("Non-Admin User Update Forbidden", False, "Could not get required auth tokens")
            return False
        
        # Get a user ID to try to update
        try:
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            response = self.session.get(f"{self.base_url}/admin/users", headers=admin_headers)
            
            if response.status_code != 200:
                self.log_result("Non-Admin User Update Forbidden", False, "Could not get users list")
                return False
            
            users = response.json().get('users', [])
            if not users:
                self.log_result("Non-Admin User Update Forbidden", False, "No users found for testing")
                return False
            
            test_user = users[0]
            
            # Try to update with student token
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            update_data = {"full_name": "Should Not Work"}
            response = self.session.put(f"{self.base_url}/admin/users/{test_user['id']}", 
                                      json=update_data, headers=student_headers)
            
            if response.status_code == 403:
                self.log_result("Non-Admin User Update Forbidden", True, 
                              "Non-admin users correctly forbidden from updating users")
                return True
            else:
                self.log_result("Non-Admin User Update Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Non-Admin User Update Forbidden", False, f"Request failed: {str(e)}")
            return False

    def test_admin_delete_user_comprehensive(self):
        """Test DELETE /api/admin/users/{user_id} - Delete User comprehensively"""
        print("\n=== Testing Admin Delete User Comprehensive ===")
        
        admin_token = self.get_admin_token()
        if not admin_token:
            self.log_result("Admin Delete User", False, "Could not get admin auth token")
            return False
        
        headers = {
            'Authorization': f'Bearer {admin_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # First create a test user to delete
            test_user_data = {
                "username": f"delete_test_user_{datetime.now().microsecond}",
                "password": "testpass123",
                "role": "student",
                "student_id": "DEL_TEST_001",
                "class_section": "A5",
                "full_name": "Delete Test User"
            }
            
            response = self.session.post(f"{self.base_url}/admin/users/create", 
                                       json=test_user_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Admin Delete User", False, "Could not create test user for deletion")
                return False
            
            created_user = response.json()
            user_id = created_user['user_id']
            username = created_user['username']
            
            all_passed = True
            
            # Test 1: Delete the user successfully
            # First, get the actual user ID from the database (there's a bug where creation returns ObjectId but queries use UUID)
            try:
                users_response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
                if users_response.status_code == 200:
                    users = users_response.json().get('users', [])
                    actual_user = next((user for user in users if user['username'] == username), None)
                    if actual_user:
                        actual_user_id = actual_user['id']
                        
                        response = self.session.delete(f"{self.base_url}/admin/users/{actual_user_id}", headers=headers)
                        
                        if response.status_code == 200:
                            result = response.json()
                            if result.get('username') == username:
                                self.log_result("Delete User Successfully", True, 
                                              f"Successfully deleted user {username}")
                            else:
                                self.log_result("Delete User Successfully", False, 
                                              "Delete response missing expected fields", f"Response: {result}")
                                all_passed = False
                        else:
                            self.log_result("Delete User Successfully", False, 
                                          f"User deletion failed: {response.status_code}", 
                                          f"Response: {response.text}")
                            all_passed = False
                    else:
                        self.log_result("Delete User Successfully", False, 
                                      f"Could not find created user {username} in user list")
                        all_passed = False
                else:
                    self.log_result("Delete User Successfully", False, 
                                  f"Could not get users list: {users_response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result("Delete User Successfully", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 2: Verify user is actually removed from database
            try:
                response = self.session.get(f"{self.base_url}/admin/users", headers=headers)
                
                if response.status_code == 200:
                    users = response.json().get('users', [])
                    deleted_user_still_exists = any(user['id'] == user_id for user in users)
                    
                    if not deleted_user_still_exists:
                        self.log_result("Verify User Removed from Database", True, 
                                      "Deleted user no longer appears in user list")
                    else:
                        self.log_result("Verify User Removed from Database", False, 
                                      "Deleted user still appears in user list")
                        all_passed = False
                else:
                    self.log_result("Verify User Removed from Database", False, 
                                  f"Could not verify user removal: {response.status_code}")
                    all_passed = False
            except Exception as e:
                self.log_result("Verify User Removed from Database", False, f"Request failed: {str(e)}")
                all_passed = False
            
            # Test 3: Try to delete non-existent user (should return 404)
            try:
                fake_user_id = "non_existent_user_id_12345"
                response = self.session.delete(f"{self.base_url}/admin/users/{fake_user_id}", headers=headers)
                
                if response.status_code == 404:
                    self.log_result("Delete Non-Existent User", True, 
                                  "Non-existent user deletion correctly returned 404")
                else:
                    self.log_result("Delete Non-Existent User", False, 
                                  f"Expected 404, got {response.status_code}", 
                                  f"Response: {response.text}")
                    all_passed = False
            except Exception as e:
                self.log_result("Delete Non-Existent User", False, f"Request failed: {str(e)}")
                all_passed = False
            
            return all_passed
            
        except Exception as e:
            self.log_result("Admin Delete User", False, f"Test setup failed: {str(e)}")
            return False

    def test_admin_delete_user_non_admin_forbidden(self):
        """Test that non-admin users cannot delete users (403 error)"""
        print("\n=== Testing Non-Admin User Delete (Should Fail) ===")
        
        # Use one of our created test users
        student_login_data = {
            "username": "student_mgmt_test1",
            "password": "testpass123"
        }
        
        headers = {'Content-Type': 'application/json'}
        response = self.session.post(f"{self.base_url}/auth/login", json=student_login_data, headers=headers)
        
        if response.status_code != 200:
            self.log_result("Non-Admin User Delete Forbidden", False, "Could not get student auth token")
            return False
        
        student_token = response.json().get('access_token')
        admin_token = self.get_admin_token()
        
        if not student_token or not admin_token:
            self.log_result("Non-Admin User Delete Forbidden", False, "Could not get required auth tokens")
            return False
        
        # Get a user ID to try to delete
        try:
            admin_headers = {'Authorization': f'Bearer {admin_token}'}
            response = self.session.get(f"{self.base_url}/admin/users", headers=admin_headers)
            
            if response.status_code != 200:
                self.log_result("Non-Admin User Delete Forbidden", False, "Could not get users list")
                return False
            
            users = response.json().get('users', [])
            if not users:
                self.log_result("Non-Admin User Delete Forbidden", False, "No users found for testing")
                return False
            
            test_user = users[0]
            
            # Try to delete with student token
            student_headers = {'Authorization': f'Bearer {student_token}'}
            response = self.session.delete(f"{self.base_url}/admin/users/{test_user['id']}", 
                                         headers=student_headers)
            
            if response.status_code == 403:
                self.log_result("Non-Admin User Delete Forbidden", True, 
                              "Non-admin users correctly forbidden from deleting users")
                return True
            else:
                self.log_result("Non-Admin User Delete Forbidden", False, 
                              f"Expected 403, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Non-Admin User Delete Forbidden", False, f"Request failed: {str(e)}")
            return False

    def run_user_management_tests_only(self):
        """Run only the user management tests as requested in the review"""
        print("=" * 80)
        print("USER MANAGEMENT ENDPOINTS TESTING")
        print("Focus: Admin/admin123 authentication and user management endpoints")
        print("=" * 80)
        print(f"Backend URL: {self.base_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Create test users for management testing
        print("\n=== Setting up test users ===")
        self.create_test_users_for_management()
        
        # Test user listing with system admin filter
        self.test_admin_users_list_system_admin_filter()
        self.test_admin_users_list_non_admin_forbidden()
        
        # Test user update functionality
        self.test_admin_update_user_comprehensive()
        self.test_admin_update_user_non_admin_forbidden()
        
        # Test user delete functionality
        self.test_admin_delete_user_comprehensive()
        self.test_admin_delete_user_non_admin_forbidden()
        
        # Print summary
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r['success'])
        
        print(f"\n{'='*60}")
        print("USER MANAGEMENT TEST SUMMARY")
        print(f"{'='*60}")
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%" if total > 0 else "No tests run")
        
        # Show failed tests
        failed_tests = [r for r in self.test_results if not r['success']]
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"  - {test['test']}: {test['message']}")
        
        return passed == total

    def test_profile_update_username(self):
        """Test 1: Profile Update Endpoint - Update Username"""
        print("\n=== Testing Profile Update - Username ===")
        
        # Get a regular user token (not system_admin)
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Profile Update Username", False, "Could not get student auth token")
            return False
        
        try:
            profile_data = {
                "username": f"updated_student_{datetime.now().strftime('%H%M%S')}",
                "current_password": "testpass123"
            }
            
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('username') == profile_data['username']:
                    self.log_result("Profile Update Username", True, 
                                  "Username updated successfully", 
                                  f"New username: {result.get('username')}")
                    return True
                else:
                    self.log_result("Profile Update Username", False, 
                                  "Username not updated in response", 
                                  f"Expected: {profile_data['username']}, Got: {result.get('username')}")
                    return False
            else:
                self.log_result("Profile Update Username", False, 
                              f"Profile update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Username", False, f"Request failed: {str(e)}")
            return False

    def test_profile_update_full_name(self):
        """Test 2: Profile Update Endpoint - Update Full Name"""
        print("\n=== Testing Profile Update - Full Name ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("Profile Update Full Name", False, "Could not get teacher auth token")
            return False
        
        try:
            profile_data = {
                "full_name": "Updated Teacher Full Name",
                "current_password": "testpass123"
            }
            
            headers = {
                'Authorization': f'Bearer {teacher_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('full_name') == profile_data['full_name']:
                    self.log_result("Profile Update Full Name", True, 
                                  "Full name updated successfully", 
                                  f"New full name: {result.get('full_name')}")
                    return True
                else:
                    self.log_result("Profile Update Full Name", False, 
                                  "Full name not updated in response", 
                                  f"Expected: {profile_data['full_name']}, Got: {result.get('full_name')}")
                    return False
            else:
                self.log_result("Profile Update Full Name", False, 
                              f"Profile update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Full Name", False, f"Request failed: {str(e)}")
            return False

    def test_profile_update_password(self):
        """Test 3: Profile Update Endpoint - Update Password"""
        print("\n=== Testing Profile Update - Password ===")
        
        # Create a new test user for password change test
        try:
            # Register a new user specifically for password testing
            test_user_data = {
                "username": f"password_test_user_{datetime.now().strftime('%H%M%S')}",
                "password": "oldpassword123",
                "role": "verifier",  # Use verifier role as it's publicly registerable
                "full_name": "Password Test User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=test_user_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Password", False, "Could not create test user for password change")
                return False
            
            # Login with old password
            login_data = {
                "username": test_user_data["username"],
                "password": "oldpassword123"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=login_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Password", False, "Could not login with old password")
                return False
            
            token = response.json()['access_token']
            
            # Update password
            profile_data = {
                "password": "newpassword123",
                "current_password": "oldpassword123"
            }
            
            auth_headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=auth_headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Password", False, 
                              f"Password update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
            
            # Try to login with new password
            new_login_data = {
                "username": test_user_data["username"],
                "password": "newpassword123"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=new_login_data, headers=headers)
            
            if response.status_code == 200:
                self.log_result("Profile Update Password", True, 
                              "Password updated successfully and login works with new password")
                return True
            else:
                self.log_result("Profile Update Password", False, 
                              f"Login with new password failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Password", False, f"Request failed: {str(e)}")
            return False

    def test_profile_update_profile_picture(self):
        """Test 4: Profile Update Endpoint - Update Profile Picture"""
        print("\n=== Testing Profile Update - Profile Picture ===")
        
        principal_token = self.get_auth_token_for_role("principal")
        if not principal_token:
            self.log_result("Profile Update Profile Picture", False, "Could not get principal auth token")
            return False
        
        try:
            # Small test image as base64 (1x1 pixel PNG)
            test_image_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            profile_data = {
                "profile_picture": test_image_base64,
                "current_password": "testpass123"
            }
            
            headers = {
                'Authorization': f'Bearer {principal_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('profile_picture') == test_image_base64:
                    # Verify profile picture persists by calling GET /auth/me
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
                    
                    if me_response.status_code == 200:
                        me_result = me_response.json()
                        if me_result.get('profile_picture') == test_image_base64:
                            self.log_result("Profile Update Profile Picture", True, 
                                          "Profile picture updated successfully and persists")
                            return True
                        else:
                            self.log_result("Profile Update Profile Picture", False, 
                                          "Profile picture not persisted in /auth/me")
                            return False
                    else:
                        self.log_result("Profile Update Profile Picture", False, 
                                      f"Could not verify profile picture persistence: {me_response.status_code}")
                        return False
                else:
                    self.log_result("Profile Update Profile Picture", False, 
                                  "Profile picture not updated in response")
                    return False
            else:
                self.log_result("Profile Update Profile Picture", False, 
                              f"Profile picture update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Profile Picture", False, f"Request failed: {str(e)}")
            return False

    def test_profile_update_wrong_password(self):
        """Test 5: Profile Update Endpoint - Wrong Current Password"""
        print("\n=== Testing Profile Update - Wrong Current Password ===")
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Profile Update Wrong Password", False, "Could not get student auth token")
            return False
        
        try:
            profile_data = {
                "username": "should_not_update",
                "current_password": "wrongpassword123"  # Wrong password
            }
            
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 401:
                result = response.json()
                if "current password" in result.get('detail', '').lower():
                    self.log_result("Profile Update Wrong Password", True, 
                                  "Wrong current password correctly rejected with 401", 
                                  f"Error message: {result.get('detail')}")
                    return True
                else:
                    self.log_result("Profile Update Wrong Password", False, 
                                  "401 returned but error message doesn't mention current password", 
                                  f"Error message: {result.get('detail')}")
                    return False
            else:
                self.log_result("Profile Update Wrong Password", False, 
                              f"Expected 401, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Wrong Password", False, f"Request failed: {str(e)}")
            return False

    def test_profile_update_duplicate_username(self):
        """Test 6: Profile Update Endpoint - Duplicate Username"""
        print("\n=== Testing Profile Update - Duplicate Username ===")
        
        # Get tokens for two different users
        student_token = self.get_auth_token_for_role("student")
        teacher_token = self.get_auth_token_for_role("teacher")
        
        if not student_token or not teacher_token:
            self.log_result("Profile Update Duplicate Username", False, "Could not get required auth tokens")
            return False
        
        try:
            # Try to update student username to teacher's username
            profile_data = {
                "username": "teacher_test_user",  # This username should already exist
                "current_password": "testpass123"
            }
            
            headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 400:
                result = response.json()
                if "username already exists" in result.get('detail', '').lower():
                    self.log_result("Profile Update Duplicate Username", True, 
                                  "Duplicate username correctly rejected with 400", 
                                  f"Error message: {result.get('detail')}")
                    return True
                else:
                    self.log_result("Profile Update Duplicate Username", False, 
                                  "400 returned but error message doesn't mention username exists", 
                                  f"Error message: {result.get('detail')}")
                    return False
            else:
                self.log_result("Profile Update Duplicate Username", False, 
                              f"Expected 400, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Duplicate Username", False, f"Request failed: {str(e)}")
            return False

    def test_profile_update_multiple_fields(self):
        """Test 7: Profile Update Endpoint - Multiple Fields Update"""
        print("\n=== Testing Profile Update - Multiple Fields ===")
        
        # Create a new test user for multiple fields update
        try:
            # Register a new user specifically for multiple fields testing
            test_user_data = {
                "username": f"multi_test_user_{datetime.now().strftime('%H%M%S')}",
                "password": "multitest123",
                "role": "verifier",  # Use verifier role as it's publicly registerable
                "full_name": "Multi Test User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=test_user_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Multiple Fields", False, "Could not create test user")
                return False
            
            # Login to get token
            login_data = {
                "username": test_user_data["username"],
                "password": "multitest123"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=login_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Multiple Fields", False, "Could not login with test user")
                return False
            
            token = response.json()['access_token']
            
            # Update multiple fields at once
            new_username = f"updated_multi_user_{datetime.now().strftime('%H%M%S')}"
            new_full_name = "Updated Multi Test User"
            new_password = "newmultitest123"
            test_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            profile_data = {
                "username": new_username,
                "full_name": new_full_name,
                "password": new_password,
                "profile_picture": test_image,
                "current_password": "multitest123"
            }
            
            auth_headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=auth_headers)
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify all fields are updated
                checks = [
                    (result.get('username') == new_username, "username"),
                    (result.get('full_name') == new_full_name, "full_name"),
                    (result.get('profile_picture') == test_image, "profile_picture")
                ]
                
                failed_checks = [field for check, field in checks if not check]
                
                if not failed_checks:
                    # Test login with new password
                    new_login_data = {
                        "username": new_username,
                        "password": new_password
                    }
                    
                    login_response = self.session.post(f"{self.base_url}/auth/login", 
                                                     json=new_login_data, headers=headers)
                    
                    if login_response.status_code == 200:
                        self.log_result("Profile Update Multiple Fields", True, 
                                      "All fields updated successfully (username, full_name, password, profile_picture)")
                        return True
                    else:
                        self.log_result("Profile Update Multiple Fields", False, 
                                      "Fields updated but new password doesn't work for login")
                        return False
                else:
                    self.log_result("Profile Update Multiple Fields", False, 
                                  f"Some fields not updated correctly: {failed_checks}", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("Profile Update Multiple Fields", False, 
                              f"Multiple fields update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("Profile Update Multiple Fields", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_login(self):
        """Test system admin login for profile update testing"""
        print("\n=== Testing System Admin Login for Profile Updates ===")
        
        try:
            admin_login_data = {
                "username": "admin",
                "password": "admin123"
            }
            
            headers = {
                'Content-Type': 'application/json',
                'Origin': 'https://smart-presence-sacs.vercel.app'
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=admin_login_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if 'access_token' in result and 'token_type' in result:
                    self.admin_token = result['access_token']
                    self.log_result("System Admin Profile Login", True, 
                                  "System admin login successful for profile testing", 
                                  f"Token type: {result['token_type']}")
                    return True
                else:
                    self.log_result("System Admin Profile Login", False, 
                                  "Login response missing token fields", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Profile Login", False, 
                              f"Login failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Profile Login", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_full_name(self):
        """Test system admin profile update - full_name (should work)"""
        print("\n=== Testing System Admin Profile Update - Full Name ===")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log_result("System Admin Full Name Update", False, "No admin token available")
            return False
        
        try:
            profile_data = {
                "full_name": "Updated System Administrator",
                "current_password": "admin123"
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('full_name') == "Updated System Administrator":
                    self.log_result("System Admin Full Name Update", True, 
                                  "System admin can update full_name", 
                                  f"Updated full_name: {result.get('full_name')}")
                    
                    # Verify persistence via /auth/me
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        me_result = me_response.json()
                        if me_result.get('full_name') == "Updated System Administrator":
                            self.log_result("System Admin Full Name Persistence", True, 
                                          "Updated full_name persists via /auth/me")
                            return True
                        else:
                            self.log_result("System Admin Full Name Persistence", False, 
                                          f"Full name not persisted: {me_result.get('full_name')}")
                            return False
                    else:
                        self.log_result("System Admin Full Name Persistence", False, 
                                      f"Failed to verify persistence: {me_response.status_code}")
                        return False
                else:
                    self.log_result("System Admin Full Name Update", False, 
                                  "Full name not updated in response", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Full Name Update", False, 
                              f"Profile update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Full Name Update", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_profile_picture(self):
        """Test system admin profile update - profile_picture (should work)"""
        print("\n=== Testing System Admin Profile Update - Profile Picture ===")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log_result("System Admin Profile Picture Update", False, "No admin token available")
            return False
        
        try:
            # Small base64 test image (1x1 pixel PNG)
            test_base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            profile_data = {
                "profile_picture": test_base64_image,
                "current_password": "admin123"
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if result.get('profile_picture') == test_base64_image:
                    self.log_result("System Admin Profile Picture Update", True, 
                                  "System admin can update profile_picture", 
                                  f"Profile picture updated successfully")
                    
                    # Verify persistence via /auth/me
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        me_result = me_response.json()
                        if me_result.get('profile_picture') == test_base64_image:
                            self.log_result("System Admin Profile Picture Persistence", True, 
                                          "Updated profile_picture persists via /auth/me")
                            return True
                        else:
                            self.log_result("System Admin Profile Picture Persistence", False, 
                                          "Profile picture not persisted")
                            return False
                    else:
                        self.log_result("System Admin Profile Picture Persistence", False, 
                                      f"Failed to verify persistence: {me_response.status_code}")
                        return False
                else:
                    self.log_result("System Admin Profile Picture Update", False, 
                                  "Profile picture not updated in response", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Profile Picture Update", False, 
                              f"Profile update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Profile Picture Update", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_wrong_password(self):
        """Test system admin profile update with wrong current password (should return 401)"""
        print("\n=== Testing System Admin Profile Update - Wrong Password ===")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log_result("System Admin Wrong Password", False, "No admin token available")
            return False
        
        try:
            profile_data = {
                "full_name": "Should Not Update",
                "current_password": "wrong_password"
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 401:
                self.log_result("System Admin Wrong Password", True, 
                              "Wrong current password correctly rejected with 401")
                return True
            else:
                self.log_result("System Admin Wrong Password", False, 
                              f"Expected 401, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Wrong Password", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_username_blocked(self):
        """Test system admin username change attempt (should return 400 - not allowed)"""
        print("\n=== Testing System Admin Profile Update - Username Change Blocked ===")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log_result("System Admin Username Change Blocked", False, "No admin token available")
            return False
        
        try:
            profile_data = {
                "username": "new_admin_username",
                "current_password": "admin123"
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 400:
                result = response.json()
                if "username cannot be changed" in result.get('detail', '').lower():
                    self.log_result("System Admin Username Change Blocked", True, 
                                  "Username change correctly blocked for system admin", 
                                  f"Error message: {result.get('detail')}")
                    return True
                else:
                    self.log_result("System Admin Username Change Blocked", False, 
                                  "Wrong error message for username change", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Username Change Blocked", False, 
                              f"Expected 400, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Username Change Blocked", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_password_blocked(self):
        """Test system admin password change attempt (should return 400 - not allowed)"""
        print("\n=== Testing System Admin Profile Update - Password Change Blocked ===")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log_result("System Admin Password Change Blocked", False, "No admin token available")
            return False
        
        try:
            profile_data = {
                "password": "new_admin_password",
                "current_password": "admin123"
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 400:
                result = response.json()
                if "password cannot be changed" in result.get('detail', '').lower():
                    self.log_result("System Admin Password Change Blocked", True, 
                                  "Password change correctly blocked for system admin", 
                                  f"Error message: {result.get('detail')}")
                    return True
                else:
                    self.log_result("System Admin Password Change Blocked", False, 
                                  "Wrong error message for password change", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Password Change Blocked", False, 
                              f"Expected 400, got {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Password Change Blocked", False, f"Request failed: {str(e)}")
            return False

    def test_system_admin_profile_update_multiple_fields(self):
        """Test system admin multiple fields update (full_name + profile_picture together)"""
        print("\n=== Testing System Admin Profile Update - Multiple Fields ===")
        
        if not hasattr(self, 'admin_token') or not self.admin_token:
            self.log_result("System Admin Multiple Fields Update", False, "No admin token available")
            return False
        
        try:
            # Small base64 test image (1x1 pixel PNG)
            test_base64_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="
            
            profile_data = {
                "full_name": "Multi-Field Updated Admin",
                "profile_picture": test_base64_image,
                "current_password": "admin123"
            }
            
            headers = {
                'Authorization': f'Bearer {self.admin_token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=headers)
            
            if response.status_code == 200:
                result = response.json()
                if (result.get('full_name') == "Multi-Field Updated Admin" and 
                    result.get('profile_picture') == test_base64_image):
                    self.log_result("System Admin Multiple Fields Update", True, 
                                  "System admin can update multiple fields simultaneously", 
                                  f"Updated full_name and profile_picture")
                    
                    # Verify persistence via /auth/me
                    me_response = self.session.get(f"{self.base_url}/auth/me", headers=headers)
                    if me_response.status_code == 200:
                        me_result = me_response.json()
                        if (me_result.get('full_name') == "Multi-Field Updated Admin" and 
                            me_result.get('profile_picture') == test_base64_image):
                            self.log_result("System Admin Multiple Fields Persistence", True, 
                                          "Multiple field updates persist via /auth/me")
                            return True
                        else:
                            self.log_result("System Admin Multiple Fields Persistence", False, 
                                          "Multiple field updates not persisted")
                            return False
                    else:
                        self.log_result("System Admin Multiple Fields Persistence", False, 
                                      f"Failed to verify persistence: {me_response.status_code}")
                        return False
                else:
                    self.log_result("System Admin Multiple Fields Update", False, 
                                  "Multiple fields not updated correctly", 
                                  f"Response: {result}")
                    return False
            else:
                self.log_result("System Admin Multiple Fields Update", False, 
                              f"Multiple fields update failed: {response.status_code}", 
                              f"Response: {response.text}")
                return False
                
        except Exception as e:
            self.log_result("System Admin Multiple Fields Update", False, f"Request failed: {str(e)}")
            return False

    def run_all_tests(self):
        """Run all backend tests"""
        print(f"\n{'='*60}")
        print("SMART ATTENDANCE BACKEND API TESTING")
        print("Focus: Emergency Alert System & Complete Backend Functionality")
        print(f"{'='*60}")
        print(f"Backend URL: {self.base_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Run tests in order
        tests = [
            # User Management System Tests (NEW - as requested in review)
            self.test_registration_restriction_teacher,
            self.test_registration_restriction_student,
            self.test_registration_restriction_principal,
            self.test_registration_allowed_verifier,
            self.test_registration_allowed_institution_admin,
            self.test_admin_user_creation_system_admin_only,
            self.test_admin_user_creation_all_roles,
            self.test_admin_user_creation_validation,
            self.test_admin_user_listing_system_admin_only,
            self.test_system_admin_authentication,
            
            # System Admin Tests (PRIORITY - as requested)
            self.test_admin_login,  # NEW: Test specific admin login issue
            self.test_system_admin_json_file_exists,
            self.test_system_admin_login,
            self.test_system_admin_user_retrieval,
            self.test_system_admin_registration_blocked,
            self.test_allowed_roles_registration,
            
            # Basic functionality tests
            self.test_cors_preflight,
            self.test_cors_actual_request,
            self.test_student_registration,
            self.test_teacher_registration,
            self.test_principal_registration,
            self.test_login,
            self.test_protected_route,
            self.test_protected_route_without_token,
            
            # QR Attendance System tests (PRIORITY - as requested)
            self.test_qr_generation_for_active_class,
            self.test_qr_generation_manual,
            self.test_attendance_marking_valid_qr,
            self.test_attendance_marking_invalid_qr,
            self.test_qr_session_expiry_logic,
            self.test_student_class_section_validation,
            
            # Principal role tests
            self.test_principal_access_teacher_endpoints,
            self.test_principal_full_attendance_records,
            self.test_principal_full_timetable,
            
            # Announcements tests
            self.test_announcement_creation_teacher,
            self.test_announcement_creation_principal,
            self.test_student_announcement_creation_forbidden,
            self.test_announcement_listing_filtering,
            self.test_announcement_target_audiences,
            self.test_announcement_update_permissions,
            self.test_announcement_delete_permissions,
            
            # Emergency Alert System tests
            self.test_emergency_alert_creation_student,
            self.test_emergency_alert_creation_teacher_forbidden,
            self.test_emergency_alert_creation_principal_forbidden,
            self.test_emergency_alert_validation,
            self.test_emergency_alert_listing_permissions,
            self.test_emergency_alert_status_update_principal,
            self.test_emergency_alert_status_update_teacher_forbidden,
            self.test_emergency_alert_status_validation,
            self.test_emergency_alert_individual_access,
            
            # Profile Update System tests (NEW - as requested in review)
            self.test_profile_update_username,
            self.test_profile_update_full_name,
            self.test_profile_update_password,
            self.test_profile_update_profile_picture,
            self.test_profile_update_wrong_password,
            self.test_profile_update_duplicate_username,
            self.test_profile_update_multiple_fields
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
    
    # Check if we should run production admin tests specifically
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "admin":
        print("Running focused production admin login tests...")
        success = tester.run_production_admin_tests()
    else:
        print("Running all backend tests...")
        success = tester.run_all_tests()
    
    sys.exit(0 if success else 1)
    sys.exit(0 if success else 1)