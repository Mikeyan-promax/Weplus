#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Comprehensive System Test for PostgreSQL Migration
Tests all system components after complete migration to PostgreSQL
"""

import requests
import json
import time
import os
from datetime import datetime
from typing import Dict, List, Any

class SystemTester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.frontend_url = "http://localhost:3000"
        self.test_results = []
        self.session = requests.Session()
        
    def log_test(self, test_name: str, success: bool, message: str, details: Dict = None):
        """Log test results"""
        result = {
            "test_name": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "PASS" if success else "FAIL"
        print(f"[{status}] {test_name}: {message}")
        if details:
            print(f"    Details: {json.dumps(details, indent=2)}")
        print()

    def test_api_health(self):
        """Test API health check"""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "API Health Check", 
                    True, 
                    "API is running and accessible",
                    {"status_code": response.status_code, "response": data}
                )
                return True
            else:
                self.log_test(
                    "API Health Check", 
                    False, 
                    f"API returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"API connection failed: {str(e)}")
            return False

    def test_database_connection(self):
        """Test database connection through API"""
        try:
            # Test through a simple API endpoint that uses database
            response = self.session.get(f"{self.base_url}/api/documents/")
            if response.status_code in [200, 404]:  # 404 is ok if no documents
                self.log_test(
                    "Database Connection", 
                    True, 
                    "Database connection successful",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test(
                    "Database Connection", 
                    False, 
                    f"Database connection failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_test("Database Connection", False, f"Database test failed: {str(e)}")
            return False

    def test_user_authentication(self):
        """Test user authentication system"""
        try:
            # Test user registration
            test_user = {
                "username": f"testuser_{int(time.time())}",
                "email": f"test_{int(time.time())}@example.com",
                "password": "testpassword123",
                "full_name": "Test User"
            }
            
            response = self.session.post(f"{self.base_url}/api/auth/register", json=test_user)
            if response.status_code in [200, 201]:
                self.log_test(
                    "User Registration", 
                    True, 
                    "User registration successful",
                    {"status_code": response.status_code}
                )
                
                # Test user login
                login_data = {
                    "username": test_user["username"],
                    "password": test_user["password"]
                }
                
                login_response = self.session.post(f"{self.base_url}/api/auth/login", data=login_data)
                if login_response.status_code == 200:
                    token_data = login_response.json()
                    self.log_test(
                        "User Login", 
                        True, 
                        "User login successful",
                        {"status_code": login_response.status_code, "has_token": "access_token" in token_data}
                    )
                    return True
                else:
                    self.log_test(
                        "User Login", 
                        False, 
                        f"Login failed with status {login_response.status_code}",
                        {"status_code": login_response.status_code}
                    )
                    return False
            else:
                self.log_test(
                    "User Registration", 
                    False, 
                    f"Registration failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
        except Exception as e:
            self.log_test("User Authentication", False, f"Authentication test failed: {str(e)}")
            return False

    def test_file_upload(self):
        """Test file upload functionality"""
        try:
            # Create a test file
            test_content = "This is a test document for PostgreSQL migration testing."
            test_filename = f"test_document_{int(time.time())}.txt"
            
            files = {
                'file': (test_filename, test_content, 'text/plain')
            }
            
            response = self.session.post(f"{self.base_url}/api/documents/upload", files=files)
            if response.status_code in [200, 201]:
                data = response.json()
                self.log_test(
                    "File Upload", 
                    True, 
                    "File upload successful",
                    {"status_code": response.status_code, "filename": data.get("filename", "unknown")}
                )
                return True
            else:
                self.log_test(
                    "File Upload", 
                    False, 
                    f"File upload failed with status {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                return False
        except Exception as e:
            self.log_test("File Upload", False, f"File upload test failed: {str(e)}")
            return False

    def test_rag_system(self):
        """Test RAG system functionality"""
        try:
            # Test basic RAG chat
            chat_data = {
                "message": "What is artificial intelligence?",
                "session_id": f"test_session_{int(time.time())}",
                "use_rag": False
            }
            
            response = self.session.post(f"{self.base_url}/api/rag/chat", json=chat_data)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "RAG Basic Chat", 
                    True, 
                    "RAG basic chat successful",
                    {"status_code": response.status_code, "has_response": bool(data.get("response"))}
                )
                
                # Test RAG with knowledge base
                rag_data = {
                    "message": "Tell me about database migration best practices",
                    "session_id": f"test_session_{int(time.time())}",
                    "use_rag": True
                }
                
                rag_response = self.session.post(f"{self.base_url}/api/rag/chat", json=rag_data)
                if rag_response.status_code == 200:
                    rag_result = rag_response.json()
                    self.log_test(
                        "RAG Knowledge Base", 
                        True, 
                        "RAG with knowledge base successful",
                        {"status_code": rag_response.status_code, "has_response": bool(rag_result.get("response"))}
                    )
                    return True
                else:
                    self.log_test(
                        "RAG Knowledge Base", 
                        False, 
                        f"RAG knowledge base failed with status {rag_response.status_code}",
                        {"status_code": rag_response.status_code}
                    )
                    return False
            else:
                self.log_test(
                    "RAG Basic Chat", 
                    False, 
                    f"RAG basic chat failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_test("RAG System", False, f"RAG system test failed: {str(e)}")
            return False

    def test_document_search(self):
        """Test document search functionality"""
        try:
            search_data = {
                "query": "test document",
                "limit": 5
            }
            
            response = self.session.post(f"{self.base_url}/api/rag/search", json=search_data)
            if response.status_code == 200:
                data = response.json()
                self.log_test(
                    "Document Search", 
                    True, 
                    "Document search successful",
                    {"status_code": response.status_code, "results_count": len(data.get("results", []))}
                )
                return True
            else:
                self.log_test(
                    "Document Search", 
                    False, 
                    f"Document search failed with status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_test("Document Search", False, f"Document search test failed: {str(e)}")
            return False

    def test_frontend_accessibility(self):
        """Test frontend accessibility"""
        try:
            response = requests.get(self.frontend_url, timeout=10)
            if response.status_code == 200:
                self.log_test(
                    "Frontend Accessibility", 
                    True, 
                    "Frontend is accessible",
                    {"status_code": response.status_code}
                )
                return True
            else:
                self.log_test(
                    "Frontend Accessibility", 
                    False, 
                    f"Frontend returned status {response.status_code}",
                    {"status_code": response.status_code}
                )
                return False
        except Exception as e:
            self.log_test("Frontend Accessibility", False, f"Frontend test failed: {str(e)}")
            return False

    def test_api_endpoints(self):
        """Test various API endpoints"""
        endpoints = [
            ("/api/documents/", "GET"),
            ("/api/auth/me", "GET"),
            ("/api/rag/documents/process", "POST"),
        ]
        
        success_count = 0
        total_count = len(endpoints)
        
        for endpoint, method in endpoints:
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}", json={})
                
                # Accept various status codes as success (200, 401 for auth, 422 for validation)
                if response.status_code in [200, 401, 422]:
                    success_count += 1
                    
            except Exception:
                pass
        
        success_rate = (success_count / total_count) * 100
        self.log_test(
            "API Endpoints", 
            success_rate >= 70, 
            f"API endpoints test: {success_count}/{total_count} accessible ({success_rate:.1f}%)",
            {"success_rate": success_rate, "accessible_endpoints": success_count}
        )
        
        return success_rate >= 70

    def run_all_tests(self):
        """Run all system tests"""
        print("=" * 60)
        print("COMPREHENSIVE SYSTEM TEST - PostgreSQL Migration")
        print("=" * 60)
        print(f"Started at: {datetime.now().isoformat()}")
        print()
        
        # Core system tests
        tests = [
            ("API Health Check", self.test_api_health),
            ("Database Connection", self.test_database_connection),
            ("User Authentication", self.test_user_authentication),
            ("File Upload", self.test_file_upload),
            ("RAG System", self.test_rag_system),
            ("Document Search", self.test_document_search),
            ("Frontend Accessibility", self.test_frontend_accessibility),
            ("API Endpoints", self.test_api_endpoints),
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"Running {test_name}...")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
            
            time.sleep(1)  # Brief pause between tests
        
        # Generate summary
        print("=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Tests Passed: {passed_tests}/{total_tests} ({success_rate:.1f}%)")
        print(f"Completed at: {datetime.now().isoformat()}")
        
        if success_rate >= 80:
            print("✅ SYSTEM STATUS: HEALTHY - PostgreSQL migration successful!")
        elif success_rate >= 60:
            print("⚠️  SYSTEM STATUS: PARTIAL - Some issues detected")
        else:
            print("❌ SYSTEM STATUS: CRITICAL - Major issues detected")
        
        print()
        print("Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test_name']}: {result['message']}")
        
        return success_rate

if __name__ == "__main__":
    tester = SystemTester()
    success_rate = tester.run_all_tests()
    
    # Save results to file
    with open("system_test_results.json", "w", encoding="utf-8") as f:
        json.dump({
            "success_rate": success_rate,
            "test_results": tester.test_results,
            "timestamp": datetime.now().isoformat()
        }, f, indent=2, ensure_ascii=False)
    
    print(f"\nDetailed results saved to: system_test_results.json")