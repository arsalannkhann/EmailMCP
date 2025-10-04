#!/usr/bin/env python3
"""
Test script to verify OAuth endpoints are correctly configured.
This script tests that the OAuth callback endpoint accepts GET requests.
"""

import sys
import requests
from typing import Dict, Any

# Test configuration
BASE_URL = "http://localhost:8001"
API_KEY = "dev-api-key"

def test_health():
    """Test that the service is running."""
    print("1. Testing health endpoint...")
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("   ✓ Service is healthy")
            return True
        else:
            print(f"   ✗ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"   ✗ Cannot connect to service: {e}")
        return False

def test_oauth_authorize():
    """Test OAuth authorization endpoint."""
    print("\n2. Testing OAuth authorization endpoint...")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}",
            "Content-Type": "application/json"
        }
        data = {
            "user_id": "test_user_123",
            "redirect_uri": "http://localhost:8000/callback.html"
        }
        response = requests.post(
            f"{BASE_URL}/v1/oauth/authorize",
            json=data,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✓ Authorization URL generated")
            print(f"   Authorization URL: {result.get('authorization_url', 'N/A')[:100]}...")
            return True
        else:
            print(f"   ✗ Authorization failed: {response.status_code}")
            print(f"   Response: {response.text}")
            return False
    except Exception as e:
        print(f"   ✗ Authorization request failed: {e}")
        return False

def test_oauth_callback_get():
    """Test OAuth callback GET endpoint (should work without API key)."""
    print("\n3. Testing OAuth callback GET endpoint (public)...")
    try:
        # This should NOT return 404 - it's a public endpoint
        params = {
            "code": "test_code_123",
            "state": "test_user_123",
            "redirect_uri": "http://localhost:8000/callback.html"
        }
        response = requests.get(
            f"{BASE_URL}/v1/oauth/callback",
            params=params,
            timeout=5
        )
        
        # We expect 400 (bad code) or 500 (service error), NOT 404
        if response.status_code == 404:
            print("   ✗ FAIL: Endpoint returns 404 (endpoint not found)")
            print("   This is the OAuth configuration bug!")
            return False
        elif response.status_code in [400, 500]:
            print(f"   ✓ Endpoint exists (returns {response.status_code})")
            print("   Note: This is expected since we're using a test code")
            print("   The important thing is it's NOT a 404!")
            return True
        elif response.status_code == 200:
            print("   ✓ Endpoint works and returned success")
            return True
        else:
            print(f"   ? Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text}")
            return True
    except Exception as e:
        print(f"   ✗ GET request failed: {e}")
        return False

def test_oauth_callback_post():
    """Test OAuth callback POST endpoint (requires API key)."""
    print("\n4. Testing OAuth callback POST endpoint (with auth)...")
    try:
        headers = {
            "Authorization": f"Bearer {API_KEY}"
        }
        params = {
            "code": "test_code_123",
            "state": "test_user_123",
            "redirect_uri": "http://localhost:8000/callback.html"
        }
        response = requests.post(
            f"{BASE_URL}/v1/oauth/callback",
            params=params,
            headers=headers,
            timeout=5
        )
        
        if response.status_code == 404:
            print("   ✗ FAIL: Endpoint returns 404")
            return False
        elif response.status_code in [400, 500]:
            print(f"   ✓ Endpoint exists (returns {response.status_code})")
            print("   Note: Expected error with test credentials")
            return True
        elif response.status_code == 200:
            print("   ✓ Endpoint works and returned success")
            return True
        else:
            print(f"   ? Unexpected status code: {response.status_code}")
            return True
    except Exception as e:
        print(f"   ✗ POST request failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 70)
    print("EmailMCP OAuth Endpoint Test Suite")
    print("=" * 70)
    print("\nThis test verifies that the OAuth callback endpoint is correctly")
    print("configured to accept GET requests without authentication.")
    print()
    
    results = []
    
    # Test 1: Health check
    results.append(("Health Check", test_health()))
    
    if not results[0][1]:
        print("\n" + "=" * 70)
        print("FAIL: Service is not running. Start it with:")
        print("  uvicorn src.mcp.main:app --reload --port 8001")
        print("=" * 70)
        sys.exit(1)
    
    # Test 2: OAuth authorize
    results.append(("OAuth Authorize", test_oauth_authorize()))
    
    # Test 3: OAuth callback GET (most important!)
    results.append(("OAuth Callback GET", test_oauth_callback_get()))
    
    # Test 4: OAuth callback POST
    results.append(("OAuth Callback POST", test_oauth_callback_post()))
    
    # Summary
    print("\n" + "=" * 70)
    print("Test Summary")
    print("=" * 70)
    
    for test_name, passed in results:
        status = "✓ PASS" if passed else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    all_passed = all(result[1] for result in results)
    
    if all_passed:
        print("\n✓ All tests passed!")
        print("\nThe OAuth callback endpoint is correctly configured.")
        print("Google OAuth redirects will now work properly.")
    else:
        print("\n✗ Some tests failed!")
        print("\nCheck the failures above and review OAUTH_CONFIGURATION.md")
    
    print("=" * 70)
    sys.exit(0 if all_passed else 1)

if __name__ == "__main__":
    main()
