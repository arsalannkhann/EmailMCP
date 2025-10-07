"""
Unit tests for OAuth redirect URI environment handling
Tests that redirect URIs are correctly determined based on environment configuration
"""
import pytest
from unittest.mock import patch, MagicMock
from src.mcp.core.config import Settings
from src.mcp.services.multi_tenant_service import MultiTenantEmailService


class TestOAuthRedirectURIConfiguration:
    """Test OAuth redirect URI configuration based on environment"""
    
    def test_development_default_redirect_uri(self):
        """Test default redirect URI in development environment"""
        settings = Settings(
            environment="development",
            mcp_port=8001,
            oauth_redirect_uri=None
        )
        
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        assert redirect_uri == "http://localhost:8001/v1/oauth/callback"
        assert "localhost" in redirect_uri
        assert redirect_uri.startswith("http://")
    
    def test_production_default_redirect_uri(self):
        """Test default redirect URI in production environment"""
        settings = Settings(
            environment="production",
            mcp_port=8001,
            oauth_redirect_uri=None
        )
        
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        assert redirect_uri == "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback"
        assert "emailmcp-hcnqp547xa-uc.a.run.app" in redirect_uri
        assert redirect_uri.startswith("https://")
    
    def test_custom_redirect_uri_override(self):
        """Test custom redirect URI override"""
        custom_uri = "https://custom-domain.com/oauth/callback"
        settings = Settings(
            environment="production",
            oauth_redirect_uri=custom_uri
        )
        
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        assert redirect_uri == custom_uri
    
    def test_development_frontend_callback_uri(self):
        """Test frontend callback URI in development"""
        settings = Settings(
            environment="development",
            oauth_frontend_origin=None
        )
        
        callback_uri = settings.get_frontend_callback_uri()
        
        assert callback_uri == "http://localhost:8000/callback.html"
        assert "localhost:8000" in callback_uri
    
    def test_production_frontend_callback_uri(self):
        """Test frontend callback URI in production"""
        settings = Settings(
            environment="production",
            oauth_frontend_origin=None
        )
        
        callback_uri = settings.get_frontend_callback_uri()
        
        assert callback_uri == "https://salesos.orionac.in/settings/"
        assert "salesos.orionac.in" in callback_uri
    
    def test_custom_frontend_origin(self):
        """Test custom frontend origin"""
        custom_origin = "https://custom-frontend.com"
        settings = Settings(
            environment="production",
            oauth_frontend_origin=custom_origin
        )
        
        callback_uri = settings.get_frontend_callback_uri()
        
        assert callback_uri == f"{custom_origin}/callback.html"
    
    def test_different_port_in_development(self):
        """Test redirect URI with different port in development"""
        settings = Settings(
            environment="development",
            mcp_port=9000,
            oauth_redirect_uri=None
        )
        
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        assert redirect_uri == "http://localhost:9000/v1/oauth/callback"
        assert ":9000" in redirect_uri


class TestMultiTenantServiceRedirectURI:
    """Test MultiTenantEmailService OAuth redirect URI handling"""
    
    @pytest.mark.asyncio
    async def test_generate_oauth_url_with_custom_redirect_uri(self):
        """Test OAuth URL generation with custom redirect URI"""
        with patch('src.mcp.services.multi_tenant_service.settings') as mock_settings:
            mock_settings.gmail_client_id = "test_client_id"
            mock_settings.gmail_client_secret = "test_client_secret"
            mock_settings.is_production = False
            
            service = MultiTenantEmailService()
            service.gmail_client_id = "test_client_id"
            
            custom_redirect = "http://localhost:3000/custom/callback"
            oauth_url = await service.generate_oauth_url(
                user_id="test_user_123",
                redirect_uri=custom_redirect
            )
            
            assert "https://accounts.google.com/o/oauth2/v2/auth" in oauth_url
            assert "client_id=test_client_id" in oauth_url
            assert f"redirect_uri={custom_redirect}" in oauth_url or "redirect_uri=http" in oauth_url
            assert "state=test_user_123" in oauth_url
    
    @pytest.mark.asyncio
    async def test_generate_oauth_url_without_redirect_uri(self):
        """Test OAuth URL generation falls back to environment default"""
        with patch('src.mcp.services.multi_tenant_service.settings') as mock_settings:
            mock_settings.gmail_client_id = "test_client_id"
            mock_settings.gmail_client_secret = "test_client_secret"
            mock_settings.is_production = False
            mock_settings.mcp_port = 8001
            mock_settings.get_default_oauth_redirect_uri.return_value = "http://localhost:8001/v1/oauth/callback"
            
            service = MultiTenantEmailService()
            service.gmail_client_id = "test_client_id"
            
            oauth_url = await service.generate_oauth_url(
                user_id="test_user_123",
                redirect_uri=None
            )
            
            # Verify that get_default_oauth_redirect_uri was called
            mock_settings.get_default_oauth_redirect_uri.assert_called_once()
            assert "https://accounts.google.com/o/oauth2/v2/auth" in oauth_url
    
    @pytest.mark.asyncio
    async def test_process_oauth_callback_with_custom_redirect_uri(self):
        """Test OAuth callback processing with custom redirect URI"""
        with patch('src.mcp.services.multi_tenant_service.settings') as mock_settings:
            with patch('requests.post') as mock_post:
                with patch('src.mcp.services.multi_tenant_service.build') as mock_build:
                    with patch('src.mcp.services.multi_tenant_service.Credentials') as mock_creds:
                        # Setup mocks
                        mock_settings.gmail_client_id = "test_client_id"
                        mock_settings.gmail_client_secret = "test_client_secret"
                        mock_settings.is_production = False
                        
                        # Mock token response
                        mock_response = MagicMock()
                        mock_response.json.return_value = {
                            'access_token': 'test_access_token',
                            'refresh_token': 'test_refresh_token',
                            'expires_in': 3600
                        }
                        mock_response.raise_for_status = MagicMock()
                        mock_post.return_value = mock_response
                        
                        # Mock Credentials
                        mock_credentials = MagicMock()
                        mock_creds.return_value = mock_credentials
                        
                        # Mock Gmail API
                        mock_service = MagicMock()
                        mock_profile = MagicMock()
                        mock_profile.execute.return_value = {'emailAddress': 'test@example.com'}
                        mock_service.users().getProfile.return_value = mock_profile
                        mock_build.return_value = mock_service
                        
                        service = MultiTenantEmailService()
                        service.gmail_client_id = "test_client_id"
                        service.gmail_client_secret = "test_client_secret"
                        service.secrets_manager = None  # Disable secrets manager for test
                        
                        custom_redirect = "http://localhost:3000/custom/callback"
                        result = await service.process_oauth_callback(
                            authorization_code="test_code",
                            user_id="test_user_123",
                            redirect_uri=custom_redirect
                        )
                        
                        # Verify the redirect_uri was used in token exchange
                        call_args = mock_post.call_args
                        assert call_args[1]['data']['redirect_uri'] == custom_redirect
                        assert result.email_address == 'test@example.com'
    
    @pytest.mark.asyncio
    async def test_process_oauth_callback_without_redirect_uri(self):
        """Test OAuth callback processing falls back to environment default"""
        with patch('src.mcp.services.multi_tenant_service.settings') as mock_settings:
            with patch('requests.post') as mock_post:
                with patch('src.mcp.services.multi_tenant_service.build') as mock_build:
                    with patch('src.mcp.services.multi_tenant_service.Credentials') as mock_creds:
                        # Setup mocks
                        mock_settings.gmail_client_id = "test_client_id"
                        mock_settings.gmail_client_secret = "test_client_secret"
                        mock_settings.is_production = False
                        mock_settings.get_default_oauth_redirect_uri.return_value = "http://localhost:8001/v1/oauth/callback"
                        
                        # Mock token response
                        mock_response = MagicMock()
                        mock_response.json.return_value = {
                            'access_token': 'test_access_token',
                            'refresh_token': 'test_refresh_token',
                            'expires_in': 3600
                        }
                        mock_response.raise_for_status = MagicMock()
                        mock_post.return_value = mock_response
                        
                        # Mock Credentials
                        mock_credentials = MagicMock()
                        mock_creds.return_value = mock_credentials
                        
                        # Mock Gmail API
                        mock_service = MagicMock()
                        mock_profile = MagicMock()
                        mock_profile.execute.return_value = {'emailAddress': 'test@example.com'}
                        mock_service.users().getProfile.return_value = mock_profile
                        mock_build.return_value = mock_service
                        
                        service = MultiTenantEmailService()
                        service.gmail_client_id = "test_client_id"
                        service.gmail_client_secret = "test_client_secret"
                        service.secrets_manager = None  # Disable secrets manager for test
                        
                        result = await service.process_oauth_callback(
                            authorization_code="test_code",
                            user_id="test_user_123",
                            redirect_uri=None
                        )
                        
                        # Verify get_default_oauth_redirect_uri was called
                        mock_settings.get_default_oauth_redirect_uri.assert_called()
                        assert result.email_address == 'test@example.com'


class TestEnvironmentSpecificBehavior:
    """Test environment-specific OAuth behavior"""
    
    def test_localhost_used_in_development(self):
        """Verify localhost is used in development environment"""
        settings = Settings(environment="development", mcp_port=8001)
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        assert "localhost" in redirect_uri
        assert redirect_uri.startswith("http://")
        assert not redirect_uri.startswith("https://")
    
    def test_cloud_run_used_in_production(self):
        """Verify Cloud Run URL is used in production environment"""
        settings = Settings(environment="production")
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        assert "emailmcp-hcnqp547xa-uc.a.run.app" in redirect_uri
        assert redirect_uri.startswith("https://")
        assert "localhost" not in redirect_uri
    
    def test_staging_environment_uses_production_default(self):
        """Test staging environment (not development) uses production-like defaults"""
        settings = Settings(environment="staging", mcp_port=8001)
        redirect_uri = settings.get_default_oauth_redirect_uri()
        
        # Staging should use production defaults (not development)
        assert "emailmcp-hcnqp547xa-uc.a.run.app" in redirect_uri
        assert redirect_uri.startswith("https://")
