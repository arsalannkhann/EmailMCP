# EmailMCP System Metadata

Complete metadata specification for the EmailMCP service with comprehensive user authentication, Google Cloud Firestore integration, and frontend compatibility.

## System Overview

**Service Name**: EmailMCP (Email Model Context Protocol)  
**Version**: 1.0.0  
**Architecture**: Multi-tenant SaaS  
**Deployment**: Google Cloud Platform (Cloud Run)  
**Database**: Google Cloud Firestore  
**Authentication**: Google OAuth 2.0 + JWT  

## Production Environment

### Service Endpoints
- **Production URL**: https://emailmcp-hcnqp547xa-uc.a.run.app
- **API Version**: v1
- **Health Check**: GET /health
- **OpenAPI Docs**: GET /docs

### Authentication
- **API Key**: `emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw`
- **Method**: Bearer Token Authentication
- **Header**: `Authorization: Bearer <api_key>`

## Google Cloud Configuration

### Project Information
```yaml
project_id: mcporionac
region: us-central1
service_name: emailmcp
```

### Enabled APIs
- Cloud Run API
- Secret Manager API
- Firestore API
- Gmail API
- IAM API
- Cloud Build API

### Service Account
```yaml
name: emailmcp-service-account@mcporionac.iam.gserviceaccount.com
roles:
  - roles/secretmanager.secretAccessor
  - roles/datastore.user
  - roles/logging.logWriter
  - roles/monitoring.metricWriter
```

### Secret Manager Configuration
```yaml
secrets:
  emailmcp-api-key:
    value: "emailmcp-oWyFsIqTUhnoOZQDaEPBfMKOQV2ElAtw"
    access: emailmcp-service-account@mcporionac.iam.gserviceaccount.com
  
  emailmcp-gmail-client-id:
    value: "480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com"
    access: emailmcp-service-account@mcporionac.iam.gserviceaccount.com
  
  emailmcp-gmail-client-secret:
    value: "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"
    access: emailmcp-service-account@mcporionac.iam.gserviceaccount.com
```

## Database Schema (Firestore)

### Collection: users
```javascript
{
  // Document ID: Google User ID
  "_metadata": {
    "collection": "users",
    "document_id": "google_user_id", // e.g., "1234567890"
    "created_at": "2025-10-04T10:00:00.000Z",
    "updated_at": "2025-10-04T15:30:00.000Z",
    "version": 1
  },
  
  // User Profile
  "id": "1234567890",
  "email": "user@company.com",
  "name": "John Doe",
  "picture": "https://lh3.googleusercontent.com/a/default-user",
  
  // Gmail Integration
  "gmail_connected": true,
  "gmail_connected_at": "2025-10-04T10:30:00.000Z",
  "gmail_email": "user@company.com",
  "gmail_refresh_token_stored": true,
  
  // Usage Statistics
  "total_emails_sent": 25,
  "last_email_sent_at": "2025-10-04T15:00:00.000Z",
  "monthly_email_count": {
    "2025-10": 25,
    "2025-09": 42
  },
  
  // Account Status
  "account_status": "active", // active, suspended, deleted
  "subscription_tier": "free", // free, pro, enterprise
  "rate_limit_quota": 100, // emails per day
  "rate_limit_used": 25,
  "rate_limit_reset_at": "2025-10-05T00:00:00.000Z",
  
  // Timestamps
  "created_at": "2025-10-01T09:15:00.000Z",
  "updated_at": "2025-10-04T15:30:00.000Z",
  "last_login": "2025-10-04T15:30:00.000Z"
}
```

### Collection: email_logs
```javascript
{
  // Document ID: Auto-generated
  "_metadata": {
    "collection": "email_logs",
    "document_id": "auto_generated_id",
    "created_at": "2025-10-04T15:25:00.000Z",
    "indexed_fields": ["user_id", "sent_at", "status"]
  },
  
  // User Reference
  "user_id": "1234567890",
  "user_email": "user@company.com",
  
  // Email Details
  "from_email": "user@company.com",
  "to_emails": ["client@example.com", "partner@startup.io"],
  "cc_emails": ["manager@company.com"],
  "bcc_emails": [],
  "subject": "Project Proposal - Q4 Planning",
  "body_preview": "Hi there, I wanted to follow up on our...", // First 100 chars
  "body_type": "html", // text, html
  "body_length": 1250,
  
  // Message Tracking
  "message_id": "CAJvQVw1234567890abcdef...",
  "gmail_thread_id": "1234567890abcdef",
  "gmail_message_id": "1234567890abcdef",
  
  // Status Tracking
  "status": "sent", // sent, failed, queued, delivered
  "error_message": null,
  "error_code": null,
  "retry_count": 0,
  "max_retries": 3,
  
  // Metadata
  "email_size_bytes": 2048,
  "attachments_count": 0,
  "priority": "normal", // low, normal, high
  "delivery_method": "gmail_api",
  
  // Timestamps
  "sent_at": "2025-10-04T15:25:00.000Z",
  "delivered_at": "2025-10-04T15:25:30.000Z",
  "created_at": "2025-10-04T15:25:00.000Z"
}
```

### Collection: oauth_tokens
```javascript
{
  // Document ID: User ID
  "_metadata": {
    "collection": "oauth_tokens",
    "document_id": "user_id",
    "created_at": "2025-10-04T10:30:00.000Z",
    "updated_at": "2025-10-04T14:00:00.000Z",
    "ttl": "2025-11-04T10:30:00.000Z" // 30 days from creation
  },
  
  // Token Information
  "user_id": "1234567890",
  "provider": "gmail",
  "scope": "https://www.googleapis.com/auth/gmail.send",
  
  // Token Data (encrypted)
  "access_token_hash": "sha256_hash_of_access_token",
  "refresh_token_hash": "sha256_hash_of_refresh_token",
  "token_expires_at": "2025-10-04T16:30:00.000Z",
  
  // Usage Tracking
  "last_used_at": "2025-10-04T15:25:00.000Z",
  "usage_count": 25,
  "last_refresh_at": "2025-10-04T14:00:00.000Z",
  
  // Security
  "created_ip": "192.168.1.100",
  "last_used_ip": "192.168.1.100",
  "user_agent": "Mozilla/5.0...",
  
  // Timestamps
  "created_at": "2025-10-04T10:30:00.000Z",
  "updated_at": "2025-10-04T14:00:00.000Z"
}
```

### Collection: user_sessions
```javascript
{
  // Document ID: Session Token Hash
  "_metadata": {
    "collection": "user_sessions",
    "document_id": "session_token_hash",
    "created_at": "2025-10-04T15:30:00.000Z",
    "ttl": "2025-10-11T15:30:00.000Z" // 7 days
  },
  
  // Session Information
  "user_id": "1234567890",
  "session_id": "sess_1234567890abcdef",
  "token_hash": "sha256_hash_of_jwt_token",
  
  // Session Details
  "expires_at": "2025-10-11T15:30:00.000Z",
  "is_active": true,
  "device_info": {
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100",
    "device_type": "desktop", // mobile, tablet, desktop
    "browser": "Chrome",
    "os": "macOS"
  },
  
  // Activity Tracking
  "last_activity": "2025-10-04T15:45:00.000Z",
  "activity_count": 15,
  "pages_visited": ["/dashboard", "/compose", "/settings"],
  
  // Security
  "login_method": "google_oauth",
  "two_factor_verified": false,
  "suspicious_activity": false,
  
  // Timestamps
  "created_at": "2025-10-04T15:30:00.000Z",
  "updated_at": "2025-10-04T15:45:00.000Z"
}
```

### Collection: system_metrics
```javascript
{
  // Document ID: Date (YYYY-MM-DD)
  "_metadata": {
    "collection": "system_metrics",
    "document_id": "2025-10-04",
    "created_at": "2025-10-04T00:00:00.000Z",
    "updated_at": "2025-10-04T23:59:59.000Z"
  },
  
  // Daily Metrics
  "date": "2025-10-04",
  "total_users": 150,
  "active_users": 45,
  "new_users": 3,
  "gmail_connections": 8,
  
  // Email Metrics
  "emails_sent": 320,
  "emails_failed": 5,
  "success_rate": 98.4,
  "avg_emails_per_user": 7.1,
  
  // Performance Metrics
  "avg_response_time_ms": 245,
  "error_rate": 0.02,
  "uptime_percentage": 99.95,
  
  // Resource Usage
  "cpu_usage_avg": 15.5,
  "memory_usage_avg": 68.2,
  "storage_used_gb": 2.3,
  
  // Hourly Breakdown
  "hourly_stats": {
    "00": { "users": 2, "emails": 5 },
    "01": { "users": 1, "emails": 2 },
    // ... for each hour
    "15": { "users": 15, "emails": 45 },
    "23": { "users": 8, "emails": 12 }
  },
  
  // Timestamps
  "created_at": "2025-10-04T00:00:00.000Z",
  "updated_at": "2025-10-04T23:59:59.000Z"
}
```

## API Endpoints Metadata

### Authentication Endpoints
```yaml
oauth_authorization:
  method: POST
  path: /v1/oauth/authorize
  description: Initiate Gmail OAuth flow
  authentication: API Key required
  rate_limit: 10 requests/minute per user
  request_schema:
    user_id: string (required)
    redirect_uri: string (required)
  response_schema:
    authorization_url: string
    state: string

oauth_callback:
  method: GET
  path: /v1/oauth/callback
  description: Handle OAuth callback from Google (public endpoint)
  authentication: None (public endpoint for Google OAuth redirects)
  parameters:
    code: string (required) - Authorization code from Google
    state: string (required) - User ID from state parameter
    redirect_uri: string (optional) - Redirect URI used in authorization
  response_schema:
    status: string
    email_address: string
    user_id: string
    message: string

oauth_callback_post:
  method: POST
  path: /v1/oauth/callback
  description: Handle OAuth callback via POST (for frontend bridge calls)
  authentication: API Key required
  parameters:
    code: string (required) - Authorization code from Google
    state: string (required) - User ID from state parameter
    redirect_uri: string (optional) - Redirect URI used in authorization
  response_schema:
    status: string
    email_address: string
    user_id: string
    message: string
```

### Email Management Endpoints
```yaml
send_email:
  method: POST
  path: /v1/users/{user_id}/messages
  description: Send email via user's Gmail account
  authentication: API Key required
  rate_limit: 100 emails/day per user
  request_schema:
    to: array[string] (required)
    subject: string (required)
    body: string (required)
    body_type: string (text|html)
    cc: array[string] (optional)
    bcc: array[string] (optional)
  response_schema:
    message_id: string
    thread_id: string
    status: string

get_user_profile:
  method: GET
  path: /v1/users/{user_id}/profile
  description: Get user profile and Gmail connection status
  authentication: API Key required
  response_schema:
    user_id: string
    email: string
    gmail_connected: boolean
    total_emails_sent: integer
    last_email_sent: datetime

get_email_history:
  method: GET
  path: /v1/users/{user_id}/messages
  description: Get user's email sending history
  authentication: API Key required
  parameters:
    limit: integer (default: 50, max: 100)
    offset: integer (default: 0)
    status: string (sent|failed|all)
  response_schema:
    messages: array[object]
    total: integer
    has_more: boolean
```

### System Management Endpoints
```yaml
health_check:
  method: GET
  path: /health
  description: Service health status
  authentication: None
  response_schema:
    status: string (healthy|unhealthy)
    timestamp: datetime
    uptime: integer
    version: string

metrics:
  method: GET
  path: /v1/metrics
  description: System metrics and analytics
  authentication: API Key required (admin only)
  parameters:
    start_date: string (YYYY-MM-DD)
    end_date: string (YYYY-MM-DD)
  response_schema:
    metrics: object
    period: object
```

## Security Configuration

### JWT Token Structure
```javascript
{
  "header": {
    "alg": "HS256",
    "typ": "JWT"
  },
  "payload": {
    "user_id": "1234567890",
    "email": "user@company.com",
    "iat": 1728048000,
    "exp": 1728652800,
    "iss": "emailmcp-service",
    "aud": "frontend-app",
    "scope": ["read", "write", "send_email"]
  }
}
```

### OAuth 2.0 Configuration
```yaml
google_oauth:
  client_id: "480969272523-fkgsdj73m89og99teqqbk13d15q172eq.apps.googleusercontent.com"
  client_secret: "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"
  scopes:
    - "https://www.googleapis.com/auth/gmail.send"
    - "https://www.googleapis.com/auth/userinfo.email"
    - "https://www.googleapis.com/auth/userinfo.profile"
  redirect_uris:
    - "https://emailmcp-hcnqp547xa-uc.a.run.app/v1/oauth/callback"
    - "http://localhost:8001/v1/oauth/callback"
    - "https://salesos.orionac.in/gmail/callback"
```

### Rate Limiting Configuration
```yaml
rate_limits:
  api_key_requests: 1000/hour
  user_email_sending: 100/day
  oauth_attempts: 10/minute
  profile_requests: 60/minute
  history_requests: 30/minute
```

## Monitoring & Observability

### Logging Configuration
```yaml
logging:
  level: INFO
  format: JSON
  destinations:
    - Cloud Logging
    - Local files (development)
  
  log_types:
    access_logs:
      enabled: true
      include_request_body: false
      include_response_body: false
    
    error_logs:
      enabled: true
      include_stack_trace: true
      alert_on_errors: true
    
    security_logs:
      enabled: true
      include_ip_address: true
      track_failed_auth: true
    
    performance_logs:
      enabled: true
      track_response_times: true
      track_database_queries: true
```

### Monitoring Alerts
```yaml
alerts:
  error_rate:
    threshold: 5%
    window: 5 minutes
    notification: email, slack
  
  response_time:
    threshold: 2000ms
    percentile: 95
    window: 10 minutes
  
  email_delivery_failure:
    threshold: 10%
    window: 15 minutes
    immediate_notification: true
  
  oauth_failures:
    threshold: 20 failures
    window: 5 minutes
    notification: email
```

## Data Privacy & Compliance

### Data Retention Policy
```yaml
data_retention:
  user_profiles: 
    duration: "Indefinite (while account active)"
    deletion: "30 days after account deletion"
  
  email_logs:
    duration: "2 years"
    archival: "After 1 year, move to cold storage"
  
  oauth_tokens:
    duration: "30 days or until refresh"
    deletion: "Immediate on user disconnect"
  
  user_sessions:
    duration: "7 days"
    cleanup: "Daily automated cleanup"
  
  system_metrics:
    duration: "5 years"
    aggregation: "Daily → Weekly → Monthly"
```

### GDPR Compliance
```yaml
gdpr_compliance:
  data_processing_basis: "Legitimate interest for service provision"
  user_rights:
    - "Right to access"
    - "Right to rectification"
    - "Right to erasure"
    - "Right to data portability"
    - "Right to object"
  
  data_export:
    format: JSON
    includes: "All user data and email logs"
    delivery: "Secure download link"
  
  data_deletion:
    user_request: "Complete within 30 days"
    automatic: "Account inactive for 2+ years"
    verification: "Email confirmation required"
```

## Integration Specifications

### Frontend Framework Compatibility
```yaml
supported_frameworks:
  - name: "React"
    versions: "16.8+, 17.x, 18.x"
    auth_library: "@react-oauth/google"
    
  - name: "Vue.js"
    versions: "2.6+, 3.x"
    auth_library: "vue-google-oauth2"
    
  - name: "Angular"
    versions: "10+, 11+, 12+, 13+, 14+, 15+"
    auth_library: "@angular/google-oauth2"
    
  - name: "Next.js"
    versions: "12.x, 13.x, 14.x"
    auth_library: "next-auth with GoogleProvider"
    
  - name: "Vanilla JavaScript"
    compatibility: "ES6+, Google Identity Services"
```

### Backend Framework Compatibility
```yaml
supported_backends:
  - name: "Node.js/Express"
    versions: "14.x, 16.x, 18.x, 20.x"
    auth_library: "google-auth-library"
    
  - name: "Python/FastAPI"
    versions: "3.8+, 3.9+, 3.10+, 3.11+"
    auth_library: "google-auth"
    
  - name: "Python/Django"
    versions: "3.2+, 4.x"
    auth_library: "google-auth-oauthlib"
    
  - name: "Java/Spring Boot"
    versions: "2.6+, 2.7+, 3.x"
    auth_library: "google-auth-library-java"
    
  - name: "C#/.NET"
    versions: ".NET Core 3.1+, .NET 5+, .NET 6+"
    auth_library: "Google.Apis.Auth"
```

## Deployment Configuration

### Docker Configuration
```yaml
docker:
  base_image: "python:3.11-slim"
  expose_port: 8000
  environment_variables:
    - GOOGLE_PROJECT_ID
    - EMAILMCP_API_KEY
    - GOOGLE_CLIENT_ID
    - GOOGLE_CLIENT_SECRET
  
  health_check:
    endpoint: "/health"
    interval: 30s
    timeout: 10s
    retries: 3
  
  resource_limits:
    memory: "512Mi"
    cpu: "0.5"
```

### Cloud Run Configuration
```yaml
cloud_run:
  service_name: "emailmcp"
  region: "us-central1"
  platform: "managed"
  
  scaling:
    min_instances: 1
    max_instances: 100
    concurrency: 80
    cpu_utilization: 70
  
  networking:
    ingress: "all"
    vpc_connector: null
    
  security:
    service_account: "emailmcp-service-account@mcporionac.iam.gserviceaccount.com"
    allow_unauthenticated: true
```

## Version Information

```yaml
system_version:
  current: "1.0.0"
  release_date: "2025-10-04"
  
  changelog:
    "1.0.0":
      date: "2025-10-04"
      changes:
        - "Initial production release"
        - "Multi-tenant architecture"
        - "Google OAuth integration"
        - "Firestore data storage"
        - "Cloud Run deployment"
        - "API key authentication"
        - "Rate limiting"
        - "Comprehensive logging"
  
  roadmap:
    "1.1.0":
      planned_date: "2025-11-01"
      features:
        - "Email templates"
        - "Bulk email sending"
        - "Advanced analytics"
        - "Webhook notifications"
    
    "1.2.0":
      planned_date: "2025-12-01"
      features:
        - "Multiple OAuth providers"
        - "Team collaboration"
        - "API versioning"
        - "Enhanced security"
```

---

**Document Version**: 1.0.0  
**Last Updated**: 2025-10-04  
**Next Review**: 2025-11-04  

This metadata document serves as the complete technical specification for the EmailMCP system, ensuring consistent implementation across all integration points and maintaining data integrity throughout the multi-tenant architecture.