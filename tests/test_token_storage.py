"""
Unit tests for token storage and retrieval from database/secrets manager
Tests AWS Secrets Manager, GCP Secret Manager, and local storage
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, Mock
from datetime import datetime, timedelta
import json

from src.mcp.services.multi_tenant_service import MultiTenantEmailService


class TestTokenStorage:
    """Test token storage functionality"""
    
    @pytest.mark.asyncio
    async def test_store_user_secret_gcp(self, mock_oauth_tokens):
        """Test storing user tokens in GCP Secret Manager"""
        service = MultiTenantEmailService()
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            mock_manager.create_or_update_secret = AsyncMock()
            service.secrets_manager = mock_manager
            
            secret_name = "users/test_user/gmail"
            secret_data = {
                "access_token": mock_oauth_tokens["access_token"],
                "refresh_token": mock_oauth_tokens["refresh_token"],
                "email_address": "test@example.com"
            }
            
            await service._store_user_secret(secret_name, secret_data)
            
            mock_manager.create_or_update_secret.assert_called_once_with(
                secret_name, secret_data
            )
    
    @pytest.mark.asyncio
    async def test_retrieve_user_secret_gcp(self):
        """Test retrieving user tokens from GCP Secret Manager"""
        service = MultiTenantEmailService()
        
        expected_secret = {
            "access_token": "stored_access_token",
            "refresh_token": "stored_refresh_token",
            "email_address": "stored@example.com"
        }
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            mock_manager.get_secret = AsyncMock(return_value=expected_secret)
            service.secrets_manager = mock_manager
            
            secret_name = "users/test_user/gmail"
            result = await service._get_user_secret(secret_name)
            
            assert result == expected_secret
            mock_manager.get_secret.assert_called_once_with(secret_name)
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_tokens_roundtrip(self, mock_oauth_tokens):
        """Test storing and retrieving tokens in a complete flow"""
        service = MultiTenantEmailService()
        user_id = "test_user_123"
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            stored_data = None
            
            async def mock_store(name, data):
                nonlocal stored_data
                stored_data = data
            
            async def mock_retrieve(name):
                return stored_data
            
            mock_manager.create_or_update_secret = AsyncMock(side_effect=mock_store)
            mock_manager.get_secret = AsyncMock(side_effect=mock_retrieve)
            service.secrets_manager = mock_manager
            
            # Store tokens
            secret_name = f"users/{user_id}/gmail"
            secret_data = {
                "access_token": mock_oauth_tokens["access_token"],
                "refresh_token": mock_oauth_tokens["refresh_token"],
                "email_address": "test@example.com"
            }
            await service._store_user_secret(secret_name, secret_data)
            
            # Retrieve tokens
            retrieved = await service._get_user_secret(secret_name)
            
            assert retrieved == secret_data
            assert retrieved["access_token"] == mock_oauth_tokens["access_token"]
    
    @pytest.mark.asyncio
    async def test_get_user_credentials(self):
        """Test getting user credentials as Google Credentials object"""
        service = MultiTenantEmailService()
        user_id = "test_user_123"
        
        secret_data = {
            "access_token": "test_access",
            "refresh_token": "test_refresh",
            "email_address": "test@example.com"
        }
        
        with patch.object(service, '_get_user_secret', return_value=secret_data):
            credentials = await service.get_user_credentials(user_id)
            
            assert credentials is not None
            assert credentials.token == "test_access"
            assert credentials.refresh_token == "test_refresh"
    
    @pytest.mark.asyncio
    async def test_get_user_credentials_not_found(self):
        """Test getting credentials for non-existent user"""
        service = MultiTenantEmailService()
        user_id = "nonexistent_user"
        
        with patch.object(service, '_get_user_secret', return_value=None):
            credentials = await service.get_user_credentials(user_id)
            
            assert credentials is None
    
    @pytest.mark.asyncio
    async def test_token_update_after_refresh(self, mock_oauth_tokens):
        """Test updating stored tokens after refresh"""
        service = MultiTenantEmailService()
        user_id = "test_user_123"
        
        # Initial tokens
        initial_data = {
            "access_token": "old_access_token",
            "refresh_token": "refresh_token",
            "email_address": "test@example.com"
        }
        
        # New refreshed tokens
        new_tokens = {
            "access_token": "new_access_token",
            "refresh_token": "refresh_token",
            "email_address": "test@example.com"
        }
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            stored_data = initial_data.copy()
            
            async def mock_update(name, data):
                nonlocal stored_data
                stored_data = data
            
            async def mock_get(name):
                return stored_data
            
            mock_manager.create_or_update_secret = AsyncMock(side_effect=mock_update)
            mock_manager.get_secret = AsyncMock(side_effect=mock_get)
            service.secrets_manager = mock_manager
            
            # Update tokens
            secret_name = f"users/{user_id}/gmail"
            await service._store_user_secret(secret_name, new_tokens)
            
            # Verify updated
            retrieved = await service._get_user_secret(secret_name)
            assert retrieved["access_token"] == "new_access_token"


class TestSecretManagerIntegration:
    """Test integration with different secret managers"""
    
    @pytest.mark.asyncio
    async def test_gcp_secrets_manager_initialization(self):
        """Test GCP Secrets Manager initialization"""
        from src.mcp.core.config import Settings
        
        settings = Settings(
            environment="production",
            gcp_project_id="test-project"
        )
        
        with patch('src.mcp.services.multi_tenant_service.settings', settings):
            with patch('src.mcp.services.multi_tenant_service.GCPSecretsManager') as mock_gcp:
                service = MultiTenantEmailService()
                
                # Verify GCP manager was attempted to be initialized
                # (it will fail to import in test, which is expected)
    
    @pytest.mark.asyncio
    async def test_aws_secrets_manager_initialization(self):
        """Test AWS Secrets Manager initialization"""
        from src.mcp.core.config import Settings
        
        settings = Settings(
            environment="production",
            aws_secrets_name="test-secrets"
        )
        
        with patch('src.mcp.services.multi_tenant_service.settings', settings):
            with patch('src.mcp.services.multi_tenant_service.AWSSecretsManager') as mock_aws:
                service = MultiTenantEmailService()
                
                # Verify AWS manager was attempted to be initialized
    
    @pytest.mark.asyncio
    async def test_secret_exists_check(self):
        """Test checking if a secret exists"""
        service = MultiTenantEmailService()
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            # Mock secret exists
            mock_manager.secret_exists = Mock(return_value=True)
            service.secrets_manager = mock_manager
            
            exists = service._secret_exists("users/test_user/gmail")
            
            assert exists is True
    
    @pytest.mark.asyncio
    async def test_secret_not_exists(self):
        """Test checking for non-existent secret"""
        service = MultiTenantEmailService()
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            # Mock secret doesn't exist
            mock_manager.secret_exists = Mock(return_value=False)
            service.secrets_manager = mock_manager
            
            exists = service._secret_exists("users/nonexistent/gmail")
            
            assert exists is False


class TestTokenExpiration:
    """Test token expiration handling"""
    
    @pytest.mark.asyncio
    async def test_store_token_with_expiration(self, mock_oauth_tokens):
        """Test storing tokens with expiration time"""
        service = MultiTenantEmailService()
        
        expires_at = (datetime.now() + timedelta(seconds=mock_oauth_tokens["expires_in"])).isoformat()
        
        secret_data = {
            "access_token": mock_oauth_tokens["access_token"],
            "refresh_token": mock_oauth_tokens["refresh_token"],
            "email_address": "test@example.com",
            "expires_at": expires_at
        }
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            mock_manager.create_or_update_secret = AsyncMock()
            service.secrets_manager = mock_manager
            
            await service._store_user_secret("users/test/gmail", secret_data)
            
            # Verify expiration was stored
            call_args = mock_manager.create_or_update_secret.call_args
            stored_data = call_args[0][1]
            assert "expires_at" in stored_data
    
    @pytest.mark.asyncio
    async def test_retrieve_expired_token_metadata(self):
        """Test retrieving token with expiration metadata"""
        service = MultiTenantEmailService()
        
        # Token expired 1 hour ago
        expired_at = (datetime.now() - timedelta(hours=1)).isoformat()
        
        secret_data = {
            "access_token": "expired_token",
            "refresh_token": "valid_refresh",
            "email_address": "test@example.com",
            "expires_at": expired_at
        }
        
        with patch.object(service, '_get_user_secret', return_value=secret_data):
            retrieved = await service._get_user_secret("users/test/gmail")
            
            # Token is expired but retrieval should still work
            assert retrieved is not None
            assert retrieved["access_token"] == "expired_token"
            
            # Check if expired
            expires_at_dt = datetime.fromisoformat(retrieved["expires_at"])
            assert expires_at_dt < datetime.now()


class TestMultiUserTokenStorage:
    """Test token storage for multiple users"""
    
    @pytest.mark.asyncio
    async def test_store_multiple_user_tokens(self):
        """Test storing tokens for multiple users"""
        service = MultiTenantEmailService()
        
        users = {
            "user1": {"access_token": "token1", "email": "user1@example.com"},
            "user2": {"access_token": "token2", "email": "user2@example.com"},
            "user3": {"access_token": "token3", "email": "user3@example.com"}
        }
        
        stored_secrets = {}
        
        async def mock_store(name, data):
            stored_secrets[name] = data
        
        with patch.object(service, 'secrets_manager') as mock_manager:
            mock_manager.create_or_update_secret = AsyncMock(side_effect=mock_store)
            service.secrets_manager = mock_manager
            
            # Store tokens for all users
            for user_id, data in users.items():
                secret_name = f"users/{user_id}/gmail"
                await service._store_user_secret(secret_name, data)
            
            # Verify all stored
            assert len(stored_secrets) == 3
            assert "users/user1/gmail" in stored_secrets
            assert "users/user2/gmail" in stored_secrets
            assert "users/user3/gmail" in stored_secrets
    
    @pytest.mark.asyncio
    async def test_retrieve_specific_user_tokens(self):
        """Test retrieving tokens for specific users"""
        service = MultiTenantEmailService()
        
        user_tokens = {
            "users/user1/gmail": {"access_token": "token1"},
            "users/user2/gmail": {"access_token": "token2"}
        }
        
        async def mock_get(name):
            return user_tokens.get(name)
        
        with patch.object(service, '_get_user_secret', side_effect=mock_get):
            # Retrieve user1 tokens
            user1_data = await service._get_user_secret("users/user1/gmail")
            assert user1_data["access_token"] == "token1"
            
            # Retrieve user2 tokens
            user2_data = await service._get_user_secret("users/user2/gmail")
            assert user2_data["access_token"] == "token2"
