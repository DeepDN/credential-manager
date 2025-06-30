#!/usr/bin/env python3
"""
Comprehensive test script for SecureVault v2.0 features
Tests all new features: HSM, Mobile API, Browser Extension API, Sync Service, and Themes
"""

import asyncio
import json
import requests
import time
import uuid
from typing import Dict, Any

class SecureVaultV2Tester:
    def __init__(self):
        self.base_url = "http://localhost:8000"
        self.session = requests.Session()
        self.test_results = {}
        
    def run_all_tests(self):
        """Run all v2.0 feature tests"""
        print("🔐 SecureVault v2.0 Feature Testing")
        print("=" * 50)
        
        tests = [
            ("HSM Support", self.test_hsm_features),
            ("Mobile API", self.test_mobile_api),
            ("Browser Extension API", self.test_browser_extension_api),
            ("Sync Service", self.test_sync_service),
            ("Themes & Customization", self.test_themes_api),
            ("Integration Tests", self.test_integration)
        ]
        
        for test_name, test_func in tests:
            print(f"\n🧪 Testing {test_name}...")
            try:
                result = test_func()
                self.test_results[test_name] = result
                status = "✅ PASSED" if result['success'] else "❌ FAILED"
                print(f"{status}: {result['message']}")
                if not result['success'] and 'details' in result:
                    print(f"   Details: {result['details']}")
            except Exception as e:
                self.test_results[test_name] = {
                    'success': False,
                    'message': f"Test failed with exception: {str(e)}"
                }
                print(f"❌ FAILED: {str(e)}")
        
        self.print_summary()
    
    def test_hsm_features(self) -> Dict[str, Any]:
        """Test HSM functionality"""
        try:
            # Test HSM initialization
            from app.hsm import initialize_hsm, get_hsm_manager
            
            # Initialize HSM
            config = {
                'provider': 'softhsm',
                'key_store_path': './test_hsm_keys'
            }
            
            if not initialize_hsm(config):
                return {
                    'success': False,
                    'message': 'HSM initialization failed'
                }
            
            hsm_manager = get_hsm_manager()
            
            # Test key generation
            if not hsm_manager.generate_master_key("test_key"):
                return {
                    'success': False,
                    'message': 'HSM key generation failed'
                }
            
            # Test encryption/decryption
            test_data = b"test vault key data"
            encrypted = hsm_manager.encrypt_vault_key(test_data, "test_key")
            
            if not encrypted:
                return {
                    'success': False,
                    'message': 'HSM encryption failed'
                }
            
            decrypted = hsm_manager.decrypt_vault_key(encrypted, "test_key")
            
            if decrypted != test_data:
                return {
                    'success': False,
                    'message': 'HSM decryption failed or data mismatch'
                }
            
            return {
                'success': True,
                'message': 'HSM features working correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'HSM test failed',
                'details': str(e)
            }
    
    def test_mobile_api(self) -> Dict[str, Any]:
        """Test Mobile API endpoints"""
        try:
            # Test device registration
            device_data = {
                "device_id": str(uuid.uuid4()),
                "device_name": "Test iPhone",
                "platform": "ios",
                "master_password": "test123"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/mobile/auth/register",
                json=device_data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Mobile device registration failed: {response.status_code}'
                }
            
            # Test mobile authentication (would need vault setup)
            # For now, just test endpoint availability
            response = self.session.post(
                f"{self.base_url}/api/mobile/auth/login",
                json=device_data
            )
            
            # Expect 401 or 500 since vault isn't set up, but endpoint should exist
            if response.status_code not in [401, 500]:
                return {
                    'success': False,
                    'message': f'Mobile auth endpoint unexpected response: {response.status_code}'
                }
            
            return {
                'success': True,
                'message': 'Mobile API endpoints accessible'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Mobile API test failed',
                'details': str(e)
            }
    
    def test_browser_extension_api(self) -> Dict[str, Any]:
        """Test Browser Extension API endpoints"""
        try:
            # Test extension authentication endpoint
            auth_data = {
                "master_password": "test123",
                "extension_id": "test-extension-id",
                "browser": "chrome",
                "origin": "https://example.com"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/browser/auth",
                json=auth_data
            )
            
            # Expect 401 or 500 since vault isn't set up
            if response.status_code not in [401, 500]:
                return {
                    'success': False,
                    'message': f'Browser extension auth unexpected response: {response.status_code}'
                }
            
            # Test password generation endpoint (should work without auth for testing)
            gen_data = {
                "length": 16,
                "include_symbols": True,
                "include_numbers": True,
                "include_uppercase": True,
                "include_lowercase": True,
                "exclude_ambiguous": True
            }
            
            # This would normally require auth, but we're testing endpoint existence
            response = self.session.post(
                f"{self.base_url}/api/browser/generate-password",
                json=gen_data,
                headers={"X-Session-Token": "test-token"}
            )
            
            # Expect 401 for invalid token, but endpoint should exist
            if response.status_code != 401:
                return {
                    'success': False,
                    'message': f'Browser extension password gen unexpected response: {response.status_code}'
                }
            
            return {
                'success': True,
                'message': 'Browser extension API endpoints accessible'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Browser extension API test failed',
                'details': str(e)
            }
    
    def test_sync_service(self) -> Dict[str, Any]:
        """Test Sync Service functionality"""
        try:
            # Test device registration for sync
            device_data = {
                "device_id": str(uuid.uuid4()),
                "device_name": "Test Desktop",
                "device_type": "desktop",
                "platform": "linux",
                "sync_key": "test-sync-key"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/sync/register",
                json=device_data
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Sync device registration failed: {response.status_code}'
                }
            
            # Test sync status
            device_id = device_data["device_id"]
            response = self.session.get(
                f"{self.base_url}/api/sync/status/{device_id}"
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Sync status check failed: {response.status_code}'
                }
            
            # Test device listing
            response = self.session.get(
                f"{self.base_url}/api/sync/devices"
            )
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Sync device listing failed: {response.status_code}'
                }
            
            return {
                'success': True,
                'message': 'Sync service working correctly'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Sync service test failed',
                'details': str(e)
            }
    
    def test_themes_api(self) -> Dict[str, Any]:
        """Test Themes and Customization API"""
        try:
            # Test getting all themes
            response = self.session.get(f"{self.base_url}/api/themes/")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Get themes failed: {response.status_code}'
                }
            
            themes = response.json()
            if not isinstance(themes, list) or len(themes) == 0:
                return {
                    'success': False,
                    'message': 'No themes returned'
                }
            
            # Test getting specific theme
            theme_id = themes[0]['id']
            response = self.session.get(f"{self.base_url}/api/themes/{theme_id}")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Get specific theme failed: {response.status_code}'
                }
            
            # Test getting current settings
            response = self.session.get(f"{self.base_url}/api/themes/settings/current")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Get current settings failed: {response.status_code}'
                }
            
            # Test getting current CSS
            response = self.session.get(f"{self.base_url}/api/themes/css/current")
            
            if response.status_code != 200:
                return {
                    'success': False,
                    'message': f'Get current CSS failed: {response.status_code}'
                }
            
            css_data = response.json()
            if 'css' not in css_data:
                return {
                    'success': False,
                    'message': 'CSS data missing from response'
                }
            
            return {
                'success': True,
                'message': f'Themes API working correctly ({len(themes)} themes available)'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Themes API test failed',
                'details': str(e)
            }
    
    def test_integration(self) -> Dict[str, Any]:
        """Test integration between features"""
        try:
            # Test that all API routers are properly mounted
            endpoints_to_test = [
                "/api/mobile/auth/register",
                "/api/browser/auth", 
                "/api/sync/devices",
                "/api/themes/",
                "/docs"  # FastAPI auto-generated docs
            ]
            
            failed_endpoints = []
            
            for endpoint in endpoints_to_test:
                try:
                    response = self.session.get(f"{self.base_url}{endpoint}")
                    # We expect various status codes, but not 404 (not found)
                    if response.status_code == 404:
                        failed_endpoints.append(endpoint)
                except Exception:
                    failed_endpoints.append(endpoint)
            
            if failed_endpoints:
                return {
                    'success': False,
                    'message': f'Some endpoints not accessible: {failed_endpoints}'
                }
            
            return {
                'success': True,
                'message': 'All API endpoints properly integrated'
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': 'Integration test failed',
                'details': str(e)
            }
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 50)
        print("🔐 SecureVault v2.0 Test Summary")
        print("=" * 50)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ Failed Tests:")
            for test_name, result in self.test_results.items():
                if not result['success']:
                    print(f"  - {test_name}: {result['message']}")
        
        print("\n🎉 SecureVault v2.0 Feature Testing Complete!")

def main():
    """Main test function"""
    print("Starting SecureVault v2.0 feature tests...")
    print("Make sure the SecureVault server is running on localhost:8000")
    
    # Wait a moment for user to read
    time.sleep(2)
    
    tester = SecureVaultV2Tester()
    tester.run_all_tests()

if __name__ == "__main__":
    main()
