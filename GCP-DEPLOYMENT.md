# EmailMCP GCP Cloud Run Deployment Guide

Complete step-by-step guide for deploying EmailMCP service on Google Cloud Platform (GCP) with Cloud Run, Secret Manager, and complete multi-tenant architecture.

## Prerequisites

Before starting the deployment, ensure you have:

- ✅ Google Cloud SDK (`gcloud`) installed and configured
- ✅ Docker installed and running
- ✅ Python 3.11+ installed
- ✅ Gmail API credentials (Client ID, Client Secret)
- ✅ GCP project with billing enabled
- ✅ Appropriate GCP permissions (Cloud Run, Secret Manager, Firestore, Container Registry, etc.)

## Architecture Overview

The deployment creates:
- **Cloud Run** - Serverless container orchestration for the EmailMCP service
- **Secret Manager** - Secure storage for Gmail API credentials and user tokens
- **Firestore** - NoSQL database for user profiles and email logs
- **Cloud Load Balancing** - HTTPS load balancer with SSL/TLS
- **Container Registry (Artifact Registry)** - Docker image storage
- **Cloud Logging** - Centralized logging and monitoring
- **Identity-Aware Proxy (Optional)** - Additional authentication layer

## Multi-Tenant Architecture

This deployment supports complete multi-tenant functionality:

### User-Specific OAuth Flow
1. Each user connects their own Gmail account via OAuth
2. User tokens are securely stored in Secret Manager with user-specific keys
3. Emails are sent through each user's authenticated Gmail account

### Database Schema (Firestore Collections)

```
/users/{user_id}
  - email_address: string
  - gmail_connected: boolean
  - connection_date: timestamp
  - last_used: timestamp
  - total_emails_sent: number

/email_logs/{log_id}
  - user_id: string
  - from_email: string
  - to_emails: array
  - subject: string
  - message_id: string
  - status: string (success/failed)
  - sent_at: timestamp
  - error_message: string (if failed)
```

## Step 1: Setup GCP Project

```bash
# Set your project ID
export PROJECT_ID="mcporionac"
export REGION="us-central1"

# Set the project
gcloud config set project $PROJECT_ID

# Enable required APIs
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com \
  cloudresourcemanager.googleapis.com \
  iam.googleapis.com
```

## Step 2: Clone and Setup Local Environment

```bash
# Clone the repository
git clone <your-repo-url>
cd EmailMCP

# Create Python virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## Step 3: Setup Firestore Database

```bash
# Create Firestore database (Native mode)
gcloud firestore databases create --location=$REGION

# Create indexes (if needed)
gcloud firestore indexes composite create \
  --collection-group=email_logs \
  --field-config field-path=user_id,order=ascending \
  --field-config field-path=sent_at,order=descending
```

## Step 4: Configure Gmail API Credentials

### 4.1 Get Gmail API Credentials

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Navigate to APIs & Services > Credentials
3. Create OAuth 2.0 Client ID (Web application)
4. Add authorized redirect URIs:
   - `https://your-domain.com/v1/oauth/callback`
   - `http://localhost:8001/v1/oauth/callback` (for testing)
5. Download credentials JSON

### 4.2 Store Credentials in Secret Manager

```bash
# Create OAuth configuration secret
gcloud secrets create emailmcp-gmail-oauth-config \
  --data-file=- <<EOF
{
  "client_id": "480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com",
  "client_secret": "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",
  "redirect_uri": "https://salesos.orionac.in/settings/v1/oauth/callback"
}
EOF

# Grant Cloud Run service account access to secrets
gcloud secrets add-iam-policy-binding emailmcp-gmail-oauth-config \
  --member="serviceAccount:${PROJECT_ID}@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

## Step 5: Create Service Account

```bash
# Create service account for Cloud Run
gcloud iam service-accounts create emailmcp-service \
  --display-name="EmailMCP Service Account"

# Grant necessary permissions
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:emailmcp-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:emailmcp-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

# Troubleshooting: If you get errors, ensure the service account exists and you have owner/editor permissions.
# You can list service accounts with:
#   gcloud iam service-accounts list
# And check IAM policy with:
#   gcloud projects get-iam-policy $PROJECT_ID

# Multi-Tenant OAuth (Localhost Testing)
# Initiate OAuth for a user using localhost redirect URI:
curl -X POST "http://localhost:8001/v1/oauth/authorize" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "redirect_uri": "http://localhost:8001/v1/oauth/callback"
  }'
```

## Step 6: Configure Environment Variables

Create `.env.production.gcp` file:

```bash
# Environment
ENVIRONMENT=production

# GCP Configuration
GCP_PROJECT_ID=your-project-id
GCP_REGION=us-central1

# Service Configuration
MCP_API_KEY=your-secure-api-key-here
MCP_HOST=0.0.0.0
MCP_PORT=8080

# Gmail OAuth Configuration (loaded from Secret Manager)
GMAIL_CLIENT_ID=your-client-id
GMAIL_CLIENT_SECRET=your-client-secret

# Email Provider
PREFERRED_EMAIL_PROVIDER=gmail_api

# Logging
LOG_LEVEL=INFO
```

## Step 7: Build and Deploy to Cloud Run

### 7.1 Create Dockerfile (if not exists)

Ensure your `Dockerfile` is optimized for Cloud Run:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port (Cloud Run expects 8080 by default)
EXPOSE 8080

# Run the application
CMD ["uvicorn", "src.mcp.main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### 7.2 Build Container Image

```bash
# Set the image name
export IMAGE_NAME="gcr.io/${PROJECT_ID}/emailmcp"

# Build using Cloud Build
gcloud builds submit --tag $IMAGE_NAME

# Or build locally and push
docker build -t $IMAGE_NAME .
docker push $IMAGE_NAME
```

### 7.3 Deploy to Cloud Run

```bash
# Deploy the service
gcloud run deploy emailmcp \
  --image=$IMAGE_NAME \
  --platform=managed \
  --region=$REGION \
  --service-account=emailmcp-service@${PROJECT_ID}.iam.gserviceaccount.com \
  --allow-unauthenticated \
  --port=8080 \
  --memory=1Gi \
  --cpu=1 \
  --min-instances=0 \
  --max-instances=10 \
  --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION}" \
  --set-secrets="GMAIL_CLIENT_ID=emailmcp-gmail-oauth-config:latest,GMAIL_CLIENT_SECRET=emailmcp-gmail-oauth-config:latest"

# Get the service URL
gcloud run services describe emailmcp --region=$REGION --format='value(status.url)'
```

## Step 8: Configure Custom Domain (Optional)

```bash
# Map custom domain
gcloud run domain-mappings create \
  --service=emailmcp \
  --domain=api.yourdomain.com \
  --region=$REGION

# Follow the instructions to update DNS records
```

## Step 9: Setup Monitoring and Alerts

```bash
# Create log-based metric for failed emails
gcloud logging metrics create email_failures \
  --description="Count of failed email sends" \
  --log-filter='resource.type="cloud_run_revision"
    severity>=ERROR
    jsonPayload.message=~"Failed to send email"'

# Create alert policy
gcloud alpha monitoring policies create \
  --notification-channels=YOUR_CHANNEL_ID \
  --display-name="Email Failures Alert" \
  --condition-display-name="High email failure rate" \
  --condition-threshold-value=10 \
  --condition-threshold-duration=60s
```

## Multi-Tenant API Usage

### 1. Initiate OAuth for User

```bash
curl -X POST "https://your-service.run.app/v1/oauth/authorize" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "user123",
    "redirect_uri": "https://your-app.com/oauth/callback"
  }'
```

Response:
```json
{
  "authorization_url": "https://accounts.google.com/o/oauth2/...",
  "state": "user123"
}
```

### 2. Handle OAuth Callback

After user authorizes, Google redirects to your callback with code:

```bash
curl -X POST "https://your-service.run.app/v1/oauth/callback?code=AUTH_CODE&state=user123" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

Response:
```json
{
  "status": "success",
  "user_id": "user123",
  "email_address": "user@gmail.com",
  "message": "Gmail account connected successfully"
}
```

### 3. Send Email as User

```bash
curl -X POST "https://your-service.run.app/v1/users/user123/messages" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "to": ["recipient@example.com"],
    "subject": "Test Email",
    "body": "Hello from EmailMCP!",
    "body_type": "text"
  }'
```

### 4. Get User Profile

```bash
curl "https://your-service.run.app/v1/users/user123/profile" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 5. Get Email Analytics

```bash
curl "https://your-service.run.app/v1/reports/users/user123?start_date=2024-01-01&end_date=2024-12-31" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### 6. Get Platform Summary

```bash
curl "https://your-service.run.app/v1/reports/summary" \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Management Commands

### View Logs

```bash
# View Cloud Run logs
gcloud run services logs read emailmcp --region=$REGION --limit=50

# Follow logs in real-time
gcloud run services logs tail emailmcp --region=$REGION
```

### Update Service

```bash
# Update environment variables
gcloud run services update emailmcp \
  --region=$REGION \
  --set-env-vars="NEW_VAR=value"

# Update to new image
gcloud builds submit --tag $IMAGE_NAME
gcloud run services update emailmcp \
  --image=$IMAGE_NAME \
  --region=$REGION
```

### Scale Service

```bash
# Update scaling configuration
gcloud run services update emailmcp \
  --region=$REGION \
  --min-instances=1 \
  --max-instances=20
```

### Manage Secrets

```bash
# List all secrets
gcloud secrets list

# View secret versions
gcloud secrets versions list emailmcp-gmail-oauth-config

# Update secret
gcloud secrets versions add emailmcp-gmail-oauth-config \
  --data-file=new-credentials.json

# Access secret (for debugging)
gcloud secrets versions access latest \
  --secret=emailmcp-gmail-oauth-config
```

### Database Management

```bash
# Export Firestore data
gcloud firestore export gs://${PROJECT_ID}-backup/$(date +%Y%m%d)

# Import Firestore data
gcloud firestore import gs://${PROJECT_ID}-backup/BACKUP_DATE
```

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Check service account permissions
   gcloud projects get-iam-policy $PROJECT_ID \
     --flatten="bindings[].members" \
     --filter="bindings.members:emailmcp-service@${PROJECT_ID}.iam.gserviceaccount.com"
   ```

2. **Secret Access Issues**
   ```bash
   # Verify secret access
   gcloud secrets get-iam-policy emailmcp-gmail-oauth-config
   ```

3. **OAuth Redirect URI Mismatch**
   - Ensure redirect URI in Google Console matches your callback endpoint
   - Check that HTTPS is properly configured

4. **Container Startup Issues**
   ```bash
   # Check startup logs
   gcloud run services logs read emailmcp --region=$REGION --limit=100
   ```

## Security Considerations

### API Key Management
- Store API keys securely in Secret Manager
- Rotate API keys regularly
- Use different keys for different environments

### OAuth Security
- Use state parameter to prevent CSRF attacks
- Validate redirect URIs strictly
- Store tokens encrypted in Secret Manager

### Network Security
- Enable Cloud Armor for DDoS protection
- Configure VPC Service Controls for additional isolation
- Use Identity-Aware Proxy for admin endpoints

### Data Protection
- Enable Firestore point-in-time recovery
- Regular backups to Cloud Storage
- Implement data retention policies

## Cost Optimization

### Cloud Run Costs
- Use min-instances=0 for development
- Set appropriate CPU and memory limits
- Enable CPU throttling (default)

### Secret Manager Costs
- Use secret versions efficiently
- Clean up old secret versions regularly

### Firestore Costs
- Create appropriate indexes
- Use batch operations when possible
- Implement data archival for old logs

## Monitoring and Alerts

### Key Metrics to Monitor
1. Request count and latency
2. Error rate and types
3. OAuth success/failure rate
4. Email send success/failure rate
5. Secret Manager access patterns
6. Firestore read/write operations

### Recommended Alerts
- Error rate > 5%
- P95 latency > 1s
- Failed OAuth attempts spike
- Failed email sends > 10/minute

## Performance Tuning

### Cloud Run Configuration
```bash
# Optimize for performance
gcloud run services update emailmcp \
  --region=$REGION \
  --cpu=2 \
  --memory=2Gi \
  --concurrency=80 \
  --min-instances=1 \
  --max-instances=100
```

### Connection Pooling
- Reuse Gmail API connections
- Implement proper connection pooling for Firestore
- Cache Secret Manager responses (with TTL)

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Deploy to Cloud Run

on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - id: auth
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}
      
      - name: Build and Push
        run: |
          gcloud builds submit --tag gcr.io/${{ secrets.GCP_PROJECT_ID }}/emailmcp
      
      - name: Deploy to Cloud Run
        run: |
          gcloud run deploy emailmcp \
            --image gcr.io/${{ secrets.GCP_PROJECT_ID }}/emailmcp \
            --region us-central1 \
            --platform managed
```

## Backup and Disaster Recovery

### Backup Strategy
```bash
# Automated backup script
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_BUCKET="gs://${PROJECT_ID}-backups"

# Backup Firestore
gcloud firestore export ${BACKUP_BUCKET}/firestore/${DATE}

# Backup secrets metadata
gcloud secrets list --format=json > secrets-${DATE}.json
gsutil cp secrets-${DATE}.json ${BACKUP_BUCKET}/secrets/
```

### Recovery Procedure
1. Restore Firestore data from backup
2. Recreate secrets if needed
3. Redeploy service from last known good image
4. Verify functionality with health checks

## Next Steps

1. **Implement Advanced Features**
   - Email templates
   - Scheduled sending
   - Email tracking and analytics
   - Webhook notifications

2. **Enhance Security**
   - Implement rate limiting
   - Add request validation
   - Enable audit logging
   - Set up VPC Service Controls

3. **Improve Monitoring**
   - Custom dashboards in Cloud Monitoring
   - Integration with external monitoring (Datadog, New Relic)
   - Synthetic monitoring for uptime

4. **Scale for Growth**
   - Multi-region deployment
   - Global load balancing
   - CDN for static assets
   - Database sharding strategy

## Support and Resources

- [Google Cloud Run Documentation](https://cloud.google.com/run/docs)
- [Secret Manager Documentation](https://cloud.google.com/secret-manager/docs)
- [Firestore Documentation](https://cloud.google.com/firestore/docs)
- [Gmail API Documentation](https://developers.google.com/gmail/api)

## Appendix: Helper Scripts

### GCP Setup Script

Create `scripts/setup_gcp.sh`:

```bash
#!/bin/bash
set -e

echo "🚀 Setting up EmailMCP on GCP"
echo "=============================="

# Configuration
PROJECT_ID=${1:-"your-project-id"}
REGION=${2:-"us-central1"}

# Enable APIs
echo "📦 Enabling required APIs..."
gcloud services enable \
  run.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  artifactregistry.googleapis.com \
  cloudbuild.googleapis.com

# Create service account
echo "🔐 Creating service account..."
gcloud iam service-accounts create emailmcp-service \
  --display-name="EmailMCP Service Account"

# Grant permissions
echo "🔑 Granting permissions..."
gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:emailmcp-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding $PROJECT_ID \
  --member="serviceAccount:emailmcp-service@${PROJECT_ID}.iam.gserviceaccount.com" \
  --role="roles/datastore.user"

echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Configure Gmail API credentials"
echo "2. Store credentials in Secret Manager"
echo "3. Build and deploy the application"
```

---

**Congratulations!** 🎉 You now have a production-ready EmailMCP service running on GCP Cloud Run with complete multi-tenant architecture, secure credential management, and comprehensive monitoring!
