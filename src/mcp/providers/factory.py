from typing import Optional
from ..providers.base import EmailProvider
from ..providers.smtp_client import SmtpClient
from ..providers.gmail_api import GmailAPIProvider
from ..providers.gmail_api_production import GmailAPIProductionProvider
from ..core.config import settings
from ..core.logging import log

class EmailProviderFactory:
    """Factory class to create appropriate email providers"""
    
    @staticmethod
    def create_provider(provider_type: Optional[str] = None) -> EmailProvider:
        """
        Create email provider based on configuration and availability
        
        Args:
            provider_type: Specific provider type to create (gmail_api, smtp)
                         If None, will choose best available provider
        
        Returns:
            EmailProvider instance
        """
        if provider_type:
            return EmailProviderFactory._create_specific_provider(provider_type)
        
        # Auto-select best available provider
        return EmailProviderFactory._create_best_available_provider()
    
    @staticmethod
    def _create_specific_provider(provider_type: str) -> EmailProvider:
        """Create a specific provider type"""
        if provider_type == "gmail_api":
            if settings.is_production:
                provider = GmailAPIProductionProvider()
            else:
                provider = GmailAPIProvider()
                
            if provider.is_configured():
                log.info(f"Created Gmail API provider for {settings.environment}")
                return provider
            else:
                log.warning("Gmail API not configured, falling back to SMTP")
                return SmtpClient()
                
        elif provider_type == "smtp":
            provider = SmtpClient()
            if provider.is_configured():
                log.info("Created SMTP provider")
                return provider
            else:
                log.error("SMTP not configured")
                raise ValueError("SMTP provider not configured")
        
        else:
            log.error(f"Unknown provider type: {provider_type}")
            raise ValueError(f"Unknown provider type: {provider_type}")
    
    @staticmethod
    def _create_best_available_provider() -> EmailProvider:
        """Create the best available provider based on configuration"""
        provider_priority = settings.get_email_provider_priority()
        
        for provider_type in provider_priority:
            try:
                provider = EmailProviderFactory._create_specific_provider(provider_type)
                log.info(f"Selected {provider_type} as email provider")
                return provider
            except ValueError:
                log.warning(f"{provider_type} not available, trying next option")
                continue
        
        # If no providers are configured, return SMTP as fallback
        log.warning("No email providers configured, returning basic SMTP client")
        return SmtpClient()
    
    @staticmethod
    def get_available_providers() -> list[str]:
        """Get list of available and configured providers"""
        available = []
        
        # Check Gmail API
        if settings.is_production:
            gmail_provider = GmailAPIProductionProvider()
        else:
            gmail_provider = GmailAPIProvider()
            
        if gmail_provider.is_configured():
            available.append("gmail_api")
        
        # Check SMTP
        smtp_provider = SmtpClient()
        if smtp_provider.is_configured():
            available.append("smtp")
        
        return available

# Convenience function for easy provider creation
def get_email_provider(provider_type: Optional[str] = None) -> EmailProvider:
    """Get email provider instance"""
    return EmailProviderFactory.create_provider(provider_type)