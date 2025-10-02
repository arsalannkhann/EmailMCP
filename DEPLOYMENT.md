# EmailMCP AWS Fargate Deployment Guide

Complete step-by-step guide for deploying EmailMCP service on AWS Fargate with Gmail API integration.

## Prerequisites

Before starting the deployment, ensure you have:

- ✅ AWS CLI installed and configured (`aws configure`)
- ✅ Docker installed and running
- ✅ Python 3.11+ installed
- ✅ Gmail API credentials (Client ID, Client Secret, Refresh Token)
- ✅ Appropriate AWS permissions (EC2, ECS, ECR, Secrets Manager, CloudFormation, etc.)

## Architecture Overview

The deployment creates:
- **VPC** with public/private subnets across 2 AZs
- **Application Load Balancer** (ALB) for traffic distribution
- **ECS Fargate** cluster and service for container orchestration
- **ECR Repository** for Docker image storage
- **ElastiCache Redis** for caching and session management
- **AWS Secrets Manager** for secure credential storage
- **CloudWatch** for logging and monitoring

## Step 1: Clone and Setup Local Environment

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

## Step 2: Configure Environment Variables

```bash
# Copy template and configure for development
cp .env.template .env

# Edit .env with your Gmail API credentials
nano .env
```

Required variables for development:
```env
GMAIL_CLIENT_ID=your_client_id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your_client_secret
GMAIL_REFRESH_TOKEN=1//your_refresh_token
GMAIL_FROM_EMAIL=your-email@gmail.com
MCP_API_KEY=your-secure-api-key
```

## Step 3: Test Application Locally

```bash
# Start local Redis (if you have Docker)
docker run -d --name redis -p 6379:6379 redis:alpine

# Or use Docker Compose
docker-compose up -d redis

# Run the application
python -m uvicorn src.mcp.main:app --host 0.0.0.0 --port 8001 --reload

# Test endpoints
curl http://localhost:8001/health
curl http://localhost:8001/docs  # API documentation
```

## Step 4: Setup Gmail API Credentials in AWS

```bash
# Configure AWS credentials (if not already done)
aws configure

# Run the Gmail credentials setup script
python3 setup_gmail_credentials.py

# Or with custom settings
python3 setup_gmail_credentials.py myproject us-west-2
```

The script will:
1. ✅ Verify AWS access and permissions
2. ✅ Prompt for Gmail API credentials
3. ✅ Test the credentials
4. ✅ Store them securely in AWS Secrets Manager

## Step 5: Deploy AWS Infrastructure

### Deploy CloudFormation Stack

```bash
# Deploy with default parameters
aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yml \
  --stack-name emailmcp-stack \
  --capabilities CAPABILITY_IAM \
  --region us-east-1

# Or with custom parameters
aws cloudformation deploy \
  --template-file infrastructure/cloudformation.yml \
  --stack-name emailmcp-production \
  --parameter-overrides \
    ProjectName=emailmcp \
    Environment=production \
  --capabilities CAPABILITY_IAM \
  --region us-east-1
```

### Monitor Stack Creation

```bash
# Check stack status
aws cloudformation describe-stacks \
  --stack-name emailmcp-stack \
  --query 'Stacks[0].StackStatus'

# Get stack outputs
aws cloudformation describe-stacks \
  --stack-name emailmcp-stack \
  --query 'Stacks[0].Outputs'
```

## Step 6: Deploy Application to Fargate

### Automated Deployment

```bash
# Make deployment script executable
chmod +x deploy-aws.sh

# Deploy application
./deploy-aws.sh deploy

# Or with custom settings
PROJECT_NAME=emailmcp ENVIRONMENT=production ./deploy-aws.sh deploy
```

The deployment script will:
1. ✅ Build Docker image
2. ✅ Push to ECR repository
3. ✅ Update ECS service with new image
4. ✅ Wait for deployment to complete
5. ✅ Show deployment status

### Manual Deployment Steps

If you prefer manual deployment:

```bash
# 1. Get AWS account ID and ECR repository
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
ECR_REPOSITORY="${AWS_ACCOUNT_ID}.dkr.ecr.us-east-1.amazonaws.com/emailmcp"

# 2. Login to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPOSITORY

# 3. Build and tag image
docker build -t emailmcp:latest .
docker tag emailmcp:latest $ECR_REPOSITORY:latest

# 4. Push image
docker push $ECR_REPOSITORY:latest

# 5. Update ECS service (this will trigger new deployment)
aws ecs update-service \
  --cluster emailmcp-cluster \
  --service emailmcp-service \
  --force-new-deployment \
  --region us-east-1
```

## Step 7: Verify Deployment

### Check Service Health

```bash
# Get load balancer URL
ALB_DNS=$(aws elbv2 describe-load-balancers \
  --names "emailmcp-alb" \
  --query 'LoadBalancers[0].DNSName' \
  --output text)

echo "Load Balancer URL: http://$ALB_DNS"

# Test health endpoint
curl http://$ALB_DNS/health

# Check API documentation
curl http://$ALB_DNS/docs
```

### Test Email Functionality

```bash
# Test email sending
curl -X POST http://$ALB_DNS/api/v1/send-email \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "to": "test@example.com",
    "subject": "Test Email",
    "body": "This is a test email from EmailMCP on AWS Fargate!"
  }'
```

### Monitor Logs

```bash
# View application logs
aws logs tail /ecs/emailmcp --follow --region us-east-1

# View specific log streams
aws logs describe-log-streams \
  --log-group-name /ecs/emailmcp \
  --region us-east-1
```

## Step 8: Configure Domain and SSL (Optional)

### Add Custom Domain

1. Create Route 53 hosted zone for your domain
2. Create ACM certificate for your domain
3. Update ALB listener to use HTTPS and your certificate
4. Update DNS records to point to ALB

### Update CloudFormation for HTTPS

```yaml
# Add to CloudFormation template
Certificate:
  Type: AWS::CertificateManager::Certificate
  Properties:
    DomainName: yourdomain.com
    ValidationMethod: DNS

HTTPSListener:
  Type: AWS::ElasticLoadBalancingV2::Listener
  Properties:
    Certificates:
      - CertificateArn: !Ref Certificate
    DefaultActions:
      - Type: forward
        TargetGroupArn: !Ref ALBTargetGroup
    LoadBalancerArn: !Ref ApplicationLoadBalancer
    Port: 443
    Protocol: HTTPS
```

## Management Commands

### Deployment Management

```bash
# Check deployment status
./deploy-aws.sh status

# Rollback to previous version
./deploy-aws.sh rollback

# Build image only
./deploy-aws.sh build

# Push to ECR only
./deploy-aws.sh push
```

### Service Management

```bash
# Scale service
aws ecs update-service \
  --cluster emailmcp-cluster \
  --service emailmcp-service \
  --desired-count 3

# Restart service
aws ecs update-service \
  --cluster emailmcp-cluster \
  --service emailmcp-service \
  --force-new-deployment

# Stop service
aws ecs update-service \
  --cluster emailmcp-cluster \
  --service emailmcp-service \
  --desired-count 0
```

### Secrets Management

```bash
# Update Gmail credentials
aws secretsmanager update-secret \
  --secret-id emailmcp/gmail \
  --secret-string '{
    "client_id": "new_client_id",
    "client_secret": "new_client_secret", 
    "refresh_token": "new_refresh_token"
  }'

# View secret (without values)
aws secretsmanager describe-secret --secret-id emailmcp/gmail
```

## Troubleshooting

### Common Issues

1. **Service not starting**
   ```bash
   # Check ECS service events
   aws ecs describe-services --cluster emailmcp-cluster --services emailmcp-service
   
   # Check task definition
   aws ecs describe-task-definition --task-definition emailmcp
   ```

2. **Image pull errors**
   ```bash
   # Verify ECR repository exists
   aws ecr describe-repositories --repository-names emailmcp
   
   # Check ECR login
   aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin $ECR_REPOSITORY
   ```

3. **Secrets Manager access issues**
   ```bash
   # Test secret access
   aws secretsmanager get-secret-value --secret-id emailmcp/gmail
   
   # Check IAM permissions for ECS task role
   aws iam get-role-policy --role-name emailmcp-task-role --policy-name SecretsManagerAccess
   ```

4. **Health check failures**
   ```bash
   # Check application logs
   aws logs tail /ecs/emailmcp --follow
   
   # Test health endpoint directly on container
   aws ecs execute-command \
     --cluster emailmcp-cluster \
     --task <task-id> \
     --container emailmcp \
     --interactive \
     --command "curl localhost:8001/health"
   ```

### Performance Tuning

1. **Adjust resource allocation**
   ```yaml
   # In CloudFormation template
   Cpu: 512        # Increase CPU
   Memory: 1024    # Increase memory
   ```

2. **Scale horizontally**
   ```bash
   aws ecs update-service \
     --cluster emailmcp-cluster \
     --service emailmcp-service \
     --desired-count 4
   ```

3. **Optimize Redis configuration**
   ```yaml
   # Use larger Redis instance
   CacheNodeType: cache.t3.small
   NumCacheNodes: 1
   ```

## Cost Optimization

### Resource Usage

- **ALB**: ~$16/month
- **ECS Fargate** (2 tasks): ~$15/month
- **ElastiCache** (t3.micro): ~$12/month
- **ECR Storage**: ~$1/month
- **CloudWatch Logs**: ~$2/month
- **Secrets Manager**: ~$1/month

**Total estimated cost**: ~$47/month

### Cost Reduction Tips

1. Use Fargate Spot pricing for non-critical workloads
2. Configure log retention policies
3. Use smaller instance types for development
4. Implement auto-scaling based on metrics

## Security Considerations

1. **Network Security**
   - Services run in private subnets
   - Security groups restrict access
   - NAT gateways for outbound internet access

2. **Secrets Management**
   - Gmail credentials stored in AWS Secrets Manager
   - IAM roles with least privilege
   - Automatic credential rotation supported

3. **Application Security**
   - API key authentication
   - Rate limiting
   - CORS protection
   - Health checks

## Monitoring and Alerts

### CloudWatch Metrics

Key metrics to monitor:
- ECS service CPU/Memory utilization
- ALB request count and latency
- Redis connection count
- Application error rates

### Set up Alarms

```bash
# CPU utilization alarm
aws cloudwatch put-metric-alarm \
  --alarm-name "EmailMCP-High-CPU" \
  --alarm-description "High CPU utilization" \
  --metric-name CPUUtilization \
  --namespace AWS/ECS \
  --statistic Average \
  --period 300 \
  --threshold 80 \
  --comparison-operator GreaterThanThreshold \
  --evaluation-periods 2
```

## Next Steps

1. 🔧 **Set up monitoring and alerting**
2. 🔒 **Configure SSL certificate and custom domain**
3. 📊 **Implement application metrics and dashboards**
4. 🔄 **Set up CI/CD pipeline for automated deployments**
5. 🧪 **Add integration tests and health checks**
6. 📚 **Create API documentation and usage examples**

## Support

For issues and questions:
1. Check CloudWatch logs for application errors
2. Review AWS service health dashboards
3. Test Gmail API credentials using the setup script
4. Verify network connectivity and security groups

---

**Congratulations!** 🎉 You now have a production-ready EmailMCP service running on AWS Fargate with Gmail API integration, secure credential management, and comprehensive monitoring.