import asyncio
import sys
import os

# Add the parent directory to the path so we can import from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.mcp.providers.factory import get_email_provider
from src.mcp.schemas.requests import EmailRequest
from src.mcp.core.config import settings

async def test_gmail_api():
    """Test Gmail API provider"""
    print("🧪 Testing Gmail API Provider")
    print("=" * 40)
    
    # Get the email provider (will auto-select best available)
    try:
        provider = get_email_provider("gmail_api")
        print(f"✅ Gmail API provider created successfully")
        print(f"📋 Provider type: {type(provider).__name__}")
        print(f"🔧 Is configured: {provider.is_configured()}")
        print(f"🌍 Environment: {settings.environment}")
        print(f"☁️ Using AWS Secrets: {settings.use_aws_secrets}")
        
    except Exception as e:
        print(f"❌ Failed to create Gmail API provider: {e}")
        return
    
    if not provider.is_configured():
        print("⚠️ Gmail API provider is not properly configured")
        if settings.use_aws_secrets:
            print("   - Check AWS Secrets Manager configuration")
            print("   - Run: python scripts/setup_aws_secrets.py")
        else:
            print("   - Check .env file for Gmail credentials:")
            print("     GMAIL_CLIENT_ID, GMAIL_CLIENT_SECRET, GMAIL_REFRESH_TOKEN")
        return
    
    # Create test email
    email = EmailRequest(
        provider="gmail_api",
        to=["recipient@example.com"],  # Change this to your test email
        subject="Gmail API Test Email",
        body="This is a test email sent via Gmail API from MCP service. If you receive this, Gmail API integration is working correctly!",
        from_email="noreply@yourdomain.com",  # Gmail API will use the authenticated user's email
        html=False
    )
    
    print(f"\n📧 Sending test email...")
    print(f"   To: {', '.join(email.to)}")
    print(f"   Subject: {email.subject}")
    
    try:
        response = await provider.send(email)
        
        if response.status == "success":
            print("✅ Email sent successfully via Gmail API!")
            print(f"   Status: {response.status}")
            print(f"   Provider: {response.provider}")
            if hasattr(response, 'message_id') and response.message_id:
                print(f"   Message ID: {response.message_id}")
        else:
            print("❌ Failed to send email via Gmail API")
            print(f"   Status: {response.status}")
            if response.error:
                print(f"   Error: {response.error}")
                
    except Exception as e:
        print(f"💥 Exception during email sending: {e}")

async def test_provider_selection():
    """Test automatic provider selection"""
    print("\n🔄 Testing Provider Selection")
    print("=" * 40)
    
    from src.mcp.providers.factory import EmailProviderFactory
    
    # Get available providers
    available = EmailProviderFactory.get_available_providers()
    print(f"📋 Available providers: {available}")
    
    # Test auto-selection
    provider = get_email_provider()
    print(f"🎯 Auto-selected provider: {type(provider).__name__}")
    print(f"🔧 Is configured: {provider.is_configured()}")
    
    # Test specific provider requests
    for provider_type in ["gmail_api", "smtp"]:
        try:
            provider = get_email_provider(provider_type)
            print(f"✅ {provider_type}: {type(provider).__name__} (configured: {provider.is_configured()})")
        except Exception as e:
            print(f"❌ {provider_type}: {e}")

if __name__ == "__main__":
    print("🚀 Gmail API and Provider Testing")
    print("=" * 50)
    
    asyncio.run(test_gmail_api())
    asyncio.run(test_provider_selection())
    
    print("\n" + "=" * 50)
    print("✨ Testing completed!")
    print("\nNext steps:")
    print("1. Update the recipient email address in this script")  
    print("2. Ensure Gmail API is properly configured")
    print("3. For production: set up AWS Secrets Manager")
    print("4. Run: python scripts/test_gmail_api.py")