from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Service Configuration
    mcp_api_key: str = "dev-api-key"
    mcp_host: str = "0.0.0.0"
    mcp_port: int = 8001
    
    # Environment Configuration
    environment: str = "development"  # development, staging, production
    
    # Flask Auth Server
    auth_server_url: str = "http://localhost:5000"
    auth_server_timeout: int = 10
    
    # AWS Configuration
    aws_region: str = "us-east-1"
    aws_secrets_name: Optional[str] = None
    
    # Redis Configuration
    redis_url: str = "redis://localhost:6379/0"
    idempotency_ttl: int = 86400
    
    # Logging
    log_level: str = "INFO"
    
    # Email Provider Credentials
    gmail_client_id: Optional[str] = None
    gmail_client_secret: Optional[str] = None
    gmail_refresh_token: Optional[str] = None
    
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
    
    def get_email_provider_priority(self) -> list[str]:
        """Get email provider priority list"""
        if self.preferred_email_provider == "gmail_api":
            return ["gmail_api", "smtp"]
        else:
            return ["smtp", "gmail_api"]

settings = Settings()
