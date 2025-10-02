# EmailMCP Multi-Tenant Integration with SalesOS

## Overview
This document outlines the integration between SalesOS platform and EmailMCP service to enable users to send emails using their own Google OAuth credentials.

## Architecture Components

### 1. Enhanced EmailMCP API Endpoints

#### New Endpoints to Add:
- `POST /v1/oauth/authorize` - Initiate OAuth flow for a user
- `POST /v1/oauth/callback` - Handle OAuth callback and store tokens
- `GET /v1/users/{user_id}/profile` - Get user's email profile
- `POST /v1/users/{user_id}/messages` - Send email using user's credentials
- `GET /v1/reports/users/{user_id}` - Get email reports for specific user
- `GET /v1/reports/summary` - Get overall email analytics

### 2. Multi-Tenant Token Management

#### Enhanced Secrets Manager Strategy:
```
AWS Secrets Manager Structure:
├── emailmcp/users/{user_id}/gmail
│   ├── client_id
│   ├── client_secret
│   ├── refresh_token
│   ├── access_token
│   └── expires_at
└── emailmcp/oauth/config
    ├── client_id (shared)
    ├── client_secret (shared)
    └── redirect_uri
```

### 3. Database Schema Enhancement

#### User Email Accounts Table:
```sql
CREATE TABLE user_email_accounts (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    email_address VARCHAR(255) NOT NULL,
    provider VARCHAR(50) DEFAULT 'gmail_api',
    refresh_token_secret_arn VARCHAR(500),
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT NOW(),
    last_used_at TIMESTAMP,
    INDEX idx_user_id (user_id),
    INDEX idx_email (email_address)
);
```

#### Email Logs Table:
```sql
CREATE TABLE email_logs (
    id UUID PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL,
    from_email VARCHAR(255),
    to_emails JSON,
    subject VARCHAR(500),
    message_id VARCHAR(255),
    provider VARCHAR(50),
    status VARCHAR(50),
    error_message TEXT,
    sent_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_user_id (user_id),
    INDEX idx_sent_at (sent_at),
    INDEX idx_status (status)
);
```

## Implementation Steps

### Step 1: OAuth Flow Implementation

#### 1.1 SalesOS Frontend Integration
```javascript
// SalesOS: Initiate Gmail OAuth
async function connectGmail() {
    const response = await fetch(`${MCP_API_URL}/v1/oauth/authorize`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${MCP_API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            user_id: currentUser.id,
            redirect_url: `${SALES_OS_URL}/gmail-callback`
        })
    });
    
    const { authorization_url } = await response.json();
    window.location.href = authorization_url;
}
```

#### 1.2 EmailMCP OAuth Handler
```python
# New endpoint in EmailMCP
@router.post("/oauth/authorize")
async def initiate_oauth(request: OAuthRequest):
    # Generate OAuth URL with user-specific state
    oauth_url = f"https://accounts.google.com/o/oauth2/auth?client_id={GMAIL_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=https://www.googleapis.com/auth/gmail.send&response_type=code&state={request.user_id}&access_type=offline&prompt=consent"
    
    return {"authorization_url": oauth_url}

@router.post("/oauth/callback") 
async def oauth_callback(code: str, state: str):
    # Exchange code for tokens
    # Store user-specific tokens in Secrets Manager
    # Return success status
    pass
```

### Step 2: User-Specific Email Sending

#### 2.1 Enhanced Message Endpoint
```python
@router.post("/users/{user_id}/messages")
async def send_user_email(
    user_id: str,
    email: EmailRequest,
    credentials: HTTPAuthorizationCredentials = Security(security)
):
    # Get user-specific tokens from Secrets Manager
    user_tokens = await get_user_tokens(user_id)
    
    # Create Gmail service with user tokens
    gmail_service = build_gmail_service(user_tokens)
    
    # Send email and log the transaction
    result = await send_email_with_user_service(gmail_service, email)
    
    # Log email transaction
    await log_email_transaction(user_id, email, result)
    
    return result
```

### Step 3: Reporting and Analytics

#### 3.1 User Reports
```python
@router.get("/reports/users/{user_id}")
async def get_user_email_report(
    user_id: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
):
    # Query email logs for specific user
    logs = await get_user_email_logs(user_id, start_date, end_date)
    
    return {
        "user_id": user_id,
        "total_emails": len(logs),
        "successful_emails": len([l for l in logs if l.status == 'success']),
        "failed_emails": len([l for l in logs if l.status == 'failed']),
        "emails_by_day": group_by_day(logs),
        "top_recipients": get_top_recipients(logs),
        "recent_emails": logs[:10]
    }
```

#### 3.2 Platform-Wide Analytics
```python
@router.get("/reports/summary")
async def get_platform_summary():
    return {
        "total_users": await count_active_users(),
        "total_emails_sent": await count_total_emails(),
        "emails_today": await count_emails_today(),
        "success_rate": await calculate_success_rate(),
        "top_senders": await get_top_senders(),
        "usage_trends": await get_usage_trends()
    }
```

## SalesOS Integration Examples

### Frontend: Gmail Connection UI
```javascript
// Display Gmail connection status
function showGmailStatus() {
    fetch(`${MCP_API_URL}/v1/users/${userId}/profile`, {
        headers: { 'Authorization': `Bearer ${MCP_API_KEY}` }
    })
    .then(r => r.json())
    .then(profile => {
        if (profile.gmail_connected) {
            showConnectedUI(profile.email_address);
        } else {
            showConnectButton();
        }
    });
}

// Send email through user's Gmail
async function sendEmail(emailData) {
    const response = await fetch(`${MCP_API_URL}/v1/users/${userId}/messages`, {
        method: 'POST',
        headers: {
            'Authorization': `Bearer ${MCP_API_KEY}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            to: [emailData.recipient],
            from_email: userProfile.gmail_address,
            subject: emailData.subject,
            body: emailData.message,
            provider: 'gmail_api'
        })
    });
    
    const result = await response.json();
    if (result.status === 'success') {
        showSuccessMessage(`Email sent! Message ID: ${result.message_id}`);
    } else {
        showErrorMessage(`Failed to send: ${result.error}`);
    }
}
```

### Email Reports Dashboard
```javascript
// Fetch and display user's email analytics
async function loadEmailReports() {
    const reports = await fetch(`${MCP_API_URL}/v1/reports/users/${userId}`, {
        headers: { 'Authorization': `Bearer ${MCP_API_KEY}` }
    }).then(r => r.json());
    
    // Display charts and statistics
    updateEmailStatsChart(reports.emails_by_day);
    updateSuccessRateWidget(reports.successful_emails, reports.total_emails);
    updateRecentEmailsList(reports.recent_emails);
}
```

## Security Considerations

### 1. Token Security
- User tokens stored in separate AWS Secrets Manager entries
- Tokens encrypted at rest and in transit
- Regular token refresh and validation

### 2. Access Control
- User can only send emails from their own connected Gmail account
- API key validation for all requests
- Rate limiting per user and per API key

### 3. Audit Trail
- All email transactions logged with user ID
- Failed attempts tracked and monitored
- Regular security audits of token usage

## Benefits

### For SalesOS Platform:
- ✅ Users send emails from their own Gmail accounts
- ✅ Better deliverability (not marked as spam)
- ✅ Complete email analytics and reporting
- ✅ Automated OAuth flow - no manual token management
- ✅ Scalable multi-tenant architecture

### For Users:
- ✅ Emails appear to come from their real Gmail address
- ✅ Email history maintained in their Gmail account
- ✅ No need to share password or app passwords
- ✅ Can revoke access anytime through Google account settings

## Next Steps

1. **Database Setup**: Add user tables to track email accounts and logs
2. **OAuth Implementation**: Build the OAuth flow endpoints
3. **Multi-tenant Token Management**: Enhance Secrets Manager integration
4. **Frontend Integration**: Update SalesOS to use new endpoints
5. **Reporting Dashboard**: Build analytics and reporting features
6. **Testing**: Comprehensive testing with multiple user accounts