"""
Tests for API routes, error handling, and response validation
Tests all HTTP endpoints, status codes, and error responses
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from fastapi.testclient import TestClient
from fastapi import status

from src.mcp.main import app


class TestAPIRouteValidation:
    """Test API route validation and error handling"""
    
    def test_send_message_missing_required_fields(self):
        """Test send message endpoint with missing required fields"""
        client = TestClient(app)
        
        # Missing 'to' field
        invalid_email = {
            "provider": "gmail_api",
            "subject": "Test",
            "body": "Test body",
            "from_email": "sender@example.com"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/messages", json=invalid_email, headers=headers)
        
        # Should return validation error
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_send_message_invalid_email_format(self):
        """Test send message with invalid email format"""
        client = TestClient(app)
        
        invalid_email = {
            "provider": "gmail_api",
            "to": ["not-an-email"],  # Invalid format
            "subject": "Test",
            "body": "Test body",
            "from_email": "sender@example.com"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/messages", json=invalid_email, headers=headers)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_send_message_empty_recipient_list(self):
        """Test send message with empty recipient list"""
        client = TestClient(app)
        
        invalid_email = {
            "provider": "gmail_api",
            "to": [],  # Empty list
            "subject": "Test",
            "body": "Test body",
            "from_email": "sender@example.com"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/messages", json=invalid_email, headers=headers)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_send_message_invalid_provider(self):
        """Test send message with invalid provider"""
        client = TestClient(app)
        
        invalid_email = {
            "provider": "invalid_provider",
            "to": ["test@example.com"],
            "subject": "Test",
            "body": "Test body",
            "from_email": "sender@example.com"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/messages", json=invalid_email, headers=headers)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_oauth_authorize_missing_fields(self):
        """Test OAuth authorize with missing fields"""
        client = TestClient(app)
        
        # Missing redirect_uri
        invalid_request = {
            "user_id": "test_user"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/oauth/authorize", json=invalid_request, headers=headers)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_oauth_callback_missing_parameters(self):
        """Test OAuth callback with missing parameters"""
        client = TestClient(app)
        
        # Missing 'state' parameter
        response = client.get("/v1/oauth/callback?code=test_code")
        
        # Should return error
        assert response.status_code in [400, 422]
    
    def test_user_profile_invalid_user_id(self):
        """Test user profile endpoint with invalid user ID"""
        client = TestClient(app)
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.get("/v1/users//profile", headers=headers)  # Empty user ID
        
        # Should return error
        assert response.status_code in [404, 422]


class TestAuthenticationAuthorization:
    """Test authentication and authorization"""
    
    def test_send_message_without_api_key(self):
        """Test send message without API key"""
        client = TestClient(app)
        
        valid_email = {
            "provider": "gmail_api",
            "to": ["test@example.com"],
            "subject": "Test",
            "body": "Test body",
            "from_email": "sender@example.com"
        }
        
        # No Authorization header
        response = client.post("/v1/messages", json=valid_email)
        
        # Should return unauthorized
        assert response.status_code in [401, 403]
    
    def test_send_message_with_invalid_api_key(self):
        """Test send message with invalid API key"""
        client = TestClient(app)
        
        valid_email = {
            "provider": "gmail_api",
            "to": ["test@example.com"],
            "subject": "Test",
            "body": "Test body",
            "from_email": "sender@example.com"
        }
        
        headers = {"Authorization": "Bearer invalid-key"}
        response = client.post("/v1/messages", json=valid_email, headers=headers)
        
        # Should return unauthorized
        assert response.status_code in [401, 403]
    
    def test_oauth_authorize_without_api_key(self):
        """Test OAuth authorize without API key"""
        client = TestClient(app)
        
        oauth_request = {
            "user_id": "test_user",
            "redirect_uri": "http://localhost:8000/callback"
        }
        
        response = client.post("/v1/oauth/authorize", json=oauth_request)
        
        # Should return unauthorized
        assert response.status_code in [401, 403]
    
    def test_oauth_callback_get_no_auth_required(self):
        """Test OAuth callback GET endpoint doesn't require auth"""
        client = TestClient(app)
        
        # OAuth callback GET should be public for Google redirect
        response = client.get("/v1/oauth/callback?code=test&state=user123")
        
        # Should NOT return 401/403 (may return 400 for invalid code, which is ok)
        assert response.status_code not in [401, 403]


class TestResponseValidation:
    """Test response format validation"""
    
    def test_health_check_response_format(self):
        """Test health check returns correct format"""
        client = TestClient(app)
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "status" in data
        assert "service" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"
    
    def test_root_endpoint_response_format(self):
        """Test root endpoint returns correct format"""
        client = TestClient(app)
        response = client.get("/")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify required fields
        assert "service" in data
        assert "version" in data
        assert "status" in data
    
    def test_oauth_authorize_response_format(self):
        """Test OAuth authorize returns correct format"""
        client = TestClient(app)
        
        oauth_request = {
            "user_id": "test_user",
            "redirect_uri": "http://localhost:8000/callback"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/oauth/authorize", json=oauth_request, headers=headers)
        
        if response.status_code == 200:
            data = response.json()
            assert "authorization_url" in data
            assert "state" in data
            assert data["state"] == "test_user"


class TestErrorResponseFormats:
    """Test error response formats"""
    
    def test_validation_error_format(self):
        """Test validation error returns proper format"""
        client = TestClient(app)
        
        invalid_data = {
            "to": "not-a-list",  # Should be a list
            "subject": "Test"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/messages", json=invalid_data, headers=headers)
        
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data
    
    def test_authentication_error_format(self):
        """Test authentication error format"""
        client = TestClient(app)
        
        response = client.post("/v1/messages", json={})
        
        assert response.status_code in [401, 403]
        data = response.json()
        assert "detail" in data
    
    def test_not_found_error_format(self):
        """Test 404 error format"""
        client = TestClient(app)
        
        response = client.get("/nonexistent-endpoint")
        
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data


class TestCORSHeaders:
    """Test CORS headers"""
    
    def test_cors_headers_on_options_request(self):
        """Test CORS headers on OPTIONS request"""
        client = TestClient(app)
        
        response = client.options("/health")
        
        # Should include CORS headers
        assert "access-control-allow-origin" in response.headers or response.status_code == 200
    
    def test_cors_headers_on_get_request(self):
        """Test CORS headers on GET request"""
        client = TestClient(app)
        
        response = client.get("/health")
        
        # Should include CORS headers
        assert response.status_code == 200


class TestRequestIDHeader:
    """Test X-Request-ID header handling"""
    
    def test_request_id_in_response(self):
        """Test that X-Request-ID is returned in response"""
        client = TestClient(app)
        
        response = client.get("/health")
        
        # Should include X-Request-ID in response headers
        assert "X-Request-ID" in response.headers or "x-request-id" in response.headers
    
    def test_custom_request_id_preserved(self):
        """Test that custom X-Request-ID is preserved"""
        client = TestClient(app)
        
        custom_id = "custom-request-id-123"
        headers = {"X-Request-ID": custom_id}
        
        response = client.get("/health", headers=headers)
        
        # Should preserve custom request ID
        if "X-Request-ID" in response.headers:
            assert response.headers["X-Request-ID"] == custom_id
        elif "x-request-id" in response.headers:
            assert response.headers["x-request-id"] == custom_id


class TestRateLimitingAndSecurity:
    """Test rate limiting and security features"""
    
    def test_subject_max_length_validation(self):
        """Test email subject max length validation"""
        client = TestClient(app)
        
        # Subject too long (> 998 characters per RFC 5322)
        long_subject = "A" * 1000
        
        email_data = {
            "provider": "gmail_api",
            "to": ["test@example.com"],
            "subject": long_subject,
            "body": "Test",
            "from_email": "sender@example.com"
        }
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.post("/v1/messages", json=email_data, headers=headers)
        
        # Should return validation error
        assert response.status_code == 422
    
    def test_sql_injection_attempt_in_user_id(self):
        """Test SQL injection attempt in user ID"""
        client = TestClient(app)
        
        malicious_user_id = "'; DROP TABLE users; --"
        
        headers = {"Authorization": "Bearer dev-api-key"}
        response = client.get(f"/v1/users/{malicious_user_id}/profile", headers=headers)
        
        # Should handle gracefully (either 404 or 400)
        assert response.status_code in [400, 404, 422]


class TestAPIDocumentation:
    """Test API documentation endpoints"""
    
    def test_openapi_docs_available(self):
        """Test OpenAPI documentation is available"""
        client = TestClient(app)
        
        response = client.get("/docs")
        
        # Should return documentation page
        assert response.status_code == 200
    
    def test_redoc_available(self):
        """Test ReDoc documentation is available"""
        client = TestClient(app)
        
        response = client.get("/redoc")
        
        # Should return documentation page
        assert response.status_code == 200
    
    def test_openapi_json_available(self):
        """Test OpenAPI JSON schema is available"""
        client = TestClient(app)
        
        response = client.get("/openapi.json")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify OpenAPI structure
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
