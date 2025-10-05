"""
Pytest configuration and shared fixtures for EmailMCP tests
"""
import pytest
import asyncio
from typing import AsyncGenerator, Generator
from unittest.mock import Mock, AsyncMock, MagicMock
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.mcp.schemas.requests import EmailRequest, MultiTenantEmailRequest
from src.mcp.core.config import Settings


@pytest.fixture(scope="session")
def event_loop() -> Generator:
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_settings():
    """Mock settings for testing"""
    settings = Settings(
        mcp_api_key="test-api-key",
        environment="test",
        gmail_client_id="test_client_id",
        gmail_client_secret="test_client_secret",
        gmail_refresh_token="test_refresh_token",
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_username="test@example.com",
        smtp_password="test_password"
    )
    return settings


@pytest.fixture
def sample_email_request():
    """Sample email request for testing"""
    return EmailRequest(
        provider="auto",
        to=["recipient@example.com"],
        subject="Test Email",
        body="This is a test email body",
        from_email="sender@example.com",
        html=False
    )


@pytest.fixture
def sample_multitenant_email_request():
    """Sample multi-tenant email request for testing"""
    return MultiTenantEmailRequest(
        to=["recipient@example.com"],
        subject="Test Email",
        body="This is a test email body",
        body_type="text"
    )


@pytest.fixture
def mock_oauth_tokens():
    """Mock OAuth token response"""
    return {
        "access_token": "test_access_token",
        "refresh_token": "test_refresh_token",
        "expires_in": 3600,
        "token_type": "Bearer",
        "scope": "https://www.googleapis.com/auth/gmail.send"
    }


@pytest.fixture
def mock_gmail_credentials():
    """Mock Gmail credentials"""
    from google.oauth2.credentials import Credentials
    return Credentials(
        token="test_access_token",
        refresh_token="test_refresh_token",
        token_uri="https://oauth2.googleapis.com/token",
        client_id="test_client_id",
        client_secret="test_client_secret"
    )


@pytest.fixture
def mock_httpx_client():
    """Mock httpx AsyncClient for API calls"""
    client = AsyncMock()
    return client


@pytest.fixture
def mock_secrets_manager():
    """Mock secrets manager (AWS/GCP)"""
    manager = AsyncMock()
    manager.get_secret = AsyncMock(return_value={
        "access_token": "test_token",
        "refresh_token": "test_refresh",
        "email_address": "test@example.com"
    })
    manager.store_secret = AsyncMock()
    return manager
