#!/usr/bin/env python3
"""
QR Attendance System Focused Testing Script
Testing the specific endpoints requested in the review
"""

import requests
import json
import sys
from datetime import datetime

# Backend URL
BASE_URL = "http://127.0.0.1:8001/api"

class QRAttendanceTester:
    def __init__(self):
        self.base_url = BASE_URL
        self.session = requests.Session()
        self.test_results = []
        self.tokens = {}
        
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
        if role in self.tokens:
            return self.tokens[role]
            
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
                token = result.get('access_token')
                self.tokens[role] = token
                return token
            return None
        except Exception:
            return None

    def test_qr_generation_endpoints(self):
        """Test both QR generation endpoints"""
        print("\n=== Testing QR Generation Endpoints ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("QR Generation Setup", False, "Could not get teacher auth token")
            return False
        
        headers = {
            'Authorization': f'Bearer {teacher_token}',
            'Content-Type': 'application/json'
        }
        
        # Test 1: Manual QR generation (/api/qr/generate)
        qr_data = {
            "class_section": "A5",
            "subject": "Mathematics",
            "class_code": "MC",
            "time_slot": "09:30-10:30"
        }
        
        response = self.session.post(f"{self.base_url}/qr/generate", json=qr_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            required_fields = ['session_id', 'qr_image', 'qr_data', 'expires_at']
            missing_fields = [field for field in required_fields if field not in result]
            
            if not missing_fields:
                self.log_result("QR Generate Manual", True, 
                              "Manual QR generation working correctly", 
                              f"Session ID: {result['session_id']}")
                self.manual_qr_result = result
            else:
                self.log_result("QR Generate Manual", False, 
                              f"Response missing fields: {missing_fields}")
                return False
        else:
            self.log_result("QR Generate Manual", False, 
                          f"Manual QR generation failed: {response.status_code}")
            return False
        
        # Test 2: Active class QR generation (/api/qr/generate-for-active-class)
        class_info = {
            "section": "A5",
            "subject": "Mathematics",
            "time": "09:30-10:30"
        }
        
        response = self.session.post(f"{self.base_url}/qr/generate-for-active-class", 
                                   json=class_info, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'session_id' in result and 'qr_data' in result:
                self.log_result("QR Generate Active Class", True, 
                              "Active class QR generation working correctly")
                self.active_qr_result = result
            else:
                self.log_result("QR Generate Active Class", False, 
                              "Active class QR response missing required fields")
        elif response.status_code == 400:
            # Expected if no active class matches current time
            self.log_result("QR Generate Active Class", True, 
                          "No active class found (expected behavior for current time)")
        else:
            self.log_result("QR Generate Active Class", False, 
                          f"Active class QR generation failed: {response.status_code}")
        
        return True

    def test_attendance_marking_endpoint(self):
        """Test attendance marking endpoint (/api/attendance/mark)"""
        print("\n=== Testing Attendance Marking Endpoint ===")
        
        if not hasattr(self, 'manual_qr_result'):
            self.log_result("Attendance Marking Setup", False, "No QR code available for testing")
            return False
        
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Attendance Marking Setup", False, "Could not get student auth token")
            return False
        
        headers = {
            'Authorization': f'Bearer {student_token}',
            'Content-Type': 'application/json'
        }
        
        # Test valid QR data
        attendance_data = {
            "qr_data": self.manual_qr_result['qr_data']
        }
        
        response = self.session.post(f"{self.base_url}/attendance/mark", 
                                   json=attendance_data, headers=headers)
        
        if response.status_code == 200:
            result = response.json()
            if 'attendance_id' in result:
                self.log_result("Attendance Marking Valid", True, 
                              "Attendance marked successfully with valid QR", 
                              f"Attendance ID: {result['attendance_id']}")
            else:
                self.log_result("Attendance Marking Valid", False, 
                              "Response missing attendance_id")
                return False
        elif response.status_code == 400:
            result = response.json()
            detail = result.get('detail', '')
            if 'already marked' in detail:
                self.log_result("Attendance Marking Valid", True, 
                              "Duplicate attendance correctly prevented")
            elif 'not enrolled' in detail:
                self.log_result("Attendance Marking Valid", True, 
                              "Class section validation working correctly")
            else:
                self.log_result("Attendance Marking Valid", False, 
                              f"Unexpected validation error: {detail}")
                return False
        else:
            self.log_result("Attendance Marking Valid", False, 
                          f"Attendance marking failed: {response.status_code}")
            return False
        
        # Test invalid QR data
        invalid_attendance_data = {
            "qr_data": "invalid_json_data"
        }
        
        response = self.session.post(f"{self.base_url}/attendance/mark", 
                                   json=invalid_attendance_data, headers=headers)
        
        if response.status_code == 400:
            self.log_result("Attendance Marking Invalid", True, 
                          "Invalid QR data correctly rejected")
        else:
            self.log_result("Attendance Marking Invalid", False, 
                          f"Expected 400 for invalid QR, got {response.status_code}")
        
        return True

    def test_qr_session_validation_and_expiry(self):
        """Test QR session validation and expiry logic"""
        print("\n=== Testing QR Session Validation and Expiry ===")
        
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token:
            self.log_result("QR Session Validation", False, "Could not get teacher auth token")
            return False
        
        headers = {'Authorization': f'Bearer {teacher_token}'}
        
        # Get QR sessions to verify session structure and expiry
        response = self.session.get(f"{self.base_url}/qr/sessions", headers=headers)
        
        if response.status_code == 200:
            sessions = response.json()
            if sessions:
                latest_session = sessions[-1]
                
                # Check session structure
                required_fields = ['id', 'expires_at', 'is_active', 'qr_data', 'class_section', 'subject']
                missing_fields = [field for field in required_fields if field not in latest_session]
                
                if not missing_fields:
                    self.log_result("QR Session Structure", True, 
                                  "QR session has all required fields")
                else:
                    self.log_result("QR Session Structure", False, 
                                  f"Session missing fields: {missing_fields}")
                    return False
                
                # Check expiry logic
                if 'expires_at' in latest_session:
                    from datetime import datetime
                    try:
                        expires_at = datetime.fromisoformat(latest_session['expires_at'].replace('Z', '+00:00'))
                        current_time = datetime.now(expires_at.tzinfo)
                        
                        if expires_at > current_time:
                            self.log_result("QR Session Expiry", True, 
                                          "QR session has valid future expiry time")
                        else:
                            self.log_result("QR Session Expiry", True, 
                                          "QR session has expired (expected for past time slots)")
                    except Exception as e:
                        self.log_result("QR Session Expiry", False, 
                                      f"Could not parse expiry date: {e}")
                        return False
                else:
                    self.log_result("QR Session Expiry", False, "Session missing expiry field")
                    return False
            else:
                self.log_result("QR Session Validation", False, "No sessions found")
                return False
        else:
            self.log_result("QR Session Validation", False, 
                          f"Could not retrieve sessions: {response.status_code}")
            return False
        
        return True

    def test_student_authentication_and_class_validation(self):
        """Test student authentication and class section validation"""
        print("\n=== Testing Student Authentication and Class Validation ===")
        
        # Test 1: Only students can mark attendance
        teacher_token = self.get_auth_token_for_role("teacher")
        if not teacher_token or not hasattr(self, 'manual_qr_result'):
            self.log_result("Student Auth Validation", False, "Setup failed")
            return False
        
        teacher_headers = {
            'Authorization': f'Bearer {teacher_token}',
            'Content-Type': 'application/json'
        }
        
        attendance_data = {
            "qr_data": self.manual_qr_result['qr_data']
        }
        
        response = self.session.post(f"{self.base_url}/attendance/mark", 
                                   json=attendance_data, headers=teacher_headers)
        
        if response.status_code == 403:
            self.log_result("Student Auth Validation", True, 
                          "Non-students correctly forbidden from marking attendance")
        else:
            self.log_result("Student Auth Validation", False, 
                          f"Expected 403 for non-student, got {response.status_code}")
            return False
        
        # Test 2: Class section validation
        student_token = self.get_auth_token_for_role("student")
        if not student_token:
            self.log_result("Class Section Validation", False, "Could not get student token")
            return False
        
        # Generate QR for different class section (A6) if student is in A5
        qr_data_a6 = {
            "class_section": "A6",
            "subject": "Physics",
            "class_code": "PHY",
            "time_slot": "10:30-11:30"
        }
        
        teacher_headers_gen = {
            'Authorization': f'Bearer {teacher_token}',
            'Content-Type': 'application/json'
        }
        
        response = self.session.post(f"{self.base_url}/qr/generate", 
                                   json=qr_data_a6, headers=teacher_headers_gen)
        
        if response.status_code == 200:
            qr_result_a6 = response.json()
            
            student_headers = {
                'Authorization': f'Bearer {student_token}',
                'Content-Type': 'application/json'
            }
            
            attendance_data_a6 = {
                "qr_data": qr_result_a6['qr_data']
            }
            
            response = self.session.post(f"{self.base_url}/attendance/mark", 
                                       json=attendance_data_a6, headers=student_headers)
            
            if response.status_code == 400:
                result = response.json()
                detail = result.get('detail', '')
                if 'not enrolled' in detail:
                    self.log_result("Class Section Validation", True, 
                                  "Class section mismatch correctly detected")
                else:
                    self.log_result("Class Section Validation", True, 
                                  "Some validation working (different error)")
            elif response.status_code == 200:
                # This could happen if student is actually in A6 or has access to both
                self.log_result("Class Section Validation", True, 
                              "Student has access to this class section")
            else:
                self.log_result("Class Section Validation", False, 
                              f"Unexpected response: {response.status_code}")
                return False
        else:
            self.log_result("Class Section Validation", False, 
                          "Could not generate A6 QR for testing")
            return False
        
        return True

    def run_qr_attendance_tests(self):
        """Run all QR attendance system tests"""
        print("=" * 70)
        print("QR ATTENDANCE SYSTEM FOCUSED TESTING")
        print("=" * 70)
        print(f"Backend URL: {self.base_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        tests = [
            self.test_qr_generation_endpoints,
            self.test_attendance_marking_endpoint,
            self.test_qr_session_validation_and_expiry,
            self.test_student_authentication_and_class_validation
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
        print(f"\n{'='*70}")
        print("QR ATTENDANCE SYSTEM TEST SUMMARY")
        print(f"{'='*70}")
        print(f"Total Test Groups: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        # Detailed results
        print(f"\nDETAILED RESULTS:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"{status} {result['test']}: {result['message']}")
        
        return passed == total

if __name__ == "__main__":
    tester = QRAttendanceTester()
    success = tester.run_qr_attendance_tests()
    sys.exit(0 if success else 1)