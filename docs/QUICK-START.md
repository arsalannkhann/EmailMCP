# EmailMCP Quick Start Guide

Get EmailMCP up and running in minutes with this quick start guide.

## What is EmailMCP?

EmailMCP is a **multi-tenant email service** that allows your users to send emails through their own Gmail accounts using OAuth 2.0. Each user connects their Gmail, and emails are sent from their account - not yours!

Perfect for SaaS applications, CRM systems, or any platform where users need to send emails on their behalf.

## Before You Start

### What You Need
- [ ] A cloud account (GCP or AWS)
- [ ] Python 3.11+
- [ ] Docker (optional, for local testing)
- [ ] Gmail API OAuth credentials

### Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Create a new project or select existing
3. Enable "Gmail API"
4. Create "OAuth 2.0 Client ID" (Web application)
5. Add authorized redirect URIs:
   - For production: `https://your-domain.com/v1/oauth/callback`
   - For testing: `http://localhost:8001/v1/oauth/callback`
6. Save your Client ID and Client Secret

## Choose Your Deployment

### Option 1: GCP Cloud Run (Recommended) 🌟

**Best for:** Most users, startups, variable traffic
**Time to deploy:** ~10 minutes
**Monthly cost:** $5-15

```bash
# 1. Clone repository
git clone <repo-url>
cd EmailMCP

# 2. Setup GCP infrastructure
./scripts/setup_gcp.sh YOUR_PROJECT_ID us-central1

# 3. Configure Gmail OAuth
python3 scripts/setup_gcp_gmail_credentials.py YOUR_PROJECT_ID

# 4. Deploy to Cloud Run
./scripts/deploy_gcp.sh YOUR_PROJECT_ID us-central1

# 5. Get your service URL
gcloud run services describe emailmcp --region=us-central1 --format='value(status.url)'
```

**📖 Full Guide:** [GCP-DEPLOYMENT.md](../GCP-DEPLOYMENT.md)

### Option 2: AWS Fargate

**Best for:** Existing AWS users, enterprise
**Time to deploy:** ~20 minutes
**Monthly cost:** $65-105

```bash
# 1. Clone repository
git clone <repo-url>
cd EmailMCP

# 2. Configure Gmail credentials
python3 setup_gmail_credentials.py

# 3. Deploy infrastructure
aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yml \
  --stack-name emailmcp-stack \
  --capabilities CAPABILITY_IAM

# 4. Deploy application
./scripts/deploy.sh

# 5. Get your service URL
aws cloudformation describe-stacks \
  --stack-name emailmcp-stack \
  --query 'Stacks[0].Outputs[?OutputKey==`ServiceURL`].OutputValue' \
  --output text
```

**📖 Full Guide:** [DEPLOYMENT.md](../DEPLOYMENT.md)

## Test Your Deployment

Once deployed, test the service:

```bash
# Health check
curl https://your-service-url/health

# Should return: {"status": "healthy"}
```

## Integrate with Your Application

### Step 1: Store Your API Key

The setup scripts generate an API key. Store it securely:

```bash
# GCP: Get API key
gcloud secrets versions access latest --secret=emailmcp-api-key

# AWS: Get API key
aws secretsmanager get-secret-value --secret-id emailmcp/api-key
```

### Step 2: Initiate OAuth Flow

When a user wants to connect their Gmail:

```javascript
// Frontend: Redirect user to OAuth
const response = await fetch('https://your-service-url/v1/oauth/authorize', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    user_id: 'user123',
    redirect_uri: 'https://your-app.com/oauth/callback'
  })
});

const { authorization_url } = await response.json();
window.location.href = authorization_url;
```

### Step 3: Handle OAuth Callback

After user authorizes, handle the callback:

```javascript
// Backend: Handle callback (GET /oauth/callback?code=...&state=user123)
const response = await fetch(
  `https://your-service-url/v1/oauth/callback?code=${code}&state=${state}`,
  {
    method: 'POST',
    headers: { 'Authorization': 'Bearer YOUR_API_KEY' }
  }
);

const result = await response.json();
// { status: "success", user_id: "user123", email_address: "user@gmail.com" }
```

### Step 4: Send Email as User

Now send emails through the user's Gmail:

```javascript
const response = await fetch('https://your-service-url/v1/users/user123/messages', {
  method: 'POST',
  headers: {
    'Authorization': 'Bearer YOUR_API_KEY',
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    to: ['recipient@example.com'],
    subject: 'Hello!',
    body: 'This email is sent from my Gmail account',
    body_type: 'text'
  })
});

const result = await response.json();
// { status: "success", message_id: "...", provider: "gmail_api" }
```

## Complete Integration Example

Here's a complete frontend integration example:

```javascript
class EmailMCPClient {
  constructor(apiUrl, apiKey) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  async connectGmail(userId) {
    const response = await fetch(`${this.apiUrl}/v1/oauth/authorize`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        user_id: userId,
        redirect_uri: `${window.location.origin}/oauth/callback`
      })
    });
    
    const { authorization_url } = await response.json();
    window.location.href = authorization_url;
  }

  async getUserProfile(userId) {
    const response = await fetch(`${this.apiUrl}/v1/users/${userId}/profile`, {
      headers: { 'Authorization': `Bearer ${this.apiKey}` }
    });
    return response.json();
  }

  async sendEmail(userId, emailData) {
    const response = await fetch(`${this.apiUrl}/v1/users/${userId}/messages`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${this.apiKey}`,
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(emailData)
    });
    return response.json();
  }

  async getAnalytics(userId, startDate, endDate) {
    const params = new URLSearchParams({
      start_date: startDate,
      end_date: endDate
    });
    const response = await fetch(
      `${this.apiUrl}/v1/reports/users/${userId}?${params}`,
      { headers: { 'Authorization': `Bearer ${this.apiKey}` } }
    );
    return response.json();
  }

  async disconnectGmail(userId) {
    const response = await fetch(`${this.apiUrl}/v1/users/${userId}/gmail`, {
      method: 'DELETE',
      headers: { 'Authorization': `Bearer ${this.apiKey}` }
    });
    return response.json();
  }
}

// Usage
const client = new EmailMCPClient(
  'https://your-service-url',
  'your-api-key'
);

// Connect Gmail
await client.connectGmail('user123');

// Check if connected
const profile = await client.getUserProfile('user123');
if (profile.gmail_connected) {
  console.log(`Connected: ${profile.email_address}`);
}

// Send email
await client.sendEmail('user123', {
  to: ['recipient@example.com'],
  subject: 'Hello!',
  body: 'Message body',
  body_type: 'text'
});
```

## API Endpoints Summary

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/v1/oauth/authorize` | POST | Start OAuth flow |
| `/v1/oauth/callback` | POST | Handle OAuth callback |
| `/v1/users/{user_id}/messages` | POST | Send email |
| `/v1/users/{user_id}/profile` | GET | Get user profile |
| `/v1/reports/users/{user_id}` | GET | User analytics |
| `/v1/reports/summary` | GET | Platform analytics |
| `/v1/users/{user_id}/gmail` | DELETE | Disconnect Gmail |

## Monitoring Your Service

### GCP

```bash
# View logs
gcloud run services logs read emailmcp --region=us-central1

# Follow logs
gcloud run services logs tail emailmcp --region=us-central1
```

### AWS

```bash
# View logs
aws logs tail /aws/ecs/emailmcp --follow
```

## Common Issues

### OAuth Redirect URI Mismatch
**Problem:** Users see "redirect_uri_mismatch" error

**Solution:** 
1. Go to Google Cloud Console > Credentials
2. Edit your OAuth client
3. Add the exact redirect URI: `https://your-domain.com/v1/oauth/callback`

### API Key Invalid
**Problem:** Getting 401 Unauthorized

**Solution:**
1. Verify API key is correct
2. Check Authorization header format: `Bearer YOUR_API_KEY`

### Email Send Failed
**Problem:** Email send returns error

**Solution:**
1. Check user has connected Gmail
2. Verify OAuth tokens haven't expired (auto-refresh should handle this)
3. Check Gmail API is enabled in Google Cloud Console

## Next Steps

1. **Read Full Documentation**
   - [GCP Deployment Guide](../GCP-DEPLOYMENT.md)
   - [AWS Deployment Guide](../DEPLOYMENT.md)
   - [Multi-Tenant Integration](./multi-tenant-integration.md)

2. **Set Up Monitoring**
   - Configure alerts for failed emails
   - Set up uptime monitoring
   - Review logs regularly

3. **Implement Rate Limiting**
   - Add rate limiting to prevent abuse
   - Set per-user quotas if needed

4. **Add Custom Domain**
   - Configure custom domain for your service
   - Set up SSL/TLS certificates

5. **Scale as Needed**
   - Monitor costs and usage
   - Adjust scaling parameters
   - Consider multi-region deployment

## Support

- 📖 [Full Documentation](../README.md)
- 🐛 [Report Issues](https://github.com/your-repo/issues)
- 💬 [Community Forum](https://github.com/your-repo/discussions)

## Congratulations! 🎉

You now have a fully functional multi-tenant email service!

Users can:
- ✅ Connect their Gmail accounts securely
- ✅ Send emails from their own accounts
- ✅ View their email analytics
- ✅ Disconnect at any time

Your service:
- ✅ Scales automatically
- ✅ Stores credentials securely
- ✅ Handles token refresh automatically
- ✅ Provides comprehensive analytics

Happy emailing! 📧
