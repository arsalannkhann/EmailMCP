#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
print_status() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

echo "🚀 Deploying EmailMCP to GCP Cloud Run"
echo "======================================="
echo ""

# Get configuration
PROJECT_ID=${1:-${GCP_PROJECT_ID}}
REGION=${2:-${GCP_REGION:-us-central1}}
SERVICE_NAME="emailmcp"

if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID is required"
    echo "Usage: $0 <project-id> [region]"
    exit 1
fi

print_info "Project ID: $PROJECT_ID"
print_info "Region: $REGION"
print_info "Service Name: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed"
    exit 1
fi

# Check if docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed"
    exit 1
fi

# Set project
gcloud config set project $PROJECT_ID
print_status "Project set"

# Build image
IMAGE_NAME="${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:latest"
print_info "Building container image..."
print_info "Image: $IMAGE_NAME"

# Use Cloud Build for faster builds
print_info "Submitting build to Cloud Build..."
gcloud builds submit --tag $IMAGE_NAME .

print_status "Container image built and pushed"

# Deploy to Cloud Run
print_info "Deploying to Cloud Run..."

gcloud run deploy $SERVICE_NAME \
    --image=$IMAGE_NAME \
    --platform=managed \
    --region=$REGION \
    --service-account="${SERVICE_NAME}-service@${PROJECT_ID}.iam.gserviceaccount.com" \
    --allow-unauthenticated \
    --port=8080 \
    --memory=1Gi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=300 \
    --set-env-vars="ENVIRONMENT=production,GCP_PROJECT_ID=${PROJECT_ID},GCP_REGION=${REGION},PREFERRED_EMAIL_PROVIDER=gmail_api,LOG_LEVEL=INFO" \
    --set-secrets="MCP_API_KEY=${SERVICE_NAME}-api-key:latest,GMAIL_CLIENT_ID=${SERVICE_NAME}-gmail-oauth-config:latest,GMAIL_CLIENT_SECRET=${SERVICE_NAME}-gmail-oauth-config:latest"

print_status "Deployment completed"

# Get service URL
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME \
    --region=$REGION \
    --format='value(status.url)')

echo ""
echo "================================"
print_status "Deployment successful! 🎉"
echo "================================"
echo ""
print_info "Service URL: $SERVICE_URL"
echo ""
echo "Test the service:"
echo "  curl ${SERVICE_URL}/health"
echo ""
echo "View logs:"
echo "  gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo ""
echo "Update service:"
echo "  ./scripts/deploy_gcp.sh $PROJECT_ID $REGION"
echo ""
