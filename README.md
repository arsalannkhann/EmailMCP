# EmailMCP - Multi-Tenant Email Service

A production-ready email service with complete multi-tenant architecture supporting both AWS and GCP deployments. Users can connect their own Gmail accounts via OAuth and send emails through the service.

## 🚀 Features

- **Multi-Tenant Architecture** - Each user connects their own Gmail account
- **OAuth 2.0 Integration** - Secure Gmail authentication for individual users
- **Gmail API** - Send emails through Gmail API with user credentials
- **Cloud Native** - Deploy on AWS Fargate or GCP Cloud Run
- **Secure Credentials** - AWS Secrets Manager or GCP Secret Manager integration
- **Analytics & Reporting** - Track email sends, success rates, and user activity
- **Scalable** - Auto-scaling serverless architecture
- **API-First** - RESTful API with comprehensive documentation

## 📦 Deployment Options

### GCP Deployment (Recommended)

Complete guide for deploying to Google Cloud Platform with Cloud Run, Secret Manager, and Firestore.

**📖 See [GCP-DEPLOYMENT.md](./GCP-DEPLOYMENT.md) for detailed instructions**

```bash
# Quick Deploy to GCP
./scripts/setup_gcp.sh your-project-id us-central1
python3 scripts/setup_gcp_gmail_credentials.py your-project-id
./scripts/deploy_gcp.sh your-project-id us-central1
```

### AWS Deployment

**📖 See [DEPLOYMENT.md](./DEPLOYMENT.md) for AWS deployment instructions**

## 🔌 Multi-Tenant API

### 1. Initiate OAuth for User
```bash
POST /v1/oauth/authorize
```

### 2. Send Email as User
```bash
POST /v1/users/{user_id}/messages
```

### 3. Get Analytics
```bash
GET /v1/reports/users/{user_id}
```

## 📚 Documentation

- [GCP Deployment Guide](./GCP-DEPLOYMENT.md)
- [AWS Deployment Guide](./DEPLOYMENT.md)
- [Multi-Tenant Integration](./docs/multi-tenant-integration.md)
- [Gmail API Integration](./GMAIL_API_INTEGRATION.md)

---

**Built with ❤️ for scalable, secure, multi-tenant email services**
