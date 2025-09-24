#!/usr/bin/env python3
"""
Debug 405 Method Not Allowed Error on /api/auth/register
Specific tests to investigate routing and method availability
"""

import requests
import json
import sys
from datetime import datetime

# Get the production URL from frontend/.env
def get_production_url():
    try:
        with open('/app/frontend/.env', 'r') as f:
            for line in f:
                if line.startswith('REACT_APP_BACKEND_URL='):
                    base_url = line.split('=', 1)[1].strip().rstrip('/')
                    return base_url
    except Exception as e:
        print(f"Error reading frontend .env: {e}")
        return None

PROD_BASE_URL = get_production_url()
if not PROD_BASE_URL:
    print("Could not get production URL from frontend/.env")
    sys.exit(1)

print(f"Production Base URL: {PROD_BASE_URL}")
print(f"Testing API at: {PROD_BASE_URL}/api")

class Debug405Tester:
    def __init__(self):
        self.base_url = PROD_BASE_URL
        self.api_url = f"{self.base_url}/api"
        self.session = requests.Session()
        
    def test_options_register(self):
        """Test OPTIONS request on /api/auth/register to see allowed methods"""
        print("\n=== 1. Testing OPTIONS /api/auth/register ===")
        
        try:
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app',
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.api_url}/auth/register", 
                                          headers=headers, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            # Check for Allow header
            allow_header = response.headers.get('Allow', 'Not present')
            print(f"\nAllow Header: {allow_header}")
            
            # Check CORS headers
            cors_methods = response.headers.get('Access-Control-Allow-Methods', 'Not present')
            print(f"Access-Control-Allow-Methods: {cors_methods}")
            
            if response.text:
                print(f"Response Body: {response.text}")
                
            return response.status_code, allow_header, cors_methods
            
        except Exception as e:
            print(f"OPTIONS request failed: {str(e)}")
            return None, None, None
    
    def test_get_register(self):
        """Test GET request on /api/auth/register to see what happens"""
        print("\n=== 2. Testing GET /api/auth/register ===")
        
        try:
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app'
            }
            
            response = self.session.get(f"{self.api_url}/auth/register", 
                                      headers=headers, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                if key.lower().startswith('access-control') or key.lower() == 'allow':
                    print(f"  {key}: {value}")
            
            if response.text:
                print(f"Response Body: {response.text[:500]}...")
                
            return response.status_code
            
        except Exception as e:
            print(f"GET request failed: {str(e)}")
            return None
    
    def test_post_register(self):
        """Test POST request on /api/auth/register with proper data"""
        print("\n=== 3. Testing POST /api/auth/register ===")
        
        try:
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app',
                'Content-Type': 'application/json'
            }
            
            test_data = {
                "username": "debug_test_user",
                "password": "testpass123",
                "role": "student",
                "student_id": "DEBUG001",
                "class_section": "A5",
                "full_name": "Debug Test User"
            }
            
            response = self.session.post(f"{self.api_url}/auth/register", 
                                       json=test_data, headers=headers, timeout=10)
            
            print(f"Status Code: {response.status_code}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                if key.lower().startswith('access-control') or key.lower() == 'allow':
                    print(f"  {key}: {value}")
            
            if response.text:
                print(f"Response Body: {response.text}")
                
            return response.status_code
            
        except Exception as e:
            print(f"POST request failed: {str(e)}")
            return None
    
    def test_fastapi_docs(self):
        """Test if FastAPI docs are accessible"""
        print("\n=== 4. Testing FastAPI Docs /docs ===")
        
        try:
            response = self.session.get(f"{self.base_url}/docs", timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("FastAPI docs are accessible - backend is running")
                if "swagger" in response.text.lower() or "openapi" in response.text.lower():
                    print("Confirmed: This is FastAPI documentation")
                else:
                    print("Warning: Response doesn't look like FastAPI docs")
            else:
                print("FastAPI docs not accessible")
                if response.text:
                    print(f"Response: {response.text[:200]}...")
                    
            return response.status_code
            
        except Exception as e:
            print(f"Docs request failed: {str(e)}")
            return None
    
    def test_api_root(self):
        """Test the API root endpoint"""
        print("\n=== 5. Testing API Root /api ===")
        
        try:
            response = self.session.get(f"{self.api_url}", timeout=10)
            
            print(f"Status Code: {response.status_code}")
            
            if response.text:
                print(f"Response Body: {response.text}")
                
            return response.status_code
            
        except Exception as e:
            print(f"API root request failed: {str(e)}")
            return None
    
    def test_path_variations(self):
        """Test different path variations to identify routing issues"""
        print("\n=== 6. Testing Path Variations ===")
        
        paths_to_test = [
            f"{self.base_url}/auth/register",  # Without /api prefix
            f"{self.api_url}/auth/register",   # With /api prefix (correct)
            f"{self.base_url}/api/auth/register/",  # With trailing slash
        ]
        
        for path in paths_to_test:
            print(f"\nTesting: {path}")
            try:
                headers = {
                    'Origin': 'https://code-pi-rust.vercel.app',
                    'Content-Type': 'application/json'
                }
                
                test_data = {
                    "username": "path_test_user",
                    "password": "testpass123",
                    "role": "student",
                    "student_id": "PATH001",
                    "class_section": "A5",
                    "full_name": "Path Test User"
                }
                
                response = self.session.post(path, json=test_data, headers=headers, timeout=10)
                
                print(f"  Status Code: {response.status_code}")
                if response.status_code == 405:
                    allow_header = response.headers.get('Allow', 'Not present')
                    print(f"  Allow Header: {allow_header}")
                
                if response.text and len(response.text) < 200:
                    print(f"  Response: {response.text}")
                    
            except Exception as e:
                print(f"  Request failed: {str(e)}")
    
    def test_verbose_curl_equivalent(self):
        """Test with verbose output similar to curl -v"""
        print("\n=== 7. Verbose Request Analysis ===")
        
        try:
            headers = {
                'Origin': 'https://code-pi-rust.vercel.app',
                'Content-Type': 'application/json',
                'User-Agent': 'Debug405Tester/1.0'
            }
            
            test_data = {
                "username": "verbose_test_user",
                "password": "testpass123",
                "role": "student",
                "student_id": "VERB001",
                "class_section": "A5",
                "full_name": "Verbose Test User"
            }
            
            print(f"Request URL: {self.api_url}/auth/register")
            print(f"Request Method: POST")
            print(f"Request Headers: {headers}")
            print(f"Request Body: {json.dumps(test_data, indent=2)}")
            
            response = self.session.post(f"{self.api_url}/auth/register", 
                                       json=test_data, headers=headers, timeout=10)
            
            print(f"\nResponse Status: {response.status_code} {response.reason}")
            print(f"Response Headers:")
            for key, value in response.headers.items():
                print(f"  {key}: {value}")
            
            print(f"\nResponse Body:")
            print(response.text)
            
            # Check if this looks like it's hitting the right server
            server_header = response.headers.get('Server', 'Unknown')
            print(f"\nServer Header: {server_header}")
            
            if 'uvicorn' in server_header.lower() or 'fastapi' in server_header.lower():
                print("✅ Request is reaching FastAPI/Uvicorn server")
            else:
                print("⚠️  Request may not be reaching FastAPI server")
                
            return response.status_code
            
        except Exception as e:
            print(f"Verbose request failed: {str(e)}")
            return None
    
    def run_debug_tests(self):
        """Run all debug tests"""
        print(f"{'='*70}")
        print("DEBUG 405 METHOD NOT ALLOWED ERROR")
        print(f"{'='*70}")
        print(f"Production URL: {PROD_BASE_URL}")
        print(f"API URL: {self.api_url}")
        print(f"Test started at: {datetime.now().isoformat()}")
        
        # Run all tests
        results = {}
        
        results['options'] = self.test_options_register()
        results['get'] = self.test_get_register()
        results['post'] = self.test_post_register()
        results['docs'] = self.test_fastapi_docs()
        results['api_root'] = self.test_api_root()
        
        self.test_path_variations()
        results['verbose'] = self.test_verbose_curl_equivalent()
        
        # Summary
        print(f"\n{'='*70}")
        print("DEBUG SUMMARY")
        print(f"{'='*70}")
        
        print(f"OPTIONS /api/auth/register: {results['options'][0] if results['options'][0] else 'FAILED'}")
        if results['options'][1]:
            print(f"  Allow Header: {results['options'][1]}")
        if results['options'][2]:
            print(f"  CORS Methods: {results['options'][2]}")
            
        print(f"GET /api/auth/register: {results['get'] if results['get'] else 'FAILED'}")
        print(f"POST /api/auth/register: {results['post'] if results['post'] else 'FAILED'}")
        print(f"FastAPI Docs: {results['docs'] if results['docs'] else 'FAILED'}")
        print(f"API Root: {results['api_root'] if results['api_root'] else 'FAILED'}")
        
        # Analysis
        print(f"\n{'='*70}")
        print("ANALYSIS")
        print(f"{'='*70}")
        
        if results['post'] == 405:
            print("❌ CONFIRMED: 405 Method Not Allowed on POST /api/auth/register")
            if results['options'][1] and 'POST' not in results['options'][1]:
                print("❌ POST method not in Allow header")
            else:
                print("✅ POST method appears to be allowed (check CORS)")
        elif results['post'] in [200, 400]:
            print("✅ POST /api/auth/register is working")
        elif results['post'] is None:
            print("❌ POST request failed completely (network/connection issue)")
        
        if results['docs'] == 200:
            print("✅ FastAPI backend is running and accessible")
        else:
            print("❌ FastAPI backend may not be running or accessible")
            
        return results

if __name__ == "__main__":
    tester = Debug405Tester()
    results = tester.run_debug_tests()