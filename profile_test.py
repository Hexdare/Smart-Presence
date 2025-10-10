#!/usr/bin/env python3
"""
Profile Update Testing Script for Smart Attendance System
Focus: Testing the new profile update functionality
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

class ProfileTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        
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

    def get_auth_token_for_role(self, role):
        """Get authentication token for specific role"""
        try:
            username_map = {
                "teacher": "teacher_test_user",
                "principal": "principal_test_user",
                "verifier": "test_verifier_user_2",
                "institution_admin": "test_institution_admin_user_2"
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

    def test_profile_update_username(self):
        """Test 1: Profile Update Endpoint - Update Username"""
        print("\n=== Testing Profile Update - Username ===")
        
        # Use verifier role as it's available
        verifier_token = self.get_auth_token_for_role("verifier")
        if not verifier_token:
            self.log_result("Profile Update Username", False, "Could not get verifier auth token")
            return False
        
        try:
            profile_data = {
                "username": f"updated_verifier_{datetime.now().strftime('%H%M%S')}",
                "current_password": "testpass123"
            }
            
            headers = {
                'Authorization': f'Bearer {verifier_token}',
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
        
        # Create a new test user for wrong password test
        try:
            test_user_data = {
                "username": f"wrong_pass_test_{datetime.now().strftime('%H%M%S')}",
                "password": "correctpass123",
                "role": "verifier",
                "full_name": "Wrong Password Test User"
            }
            
            headers = {'Content-Type': 'application/json'}
            response = self.session.post(f"{self.base_url}/auth/register", 
                                       json=test_user_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Wrong Password", False, "Could not create test user")
                return False
            
            # Login to get token
            login_data = {
                "username": test_user_data["username"],
                "password": "correctpass123"
            }
            
            response = self.session.post(f"{self.base_url}/auth/login", 
                                       json=login_data, headers=headers)
            
            if response.status_code != 200:
                self.log_result("Profile Update Wrong Password", False, "Could not login with test user")
                return False
            
            token = response.json()['access_token']
            
            # Try to update with wrong current password
            profile_data = {
                "username": "should_not_update",
                "current_password": "wrongpassword123"  # Wrong password
            }
            
            auth_headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }
            
            response = self.session.put(f"{self.base_url}/auth/profile", 
                                      json=profile_data, headers=auth_headers)
            
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
        verifier_token = self.get_auth_token_for_role("verifier")
        teacher_token = self.get_auth_token_for_role("teacher")
        
        if not verifier_token or not teacher_token:
            self.log_result("Profile Update Duplicate Username", False, "Could not get required auth tokens")
            return False
        
        try:
            # Try to update verifier username to teacher's username
            profile_data = {
                "username": "teacher_test_user",  # This username should already exist
                "current_password": "testpass123"
            }
            
            headers = {
                'Authorization': f'Bearer {verifier_token}',
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

    def run_profile_tests(self):
        """Run all profile update tests"""
        print("=" * 80)
        print("SMART ATTENDANCE SYSTEM - PROFILE UPDATE TESTING")
        print("=" * 80)
        
        tests = [
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
        print(f"\n{'='*80}")
        print("PROFILE UPDATE TEST SUMMARY")
        print(f"{'='*80}")
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
        else:
            print(f"\n✅ ALL PROFILE UPDATE TESTS PASSED!")
        
        return passed == total

if __name__ == "__main__":
    tester = ProfileTester()
    success = tester.run_profile_tests()
    sys.exit(0 if success else 1)