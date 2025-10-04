# OAuth Flow Diagram

This document explains the complete OAuth flow for EmailMCP with visual diagrams.

## Overview

The OAuth flow involves three parties:
1. **User's Browser** - The end user accessing the application
2. **EmailMCP Service** - Your backend service
3. **Google OAuth** - Google's authentication server

## Complete OAuth Flow

```
┌─────────────┐
│   Browser   │
│   (User)    │
└──────┬──────┘
       │
       │ 1. User clicks "Connect Gmail"
       ▼
┌─────────────────────────────────────────────────────────┐
│  Frontend (sample-frontend/app.js)                      │
│  - Calls: POST /v1/oauth/authorize                      │
│  - Body: { user_id: "user_123",                         │
│           redirect_uri: "http://localhost:8000/..." }   │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 2. Request authorization URL
       ▼
┌─────────────────────────────────────────────────────────┐
│  EmailMCP Backend (src/mcp/api/v1/multi_tenant.py)     │
│  - Generates OAuth URL with parameters                  │
│  - Returns: { authorization_url: "https://..." }        │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 3. Redirect user to Google
       ▼
┌─────────────────────────────────────────────────────────┐
│  Google OAuth (accounts.google.com)                     │
│  - User logs in with Google account                     │
│  - User approves Gmail access                           │
│  - User sees: "EmailMCP wants to access Gmail"          │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 4. Google redirects back with auth code
       │    GET /v1/oauth/callback?code=ABC123&state=user_123
       ▼
┌─────────────────────────────────────────────────────────┐
│  EmailMCP Backend - OAuth Callback (GET endpoint)       │
│  ✓ Public endpoint (no API key required)                │
│  - Receives: code, state, redirect_uri                  │
│  - Exchanges code for tokens                            │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 5. Exchange authorization code for tokens
       ▼
┌─────────────────────────────────────────────────────────┐
│  Google Token Exchange (oauth2.googleapis.com/token)    │
│  - Validates authorization code                         │
│  - Returns: { access_token, refresh_token }             │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 6. Store tokens securely
       ▼
┌─────────────────────────────────────────────────────────┐
│  EmailMCP Backend - Token Storage                       │
│  - Stores tokens in Secret Manager                      │
│  - Gets user's Gmail address                            │
│  - Returns success to user                              │
└──────┬──────────────────────────────────────────────────┘
       │
       │ 7. Return success response
       ▼
┌─────────────┐
│   Browser   │
│  ✓ Success! │
└─────────────┘
```

## Key Components of the Fix

### BEFORE (Broken - Returned 404)

```
Step 4: Google tries to redirect
   ↓
GET /v1/oauth/callback?code=ABC&state=user_123
   ↓
❌ 404 NOT FOUND
   ↓
Endpoint only accepts POST requests
```

### AFTER (Fixed - Works Correctly)

```
Step 4: Google tries to redirect
   ↓
GET /v1/oauth/callback?code=ABC&state=user_123
   ↓
✓ 200 OK - Public endpoint accepts GET
   ↓
Token exchange succeeds
```

## Endpoint Configuration

### OAuth Authorization URL Generation

```
POST /v1/oauth/authorize
Headers: Authorization: Bearer <api_key>
Body: {
  "user_id": "user_123",
  "redirect_uri": "http://localhost:8001/v1/oauth/callback"
}

Response: {
  "authorization_url": "https://accounts.google.com/o/oauth2/v2/auth?...",
  "state": "user_123"
}
```

### OAuth Callback (GET - Public)

```
GET /v1/oauth/callback?code=AUTH_CODE&state=USER_ID&redirect_uri=...
Headers: None (public endpoint)

Response: {
  "status": "success",
  "user_id": "user_123",
  "email_address": "user@gmail.com",
  "message": "Gmail account connected successfully"
}
```

### OAuth Callback (POST - With Auth)

```
POST /v1/oauth/callback?code=AUTH_CODE&state=USER_ID&redirect_uri=...
Headers: Authorization: Bearer <api_key>

Response: {
  "status": "success",
  "user_id": "user_123",
  "email_address": "user@gmail.com",
  "message": "Gmail account connected successfully"
}
```

## Token Exchange Flow

```
┌──────────────────────┐
│ Authorization Code   │  (From Google callback)
│   "ABC123XYZ"        │
└──────────┬───────────┘
           │
           ▼
┌────────────────────────────────────────────────┐
│ POST https://oauth2.googleapis.com/token       │
│ Body:                                          │
│   - code: ABC123XYZ                            │
│   - client_id: your-client-id                  │
│   - client_secret: your-client-secret          │
│   - redirect_uri: http://localhost:8001/...    │
│   - grant_type: authorization_code             │
└──────────┬─────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────┐
│ Tokens Response:                               │
│   - access_token: "ya29.a0..."                 │
│   - refresh_token: "1//0g..."                  │
│   - expires_in: 3600                           │
│   - token_type: "Bearer"                       │
└──────────┬─────────────────────────────────────┘
           │
           ▼
┌────────────────────────────────────────────────┐
│ Store in Secret Manager:                       │
│   users/{user_id}/gmail                        │
│   {                                            │
│     "access_token": "ya29...",                 │
│     "refresh_token": "1//0g...",               │
│     "email_address": "user@gmail.com",         │
│     "expires_at": "2025-10-04T15:00:00Z"       │
│   }                                            │
└────────────────────────────────────────────────┘
```

## Redirect URI Configuration

### Google Cloud Console Setup

You must add BOTH redirect URIs:

```
1. Backend Callback (for direct OAuth):
   http://localhost:8001/v1/oauth/callback
   https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback

2. Frontend Callback Page (for user feedback):
   http://localhost:8000/callback.html
   https://yourdomain.com/callback.html
```

### Why Both Are Needed

```
Option A: Direct Callback to Backend
   Google → GET /v1/oauth/callback → Backend processes
   (Used when redirect_uri points to backend)

Option B: Frontend Bridge
   Google → callback.html → POST /v1/oauth/callback → Backend processes
   (Used when redirect_uri points to frontend)
```

## Security Considerations

### ✓ Correct (Public GET Endpoint)

```
GET /v1/oauth/callback
- No authentication required
- Google can directly call this endpoint
- State parameter prevents CSRF attacks
- Standard OAuth 2.0 practice
```

### ✗ Incorrect (Was requiring authentication)

```
POST /v1/oauth/callback
- Required API key
- Google cannot include API key in redirect
- Caused 404 errors
- Non-standard implementation
```

## Testing the Flow

### Test 1: Check Endpoint Exists

```bash
curl http://localhost:8001/v1/oauth/callback?code=test&state=test

# Should return 400 (bad code) or 500 (network error)
# Should NOT return 404 (endpoint not found)
```

### Test 2: Generate Authorization URL

```bash
curl -X POST http://localhost:8001/v1/oauth/authorize \
  -H "Authorization: Bearer dev-api-key" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "redirect_uri": "http://localhost:8001/v1/oauth/callback"
  }'

# Should return authorization_url
```

### Test 3: Complete Flow

```bash
# Run the automated test
python3 scripts/test_oauth_endpoints.py

# Expected output:
# ✓ PASS: Health Check
# ✓ PASS: OAuth Authorize
# ✓ PASS: OAuth Callback GET
# ✓ PASS: OAuth Callback POST
```

## Common Error Messages

### 404 Not Found
```
❌ Error: Cannot GET /v1/oauth/callback
Cause: Endpoint doesn't exist or only accepts POST
Fix: Update to latest code with GET endpoint
```

### redirect_uri_mismatch
```
❌ Error: redirect_uri_mismatch
Cause: redirect_uri not registered in Google Cloud Console
Fix: Add exact redirect_uri to authorized redirect URIs
```

### invalid_client
```
❌ Error: invalid_client
Cause: client_id or client_secret is wrong
Fix: Check .env file has correct credentials
```

### invalid_grant
```
❌ Error: invalid_grant
Cause: Authorization code already used or expired
Fix: Start OAuth flow again from beginning
```

## Success Indicators

When everything works correctly:

1. ✓ No 404 errors during callback
2. ✓ User is redirected back to your app
3. ✓ User sees "Gmail Connected Successfully"
4. ✓ Tokens are stored in Secret Manager
5. ✓ User can send emails via their Gmail account

## Migration Guide

### If You Have Existing Users

1. Update your code to the latest version
2. No database migration needed
3. Existing tokens continue to work
4. New OAuth flows use the fixed endpoint
5. Users don't need to reconnect

### If You're Starting Fresh

1. Clone the repository
2. Copy `.env.example` to `.env`
3. Add your OAuth credentials
4. Configure redirect URIs in Google Cloud Console
5. Run the test script
6. Start using the service

## Additional Resources

- [OAUTH_CONFIGURATION.md](./OAUTH_CONFIGURATION.md) - Detailed setup guide
- [OAUTH_404_FIX_SUMMARY.md](./OAUTH_404_FIX_SUMMARY.md) - Technical details of the fix
- [sample-frontend/README.md](./sample-frontend/README.md) - Frontend integration guide
- [Google OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
