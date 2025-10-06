from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Service Configuration
    mcp_api_key: str = "emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    
    # Environment Configuration
    environment: str = "production"  # development, staging, production
    
    # Flask Auth Server
    auth_server_url: str = "http://localhost:5000"
    auth_server_timeout: int = 10
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_secrets_name: Optional[str] = None
    
    # GCP Configuration
    gcp_project_id: Optional[str] = "mcporionac"  # Default to our project
    gcp_region: str = "us-central1"
    
    # Firestore Configuration
    firestore_database: str = "(default)"  # Firestore database name
    firestore_timeout: int = 30  # Timeout for Firestore operations
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    idempotency_ttl: int = 86400
    
    # Logging
    log_level: str = "INFO"
    
    # Email Provider Credentials
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_refresh_token: Optional[str] = None
    
    # OAuth Redirect URI Configuration
    # Development default: http://localhost:8001/v1/oauth/callback
    # Production default: https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
    oauth_redirect_uri: Optional[str] = None  # Custom redirect URI override
    oauth_frontend_origin: Optional[str] = None  # Frontend origin for callback pages
    
    outlook_tenant_id: Optional[str] = None
    outlook_client_id: Optional[str] = None
    outlook_client_secret: Optional[str] = None
    
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    
    # Email provider preference (smtp, gmail_api)
    preferred_email_provider: str = "gmail_api"
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment"""
        return self.environment.lower() == "production"
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment"""
        return self.environment.lower() == "development"
    
    @property
    def use_aws_secrets(self) -> bool:
        """Check if should use AWS Secrets Manager"""
        return self.is_production and self.aws_secrets_name is not None
    
    @property
    def use_gcp_secrets(self) -> bool:
        """Check if should use GCP Secret Manager"""
        return self.is_production and self.gcp_project_id is not None
    
    @property
    def use_firestore(self) -> bool:
        """Check if should use Firestore for data persistence"""
        return self.gcp_project_id is not None
    
    def get_email_provider_priority(self) -> list[str]:
        """Get email provider priority list"""
        if self.preferred_email_provider == "gmail_api":
            return ["gmail_api", "smtp"]
        else:
            return ["smtp", "gmail_api"]
    
    def get_default_oauth_redirect_uri(self) -> str:
        """
        Get default OAuth redirect URI based on environment
        
        Returns environment-appropriate redirect URI:
        - Development: http://localhost:8001/v1/oauth/callback
        - Production: https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
        - Custom: Value from oauth_redirect_uri if set
        """
        if self.oauth_redirect_uri:
            return self.oauth_redirect_uri
        
        if self.is_development:
            # Development: Use localhost with configured port
            return f"http://localhost:{self.mcp_port}/v1/oauth/callback"
        else:
            # Production: Use Cloud Run URL
            return "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback"
    
    def get_frontend_callback_uri(self) -> str:
        """
        Get frontend callback page URI based on environment
        
        Returns environment-appropriate frontend callback:
        - Development: http://localhost:8000/callback.html
        - Production: https://salesos.orionac.in/settings/
        - Custom: Value from oauth_frontend_origin + /callback.html if set
        """
        if self.oauth_frontend_origin:
            return f"{self.oauth_frontend_origin}/callback.html"
        
        if self.is_development:
            # Development: Frontend typically runs on port 8000
            return "http://localhost:8000/callback.html"
        else:
            # Production: Use production frontend URL
            return "https://salesos.orionac.in/settings/"

settings = Settings()