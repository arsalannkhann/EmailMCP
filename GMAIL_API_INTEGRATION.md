# Gmail API & AWS Secrets Manager Integration Guide

## Overview

Your EmailMCP service now supports both SMTP and Gmail API for sending emails, with production-ready AWS Secrets Manager integration for secure credential management.

## Features Added

### ✅ Gmail API Provider
- OAuth2 refresh token support
- Automatic token refresh
- Better rate limits than SMTP
- Rich Gmail integration features

### ✅ AWS Secrets Manager Integration
- Secure credential storage for production
- Automatic credential loading
- Refresh token management
- Environment-based configuration

### ✅ Smart Provider Selection
- Auto-selects best available provider
- Fallback support (Gmail API → SMTP)
- Environment-aware configuration

### ✅ Production Ready
- Separate production configuration
- Deployment scripts
- Health checks
- Comprehensive error handling

## Configuration

### Development Environment

Your `.env` file now includes:
```bash
# Email Provider Configuration
PREFERRED_EMAIL_PROVIDER=gmail_api
ENVIRONMENT=development

# Gmail API Credentials (Development)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_REFRESH_TOKEN=your-refresh-token
```

### Production Environment

Production uses AWS Secrets Manager:
```bash
# Production Environment
ENVIRONMENT=production
AWS_REGION=us-east-1
AWS_SECRETS_NAME=mcp-service
PREFERRED_EMAIL_PROVIDER=gmail_api
```

## Usage Examples

### 1. Auto Provider Selection (Recommended)
```python
# API Request
{
    "provider": "auto",  # or omit for auto-selection
    "to": ["recipient@example.com"],
    "subject": "Test Email",
    "body": "Hello from MCP!"
}
```

### 2. Specific Provider
```python
# Force Gmail API
{
    "provider": "gmail_api",
    "to": ["recipient@example.com"],
    "subject": "Test Email",
    "body": "Hello via Gmail API!"
}

# Force SMTP  
{
    "provider": "smtp",
    "to": ["recipient@example.com"],
    "subject": "Test Email", 
    "body": "Hello via SMTP!"
}
```

## Setup Instructions

### 1. Development Setup (Current)
Your current setup already works! The service will:
- Use Gmail API if configured
- Fall back to SMTP if Gmail API unavailable
- Auto-select the best provider

### 2. Test Gmail API
```bash
cd /Users/arsalankhan/Documents/GitHub/EmailMCP
source venv/bin/activate
python scripts/test_gmail_api.py
```

### 3. Production Setup

#### Step 1: Set up AWS Secrets Manager
```bash
# Set your AWS credentials first
aws configure

# Run the setup script
python scripts/setup_aws_secrets.py
```

#### Step 2: Deploy to Production
```bash
# Deploy with the deployment script
./scripts/deploy.sh

# Or deploy in background
./scripts/deploy.sh --background
```

## Provider Priority Logic

The system automatically selects providers in this order:

1. **If `PREFERRED_EMAIL_PROVIDER=gmail_api`:**
   - Gmail API (if configured)
   - SMTP (fallback)

2. **If `PREFERRED_EMAIL_PROVIDER=smtp`:**
   - SMTP (if configured)
   - Gmail API (fallback)

## Files Created/Modified

### New Files
- `src/mcp/providers/gmail_api.py` - Gmail API provider
- `src/mcp/providers/gmail_api_production.py` - Production Gmail provider
- `src/mcp/providers/factory.py` - Provider selection logic
- `src/mcp/services/aws_secrets.py` - AWS Secrets Manager service
- `scripts/setup_aws_secrets.py` - AWS setup script
- `scripts/deploy.sh` - Production deployment script
- `scripts/test_gmail_api.py` - Gmail API testing script
- `.env.production` - Production environment template

### Modified Files
- `src/mcp/core/config.py` - Enhanced configuration management
- `src/mcp/providers/base.py` - Added `is_configured()` method
- `src/mcp/providers/smtp_client.py` - Added `is_configured()` method
- `src/mcp/api/v1/messages.py` - Updated to use provider factory
- `src/mcp/schemas/requests.py` - Added gmail_api and auto options
- `.env` - Added new configuration options

## Refresh Token Logic

### Development
- Refresh tokens stored in `.env` file
- Automatic token refresh when expired
- New access tokens cached in memory

### Production
- Refresh tokens stored in AWS Secrets Manager
- Credentials loaded automatically on first use
- Secure token refresh with AWS integration
- Option to rotate refresh tokens

## Benefits vs SMTP

| Feature | SMTP | Gmail API |
|---------|------|-----------|
| Security | App Passwords | OAuth2 |
| Rate Limits | Limited | Higher |
| Features | Basic | Rich Gmail features |
| Monitoring | Basic | Detailed |
| Scalability | Limited | Better |

## Troubleshooting

### Gmail API Not Working?
1. Check credentials in `.env` file
2. Verify refresh token is valid
3. Run: `python scripts/test_gmail_api.py`

### AWS Secrets Manager Issues?
1. Verify AWS credentials: `aws sts get-caller-identity`
2. Check secrets exist: AWS Console → Secrets Manager
3. Re-run: `python scripts/setup_aws_secrets.py`

### Provider Selection Issues?
1. Check available providers: Look at test script output
2. Verify configuration: Check `.env` file settings
3. Check logs for provider selection details

## Next Steps

1. **Test the Integration:**
   ```bash
   python scripts/test_gmail_api.py
   ```

2. **Update Test Recipients:**
   - Edit recipient emails in test scripts
   - Test both Gmail API and SMTP

3. **Production Deployment:**
   ```bash
   python scripts/setup_aws_secrets.py
   ./scripts/deploy.sh
   ```

4. **Monitor & Maintain:**
   - Monitor refresh token health
   - Set up AWS CloudWatch for secrets access logging
   - Regular testing of both providers

Your EmailMCP service is now production-ready with secure, scalable email delivery! 🚀