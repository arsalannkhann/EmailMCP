"""
Unit tests for OAuth authentication and token refresh flows
Tests Gmail OAuth2 authentication, token refresh, and token expiry handling
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
import time
from datetime import datetime, timedelta

from src.mcp.providers.gmail_api import GmailAPIProvider
from src.mcp.services.multi_tenant_service import MultiTenantEmailService
from src.mcp.schemas.requests import EmailRequest


class TestGmailOAuthFlow:
    """Test Gmail OAuth authentication flow"""
    
    @pytest.mark.asyncio
    async def test_generate_oauth_url(self, mock_settings):
        """Test OAuth URL generation"""
        service = MultiTenantEmailService()
        service.gmail_client_id = "test_client_id"
        
        user_id = "test_user_123"
        redirect_uri = "http://localhost:8000/callback"
        
        oauth_url = await service.generate_oauth_url(user_id, redirect_uri)
        
        # Verify URL structure
        assert "https://accounts.google.com/o/oauth2/v2/auth" in oauth_url
        assert "client_id=test_client_id" in oauth_url
        assert "redirect_uri=http" in oauth_url
        assert f"state={user_id}" in oauth_url
        # Scope is URL encoded, check for gmail.send in any form
        assert "gmail.send" in oauth_url
        assert "access_type=offline" in oauth_url
        assert "prompt=consent" in oauth_url
    
    @pytest.mark.asyncio
    async def test_oauth_callback_processing(self, mock_oauth_tokens):
        """Test OAuth callback token exchange"""
        service = MultiTenantEmailService()
        service.gmail_client_id = "test_client_id"
        service.gmail_client_secret = "test_client_secret"
        service.secrets_manager = None  # Disable secrets manager for test
        
        # Mock requests.post which is imported inside the method
        with patch('requests.post') as mock_post, \
             patch('googleapiclient.discovery.build') as mock_build:
            
            # Mock token exchange response
            mock_response = MagicMock()
            mock_response.json.return_value = mock_oauth_tokens
            mock_response.raise_for_status = MagicMock()
            mock_post.return_value = mock_response
            
            # Mock Gmail API profile response with full mock chain
            mock_profile_result = MagicMock()
            mock_profile_result.execute.return_value = {'emailAddress': 'test@example.com'}
            
            mock_get_profile = MagicMock()
            mock_get_profile.return_value = mock_profile_result
            
            mock_users = MagicMock()
            mock_users.getProfile = mock_get_profile
            
            mock_service = MagicMock()
            mock_service.users.return_value = mock_users
            mock_build.return_value = mock_service
            
            # Process callback
            result = await service.process_oauth_callback(
                authorization_code="test_code",
                user_id="test_user_123",
                redirect_uri="http://localhost:8000/callback"
            )
            
            # Verify result
            assert result.user_id == "test_user_123"
            assert result.email_address == "test@example.com"
            assert result.gmail_connected is True
            
            # Verify token exchange was called correctly
            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert call_args[0][0] == 'https://oauth2.googleapis.com/token'
            assert call_args[1]['data']['code'] == 'test_code'
            assert call_args[1]['data']['grant_type'] == 'authorization_code'


class TestTokenRefresh:
    """Test token refresh functionality"""
    
    @pytest.mark.asyncio
    async def test_token_refresh_success(self, sample_email_request):
        """Test successful token refresh"""
        provider = GmailAPIProvider()
        provider.client_id = "test_client_id"
        provider.client_secret = "test_client_secret"
        provider.refresh_token = "test_refresh_token"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Mock successful token refresh
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "new_access_token",
                "expires_in": 3600,
                "token_type": "Bearer"
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Refresh token
            access_token = await provider._refresh_access_token()
            
            assert access_token == "new_access_token"
            assert provider._access_token == "new_access_token"
            assert provider._token_expires_at is not None
            assert provider._token_expires_at > time.time()
    
    @pytest.mark.asyncio
    async def test_token_refresh_failure(self):
        """Test token refresh failure handling"""
        provider = GmailAPIProvider()
        provider.client_id = "test_client_id"
        provider.client_secret = "test_client_secret"
        provider.refresh_token = "invalid_refresh_token"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Mock failed token refresh
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.text = "Invalid refresh token"
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                await provider._refresh_access_token()
            
            assert "Token refresh failed" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_token_expiry_detection(self):
        """Test that expired tokens are detected and refreshed"""
        provider = GmailAPIProvider()
        provider.client_id = "test_client_id"
        provider.client_secret = "test_client_secret"
        provider.refresh_token = "test_refresh_token"
        
        # Set expired token
        provider._access_token = "old_expired_token"
        provider._token_expires_at = time.time() - 100  # Expired 100 seconds ago
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Mock successful token refresh
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "refreshed_access_token",
                "expires_in": 3600
            }
            
            mock_client = AsyncMock()
            mock_client.__aenter__.return_value.post = AsyncMock(return_value=mock_response)
            mock_client_class.return_value = mock_client
            
            # Get valid token should trigger refresh
            access_token = await provider._get_valid_access_token()
            
            assert access_token == "refreshed_access_token"
            assert access_token != "old_expired_token"
    
    @pytest.mark.asyncio
    async def test_token_reuse_when_valid(self):
        """Test that valid tokens are reused without refresh"""
        provider = GmailAPIProvider()
        provider.client_id = "test_client_id"
        provider.client_secret = "test_client_secret"
        provider.refresh_token = "test_refresh_token"
        
        # Set valid token (expires in 1 hour)
        provider._access_token = "valid_token"
        provider._token_expires_at = time.time() + 3600
        
        # Get valid token should NOT trigger refresh
        access_token = await provider._get_valid_access_token()
        
        # Should return existing token without calling refresh
        assert access_token == "valid_token"


class TestInvalidTokenHandling:
    """Test handling of invalid or expired tokens"""
    
    @pytest.mark.asyncio
    async def test_email_send_with_expired_token(self, sample_email_request):
        """Test email sending with expired token triggers refresh"""
        provider = GmailAPIProvider()
        provider.client_id = "test_client_id"
        provider.client_secret = "test_client_secret"
        provider.refresh_token = "test_refresh_token"
        
        # Set expired token
        provider._access_token = "expired_token"
        provider._token_expires_at = time.time() - 100
        
        with patch('httpx.AsyncClient') as mock_client_class:
            # Mock token refresh and email send
            mock_refresh_response = MagicMock()
            mock_refresh_response.status_code = 200
            mock_refresh_response.json.return_value = {
                "access_token": "new_valid_token",
                "expires_in": 3600
            }
            
            mock_send_response = MagicMock()
            mock_send_response.status_code = 200
            mock_send_response.json.return_value = {
                "id": "message_id_123",
                "threadId": "thread_id_123"
            }
            
            mock_client = AsyncMock()
            mock_post = AsyncMock(side_effect=[mock_refresh_response, mock_send_response])
            mock_client.__aenter__.return_value.post = mock_post
            mock_client_class.return_value = mock_client
            
            # Send email
            response = await provider.send(sample_email_request)
            
            # Should succeed with refreshed token
            assert response.status == "success"
            assert response.message_id == "message_id_123"
            
            # Verify refresh was called
            assert mock_post.call_count == 2  # refresh + send
    
    @pytest.mark.asyncio
    async def test_oauth_callback_with_invalid_code(self):
        """Test OAuth callback with invalid authorization code"""
        service = MultiTenantEmailService()
        service.gmail_client_id = "test_client_id"
        service.gmail_client_secret = "test_client_secret"
        
        with patch('requests.post') as mock_post:
            # Mock failed token exchange
            mock_response = MagicMock()
            mock_response.raise_for_status.side_effect = Exception("Invalid authorization code")
            mock_post.return_value = mock_response
            
            # Should raise exception
            with pytest.raises(Exception) as exc_info:
                await service.process_oauth_callback(
                    authorization_code="invalid_code",
                    user_id="test_user_123"
                )
            
            assert "Invalid authorization code" in str(exc_info.value)
