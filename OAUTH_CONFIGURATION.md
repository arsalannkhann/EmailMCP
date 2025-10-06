# OAuth Configuration Guide

This guide explains how to configure Gmail OAuth for the EmailMCP service.

## Understanding the OAuth 404 Error

If you're seeing a 404 error during OAuth callback, it means:

1. **Google cannot find your callback endpoint** - The redirect URI in your Google Cloud Console doesn't match your actual callback URL
2. **Your credentials are not configured correctly** - The client_id and client_secret need to match your Google Cloud project

## Prerequisites

You need credentials from Google Cloud Console with the correct redirect URIs configured.

## Step 1: Get OAuth Credentials from Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Select or create a project
3. Navigate to **APIs & Services > Credentials**
4. Click **Create Credentials > OAuth 2.0 Client ID**
5. Select **Web application** as application type
6. Configure the following:

### Authorized JavaScript origins
```
http://localhost:8000
http://localhost
https://yourdomain.com
```

### Authorized redirect URIs

For local development:
```
http://localhost:8001/v1/oauth/callback
http://localhost:8000/callback.html
```

For production:
```
https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
https://yourdomain.com/callback.html
https://salesos.orionac.in/settings/
```

## Step 2: Configure Your Credentials

### Method A: Using Environment Variables (Recommended)

Create or update your `.env` file:

```bash
# Environment Configuration
ENVIRONMENT=development  # or production

# Gmail OAuth Configuration
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret

# Optional: Override default redirect URIs
# OAUTH_REDIRECT_URI=http://localhost:8001/v1/oauth/callback
# OAUTH_FRONTEND_ORIGIN=http://localhost:8000
```

Example with provided credentials:
```bash
GMAIL_CLIENT_ID=1009146957673-h7964rj4s2a9be9ekrqh0j2dehk4mu5t.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=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
```

**Note:** The service now automatically determines redirect URIs based on your environment setting. See [OAUTH_ENVIRONMENT_CONFIG.md](OAUTH_ENVIRONMENT_CONFIG.md) for detailed configuration options.

### Method B: Using GCP Secret Manager (Production)

For production deployments, credentials are stored in GCP Secret Manager:

```bash
# Store OAuth credentials in Secret Manager
gcloud secrets create gmail-oauth-credentials \
    --data-file=credentials.json \
    --project=mcporionac

# Or update existing secret
gcloud secrets versions add gmail-oauth-credentials \
    --data-file=credentials.json \
    --project=mcporionac
```

## Step 3: Update Frontend Configuration

Update `sample-frontend/config.js`:

```javascript
const CONFIG = {
    // EmailMCP Service URL
    EMAILMCP_SERVICE_URL: 'http://localhost:8001', // or production URL
    EMAILMCP_API_KEY: 'emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw',
    
    // Google OAuth (for Google Sign-In)
    GOOGLE_CLIENT_ID: '480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com',
    
    // OAuth Callback URL - MUST match redirect_uri in Google Cloud Console
    OAUTH_REDIRECT_URI: window.location.origin + '/callback.html',
};
```

## Step 4: Understanding the OAuth Flow

### Authorization URL Generation

When a user clicks "Connect Gmail", the frontend calls:

```
POST /v1/oauth/authorize
Body: {
  "user_id": "user_123",
  "redirect_uri": "http://localhost:8000/callback.html"
}
```

The service generates an authorization URL and redirects the user to Google.

### OAuth Callback

Google redirects back to your callback URL with:
```
GET /v1/oauth/callback?code=AUTH_CODE&state=USER_ID
```

**Important**: This is now a **GET endpoint** that accepts:
- `code`: Authorization code from Google
- `state`: The user_id passed during authorization
- `redirect_uri` (optional): The redirect URI to use for token exchange

The service exchanges the code for access/refresh tokens and stores them securely.

## Common Issues and Solutions

### Issue 1: 404 Error on Callback

**Cause**: Redirect URI mismatch or endpoint not configured

**Solution**:
1. Ensure redirect URI in Google Cloud Console exactly matches your callback URL
2. Check that the EmailMCP service is running
3. Verify the callback endpoint is accessible (it's now a public GET endpoint)

Example correct redirect URIs:
```
http://localhost:8001/v1/oauth/callback
https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
```

### Issue 2: "redirect_uri_mismatch" Error

**Cause**: The redirect_uri parameter doesn't match any URIs registered in Google Cloud Console

**Solution**:
1. Go to Google Cloud Console > APIs & Services > Credentials
2. Edit your OAuth 2.0 Client ID
3. Add the exact redirect URI to the "Authorized redirect URIs" list
4. Wait a few minutes for changes to propagate

### Issue 3: Invalid Client Error

**Cause**: client_id or client_secret is incorrect

**Solution**:
1. Verify credentials in `.env` match Google Cloud Console
2. Check for extra spaces or newlines in credential values
3. Regenerate credentials if needed from Google Cloud Console

### Issue 4: Credentials File Format

If you have a `credentials.json` file from Google Cloud Console:

```json
{
  "web": {
    "client_id": "your-client-id.apps.googleusercontent.com",
    "project_id": "your-project-id",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
    "client_secret": "your-client-secret",
    "redirect_uris": [
      "http://localhost/",
      "https://yourdomain.com/callback"
    ]
  }
}
```

Extract and set in `.env`:
```bash
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
```

## Testing the OAuth Flow

### 1. Start the Service

```bash
cd /path/to/EmailMCP
uvicorn src.mcp.main:app --reload --host 0.0.0.0 --port 8001
```

### 2. Start the Frontend

```bash
cd sample-frontend
python3 -m http.server 8000
```

### 3. Test the Flow

1. Open http://localhost:8000
2. Sign in with Google
3. Click "Connect Gmail Account"
4. You should be redirected to Google's authorization page
5. After authorizing, you should be redirected back to callback.html
6. The callback should complete successfully

### 4. Verify Success

Check the logs for:
```
OAuth completed for user: user_123
```

## API Endpoints

### POST /v1/oauth/authorize
Initiates OAuth flow and returns Google authorization URL.

**Request:**
```json
{
  "user_id": "user_123",
  "redirect_uri": "http://localhost:8000/callback.html"
}
```

**Response:**
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "user_123"
}
```

### GET /v1/oauth/callback
Handles OAuth callback from Google (public endpoint).

**Query Parameters:**
- `code`: Authorization code from Google
- `state`: User ID
- `redirect_uri` (optional): Redirect URI used in authorization

**Response:**
```json
{
  "status": "success",
  "user_id": "user_123",
  "email_address": "user@gmail.com",
  "message": "Gmail account connected successfully"
}
```

### POST /v1/oauth/callback
Alternative POST endpoint for frontend bridge calls (requires API key).

Same parameters and response as GET endpoint.

## Security Notes

1. **Never commit credentials to version control** - Use environment variables or secret managers
2. **Use HTTPS in production** - OAuth requires secure connections
3. **Validate state parameter** - Prevents CSRF attacks
4. **Rotate credentials regularly** - Update client secrets periodically
5. **Limit redirect URIs** - Only add URIs you control

## Production Deployment

For production:

1. Store credentials in GCP Secret Manager
2. Configure authorized redirect URIs for production domain
3. Use HTTPS for all endpoints
4. Enable audit logging for OAuth events
5. Monitor failed authentication attempts

## Support

If you continue to have issues:

1. Check server logs for detailed error messages
2. Verify all URLs match exactly (including http/https, trailing slashes)
3. Test with a fresh browser session or incognito mode
4. Confirm Google Cloud project has Gmail API enabled
5. Check service account permissions in GCP
