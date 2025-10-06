# OAuth Redirect URI Environment Configuration - Visual Guide

## Configuration Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Application Startup                               │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                  Load Configuration from .env                        │
│                                                                       │
│  • ENVIRONMENT = development/production                              │
│  • MCP_PORT = 8001                                                   │
│  • OAUTH_REDIRECT_URI = (optional)                                   │
│  • OAUTH_FRONTEND_ORIGIN = (optional)                                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│         Initialize Settings with Environment Detection              │
│                                                                       │
│  settings = Settings()                                               │
│  • is_development → ENVIRONMENT == "development"                     │
│  • is_production → ENVIRONMENT == "production"                       │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
         ┌─────────────────────┴─────────────────────┐
         │                                             │
         ▼                                             ▼
┌──────────────────────┐                  ┌──────────────────────┐
│ Development Mode     │                  │ Production Mode      │
│                      │                  │                      │
│ Backend:             │                  │ Backend:             │
│ http://localhost:    │                  │ https://emailmcp-    │
│   {MCP_PORT}/v1/     │                  │   hcnqp547xa-uc.a.   │
│   oauth/callback     │                  │   run.app/v1/oauth/  │
│                      │                  │   callback           │
│ Frontend:            │                  │                      │
│ http://localhost:    │                  │ Frontend:            │
│   8000/callback.html │                  │ https://salesos.     │
│                      │                  │   orionac.in/        │
│                      │                  │   settings/          │
└──────────────────────┘                  └──────────────────────┘
         │                                             │
         └─────────────────────┬─────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Check for Custom Override Configuration                 │
│                                                                       │
│  If OAUTH_REDIRECT_URI is set:                                       │
│    → Use custom backend redirect URI                                 │
│  Else:                                                                │
│    → Use environment default                                         │
│                                                                       │
│  If OAUTH_FRONTEND_ORIGIN is set:                                    │
│    → Use custom frontend origin + /callback.html                     │
│  Else:                                                                │
│    → Use environment default                                         │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      Service Initialization                          │
│                                                                       │
│  service = MultiTenantEmailService()                                 │
│  • Has access to settings.get_default_oauth_redirect_uri()           │
│  • Can accept custom redirect_uri per request                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
```

## OAuth URL Generation Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│              Client Calls generate_oauth_url()                       │
│                                                                       │
│  oauth_url = await service.generate_oauth_url(                       │
│      user_id="user_123",                                             │
│      redirect_uri=None  # Optional parameter                         │
│  )                                                                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Is redirect_uri  │
                    │ provided?        │
                    └─────┬────────┬───┘
                          │        │
                     YES  │        │  NO
                          │        │
         ┌────────────────┘        └────────────────┐
         ▼                                           ▼
┌──────────────────────┐              ┌──────────────────────────┐
│ Use Provided URI     │              │ Use Environment Default  │
│                      │              │                          │
│ redirect_uri =       │              │ redirect_uri = settings  │
│   custom_value       │              │   .get_default_oauth_    │
│                      │              │   redirect_uri()         │
└──────────────────────┘              └──────────────────────────┘
         │                                           │
         └────────────────┬──────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Build OAuth Authorization URL                           │
│                                                                       │
│  https://accounts.google.com/o/oauth2/v2/auth?                       │
│    client_id={GMAIL_CLIENT_ID}                                       │
│    &redirect_uri={redirect_uri}  ← Determined above                  │
│    &response_type=code                                               │
│    &scope=openid+https://mail.google.com/+...                        │
│    &access_type=offline                                              │
│    &prompt=consent                                                   │
│    &state={user_id}                                                  │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Return OAuth URL to Client                        │
└─────────────────────────────────────────────────────────────────────┘
```

## OAuth Callback Processing Flow

```
┌─────────────────────────────────────────────────────────────────────┐
│         Google Redirects User to Callback Endpoint                   │
│                                                                       │
│  GET /v1/oauth/callback?code=AUTH_CODE&state=user_123                │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│            API Endpoint Receives Callback Request                    │
│                                                                       │
│  async def handle_oauth_callback(                                    │
│      code: str,                                                      │
│      state: str,                                                     │
│      redirect_uri: Optional[str] = None                              │
│  )                                                                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│           Call service.process_oauth_callback()                      │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
                    ┌──────────────────┐
                    │ Is redirect_uri  │
                    │ provided?        │
                    └─────┬────────┬───┘
                          │        │
                     YES  │        │  NO
                          │        │
         ┌────────────────┘        └────────────────┐
         ▼                                           ▼
┌──────────────────────┐              ┌──────────────────────────┐
│ Use Provided URI     │              │ Use Environment Default  │
│                      │              │                          │
│ redirect_uri =       │              │ redirect_uri = settings  │
│   query_param_value  │              │   .get_default_oauth_    │
│                      │              │   redirect_uri()         │
└──────────────────────┘              └──────────────────────────┘
         │                                           │
         └────────────────┬──────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────────┐
│         Exchange Authorization Code for Access Token                 │
│                                                                       │
│  POST https://oauth2.googleapis.com/token                            │
│  {                                                                    │
│    code: AUTH_CODE,                                                  │
│    client_id: GMAIL_CLIENT_ID,                                       │
│    client_secret: GMAIL_CLIENT_SECRET,                               │
│    redirect_uri: {redirect_uri},  ← MUST match authorization value  │
│    grant_type: "authorization_code"                                  │
│  }                                                                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│              Store Tokens and Create User Profile                    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Return Success Response                           │
└─────────────────────────────────────────────────────────────────────┘
```

## Environment-Based Configuration Matrix

```
┌──────────────┬─────────────────────────────┬─────────────────────────────┐
│ Environment  │ Backend Redirect URI        │ Frontend Callback URI       │
├──────────────┼─────────────────────────────┼─────────────────────────────┤
│ development  │ http://localhost:{PORT}/    │ http://localhost:8000/      │
│              │   v1/oauth/callback         │   callback.html             │
├──────────────┼─────────────────────────────┼─────────────────────────────┤
│ staging      │ https://emailmcp-hcnqp547xa-│ https://salesos.orionac.in/ │
│              │   uc.a.run.app/v1/oauth/    │   settings/                 │
│              │   callback                  │                             │
├──────────────┼─────────────────────────────┼─────────────────────────────┤
│ production   │ https://emailmcp-hcnqp547xa-│ https://salesos.orionac.in/ │
│              │   uc.a.run.app/v1/oauth/    │   settings/                 │
│              │   callback                  │                             │
├──────────────┼─────────────────────────────┼─────────────────────────────┤
│ custom       │ {OAUTH_REDIRECT_URI}        │ {OAUTH_FRONTEND_ORIGIN}/    │
│ (override)   │                             │   callback.html             │
└──────────────┴─────────────────────────────┴─────────────────────────────┘
```

## Decision Tree: Which Redirect URI is Used?

```
                    ┌─────────────────┐
                    │ OAuth Request   │
                    │ Initiated       │
                    └────────┬────────┘
                             │
                             ▼
              ┌──────────────────────────┐
              │ Is redirect_uri provided │
              │ in API request?          │
              └──────┬──────────┬────────┘
                     │          │
                 YES │          │ NO
                     │          │
                     ▼          ▼
         ┌──────────────┐  ┌──────────────────────┐
         │ Use Provided │  │ Check OAUTH_REDIRECT_│
         │ redirect_uri │  │ URI env variable     │
         └──────────────┘  └──────┬───────────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    │                           │
                SET │                           │ NOT SET
                    │                           │
                    ▼                           ▼
         ┌──────────────────┐      ┌──────────────────────┐
         │ Use OAUTH_       │      │ Check ENVIRONMENT    │
         │ REDIRECT_URI     │      │ variable             │
         └──────────────────┘      └──────┬───────────────┘
                                          │
                              ┌───────────┴───────────┐
                              │                       │
                  "development"│                      │ other
                              │                       │
                              ▼                       ▼
                  ┌──────────────────┐    ┌──────────────────┐
                  │ http://localhost:│    │ https://emailmcp-│
                  │ {PORT}/v1/oauth/ │    │ hcnqp547xa-uc.a. │
                  │ callback         │    │ run.app/v1/oauth/│
                  │                  │    │ callback         │
                  └──────────────────┘    └──────────────────┘
```

## Example Scenarios

### Scenario 1: Local Development (Simplest)

```
.env:
  ENVIRONMENT=development
  MCP_PORT=8001

Result:
  Backend:  http://localhost:8001/v1/oauth/callback
  Frontend: http://localhost:8000/callback.html
```

### Scenario 2: Frontend on Different Port

```
.env:
  ENVIRONMENT=development
  MCP_PORT=8001

Code:
  oauth_url = await service.generate_oauth_url(
      user_id="user_123",
      redirect_uri="http://localhost:3000/callback"
  )

Result:
  Backend:  http://localhost:3000/callback (custom)
  Frontend: http://localhost:8000/callback.html (default)
```

### Scenario 3: Production Deployment

```
.env:
  ENVIRONMENT=production

Result:
  Backend:  https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback
  Frontend: https://salesos.orionac.in/settings/
```

### Scenario 4: Custom Domain

```
.env:
  ENVIRONMENT=production
  OAUTH_REDIRECT_URI=https://api.mycompany.com/v1/oauth/callback
  OAUTH_FRONTEND_ORIGIN=https://app.mycompany.com

Result:
  Backend:  https://api.mycompany.com/v1/oauth/callback
  Frontend: https://app.mycompany.com/callback.html
```

## Implementation Benefits

```
┌─────────────────────────────────────────────────────────────────────┐
│                      Before Implementation                           │
│                                                                       │
│  ❌ Hardcoded redirect URIs                                          │
│  ❌ Manual configuration per environment                             │
│  ❌ Conflicts with different ports                                   │
│  ❌ credentials.json mismatch issues                                 │
│  ❌ Difficult to maintain                                            │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│                       After Implementation                           │
│                                                                       │
│  ✅ Environment-aware defaults                                       │
│  ✅ Automatic configuration                                          │
│  ✅ Support for multiple ports                                       │
│  ✅ Custom override capability                                       │
│  ✅ Easy to maintain and extend                                      │
│  ✅ Well tested (21 passing tests)                                   │
└─────────────────────────────────────────────────────────────────────┘
```
