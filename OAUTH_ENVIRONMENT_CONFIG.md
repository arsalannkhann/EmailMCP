# OAuth Redirect URI Environment Configuration

## Overview

This guide explains how to configure OAuth redirect URIs based on your deployment environment. The EmailMCP service now supports flexible redirect URI configuration that automatically adapts to development, staging, and production environments.

## Problem This Solves

Previously, the OAuth redirect URI was either hardcoded or required manual configuration for each environment. This created issues when:

- Frontend runs on different ports (e.g., localhost:3000, localhost:8000)
- Backend runs on different ports (e.g., localhost:5005, localhost:8001)
- `credentials.json` has a fixed redirect URI that doesn't match the actual running environment
- Moving between development and production required manual configuration changes

## Solution

The service now provides environment-aware defaults with override capabilities:

### Default Behavior

**Development Environment** (`ENVIRONMENT=development`):
- Backend OAuth callback: `http://localhost:{MCP_PORT}/v1/oauth/callback`
- Frontend callback page: `http://localhost:8000/callback.html`

**Production Environment** (`ENVIRONMENT=production`):
- Backend OAuth callback: `https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback`
- Frontend callback page: `https://salesos.orionac.in/settings/`

## Configuration

### Option 1: Use Environment Defaults (Recommended)

Simply set your environment type in `.env`:

```bash
# For local development
ENVIRONMENT=development
MCP_PORT=8001

# For production deployment
ENVIRONMENT=production
```

The service will automatically use appropriate redirect URIs.

### Option 2: Custom Redirect URIs

Override defaults with custom URIs in `.env`:

```bash
# Custom backend OAuth callback
OAUTH_REDIRECT_URI=https://custom-domain.com/oauth/callback

# Custom frontend callback page origin
OAUTH_FRONTEND_ORIGIN=https://custom-frontend.com
```

### Option 3: Per-Request Redirect URI

Pass redirect_uri dynamically when initiating OAuth:

```python
# In your application code
await service.generate_oauth_url(
    user_id="user_123",
    redirect_uri="http://localhost:3000/custom/callback"
)
```

## Google Cloud Console Configuration

You must add ALL redirect URIs you plan to use in Google Cloud Console:

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Select your OAuth 2.0 Client ID
3. Add the following **Authorized redirect URIs**:

### For Local Development
```
http://localhost:8001/v1/oauth/callback
http://localhost:8000/callback.html
http://localhost:3000/callback.html (if frontend uses port 3000)
```

### For Production
```
https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
https://salesos.orionac.in/settings/
```

### For Custom Domains
```
https://your-backend.com/v1/oauth/callback
https://your-frontend.com/callback.html
```

## API Usage

### 1. Generate OAuth URL

**With Environment Default:**
```bash
curl -X POST http://localhost:8001/v1/oauth/authorize \
  -H "Authorization: Bearer emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123"
  }'
```

**With Custom Redirect URI:**
```bash
curl -X POST http://localhost:8001/v1/oauth/authorize \
  -H "Authorization: Bearer emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user_123",
    "redirect_uri": "http://localhost:3000/oauth/callback"
  }'
```

### 2. OAuth Callback

**Query Parameters:**
- `code`: Authorization code from Google (required)
- `state`: User ID from authorization request (required)
- `redirect_uri`: Redirect URI used in authorization (optional, uses environment default if not provided)

**Example:**
```bash
# Google redirects to this URL after user authorization
http://localhost:8001/v1/oauth/callback?code=AUTH_CODE&state=user_123
```

## Code Examples

### Python Service Usage

```python
from src.mcp.services.multi_tenant_service import MultiTenantEmailService

service = MultiTenantEmailService()

# Option 1: Use environment default
oauth_url = await service.generate_oauth_url(
    user_id="user_123"
)

# Option 2: Use custom redirect URI
oauth_url = await service.generate_oauth_url(
    user_id="user_123",
    redirect_uri="http://localhost:3000/callback"
)

# Process callback with environment default
result = await service.process_oauth_callback(
    authorization_code="AUTH_CODE",
    user_id="user_123"
)

# Process callback with custom redirect URI
result = await service.process_oauth_callback(
    authorization_code="AUTH_CODE",
    user_id="user_123",
    redirect_uri="http://localhost:3000/callback"
)
```

### JavaScript Frontend Usage

```javascript
// Get authorization URL
const response = await fetch('http://localhost:8001/v1/oauth/authorize', {
    method: 'POST',
    headers: {
        'Authorization': 'Bearer emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw',
        'Content-Type': 'application/json'
    },
    body: JSON.stringify({
        user_id: 'user_123',
        redirect_uri: window.location.origin + '/callback.html'  // Optional
    })
});

const data = await response.json();
// Redirect user to authorization URL
window.location.href = data.authorization_url;
```

## Environment Variables Reference

### Core Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `ENVIRONMENT` | `production` | Environment type: `development`, `staging`, or `production` |
| `MCP_PORT` | `8001` | Port for EmailMCP service |
| `GMAIL_CLIENT_ID` | - | Gmail OAuth client ID |
| `GMAIL_CLIENT_SECRET` | - | Gmail OAuth client secret |

### OAuth Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `OAUTH_REDIRECT_URI` | (environment-based) | Custom backend OAuth callback URI |
| `OAUTH_FRONTEND_ORIGIN` | (environment-based) | Custom frontend origin for callback pages |

## Migration Guide

### From Hardcoded Redirect URIs

**Before:**
```python
# Hardcoded in credentials.json or code
redirect_uri = "http://localhost:5005/oauth2callback"
```

**After:**
```bash
# In .env
ENVIRONMENT=development
MCP_PORT=8001

# Service automatically uses: http://localhost:8001/v1/oauth/callback
```

### From Manual Configuration

**Before:**
```bash
# Different .env files for each environment
# .env.development
REDIRECT_URI=http://localhost:8001/v1/oauth/callback

# .env.production
REDIRECT_URI=https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
```

**After:**
```bash
# Single .env for all environments
ENVIRONMENT=development  # or production
# Redirect URI automatically determined
```

## Testing

Run the comprehensive test suite:

```bash
# Test all OAuth redirect URI functionality
python -m pytest tests/test_oauth_redirect_uri.py -v

# Test specific environment scenarios
python -m pytest tests/test_oauth_redirect_uri.py::TestOAuthRedirectURIConfiguration -v

# Test service integration
python -m pytest tests/test_oauth_redirect_uri.py::TestMultiTenantServiceRedirectURI -v
```

## Troubleshooting

### redirect_uri_mismatch Error

**Cause:** The redirect_uri doesn't match any URIs in Google Cloud Console.

**Solution:**
1. Check your environment configuration
2. Verify the redirect URI in Google Cloud Console matches exactly
3. Try explicitly setting `OAUTH_REDIRECT_URI` in `.env`

```bash
# Check what redirect URI is being used
curl -X POST http://localhost:8001/v1/oauth/authorize \
  -H "Authorization: Bearer emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "test"}' | jq '.authorization_url'
```

### Invalid Client Error

**Cause:** Gmail credentials not configured correctly.

**Solution:**
```bash
# In .env
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
```

### 404 on Callback

**Cause:** Service not running or wrong port.

**Solution:**
```bash
# Check service is running
curl http://localhost:8001/health

# Verify port matches MCP_PORT
grep MCP_PORT .env
```

## Best Practices

1. **Use environment defaults in development** - No configuration needed
2. **Set custom URIs for special cases** - Only when necessary
3. **Keep Google Cloud Console in sync** - Add all possible redirect URIs
4. **Use HTTPS in production** - Always for security
5. **Test with different ports** - Ensure flexibility works
6. **Document custom configurations** - For team members

## Advanced Usage

### Multi-Port Development Setup

Support multiple frontend ports simultaneously:

```bash
# In .env
ENVIRONMENT=development
MCP_PORT=8001

# In Google Cloud Console, add:
# - http://localhost:8001/v1/oauth/callback (backend)
# - http://localhost:8000/callback.html (frontend option 1)
# - http://localhost:3000/callback.html (frontend option 2)

# In frontend, use:
redirect_uri: window.location.origin + '/callback.html'
```

### Custom Domain Setup

```bash
# In .env
ENVIRONMENT=production
OAUTH_REDIRECT_URI=https://api.yourdomain.com/v1/oauth/callback
OAUTH_FRONTEND_ORIGIN=https://app.yourdomain.com

# In Google Cloud Console, add:
# - https://api.yourdomain.com/v1/oauth/callback
# - https://app.yourdomain.com/callback.html
```

### Dynamic Tenant-Specific Redirect URIs

```python
# For multi-tenant SaaS applications
async def get_tenant_redirect_uri(tenant_id: str) -> str:
    tenant = await get_tenant_config(tenant_id)
    return tenant.custom_domain + '/oauth/callback' if tenant.custom_domain else settings.get_default_oauth_redirect_uri()

# Use in OAuth flow
oauth_url = await service.generate_oauth_url(
    user_id=f"{tenant_id}:{user_id}",
    redirect_uri=await get_tenant_redirect_uri(tenant_id)
)
```

## Related Documentation

- [OAUTH_CONFIGURATION.md](OAUTH_CONFIGURATION.md) - General OAuth setup guide
- [OAUTH_FLOW_DIAGRAM.md](OAUTH_FLOW_DIAGRAM.md) - OAuth flow visualization
- [.env.example](.env.example) - Environment variable examples
