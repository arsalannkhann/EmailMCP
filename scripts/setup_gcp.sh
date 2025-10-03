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

echo "🚀 EmailMCP GCP Setup"
echo "====================="
echo ""

# Get configuration from arguments or environment
PROJECT_ID=${1:-${GCP_PROJECT_ID}}
REGION=${2:-${GCP_REGION:-us-central1}}
SERVICE_NAME="emailmcp"

if [ -z "$PROJECT_ID" ]; then
    print_error "Project ID is required"
    echo "Usage: $0 <project-id> [region]"
    echo "Or set GCP_PROJECT_ID environment variable"
    exit 1
fi

print_info "Project ID: $PROJECT_ID"
print_info "Region: $REGION"
print_info "Service Name: $SERVICE_NAME"
echo ""

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed"
    echo "Please install from: https://cloud.google.com/sdk/docs/install"
    exit 1
fi
print_status "gcloud CLI is installed"

# Set project
print_info "Setting project..."
gcloud config set project $PROJECT_ID
print_status "Project set to $PROJECT_ID"

# Enable required APIs
print_info "Enabling required GCP APIs..."
apis=(
    "run.googleapis.com"
    "secretmanager.googleapis.com"
    "firestore.googleapis.com"
    "artifactregistry.googleapis.com"
    "cloudbuild.googleapis.com"
    "cloudresourcemanager.googleapis.com"
    "iam.googleapis.com"
)

for api in "${apis[@]}"; do
    print_info "Enabling $api..."
    gcloud services enable $api --quiet
done
print_status "All APIs enabled"

# Create service account
print_info "Creating service account..."
SERVICE_ACCOUNT="${SERVICE_NAME}-service@${PROJECT_ID}.iam.gserviceaccount.com"

if gcloud iam service-accounts describe $SERVICE_ACCOUNT &> /dev/null; then
    print_warning "Service account already exists"
else
    gcloud iam service-accounts create ${SERVICE_NAME}-service \
        --display-name="EmailMCP Service Account" \
        --description="Service account for EmailMCP Cloud Run service"
    print_status "Service account created"
fi

# Grant permissions
print_info "Granting IAM permissions..."

# Secret Manager access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/secretmanager.secretAccessor" \
    --quiet

# Firestore access
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:${SERVICE_ACCOUNT}" \
    --role="roles/datastore.user" \
    --quiet

print_status "IAM permissions granted"

# Create Artifact Registry repository
print_info "Creating Artifact Registry repository..."
REPO_EXISTS=$(gcloud artifacts repositories describe $SERVICE_NAME \
    --location=$REGION 2>&1 | grep -c "NOT_FOUND" || true)

if [ "$REPO_EXISTS" -eq 0 ]; then
    print_warning "Artifact Registry repository already exists"
else
    gcloud artifacts repositories create $SERVICE_NAME \
        --repository-format=docker \
        --location=$REGION \
        --description="EmailMCP Docker repository"
    print_status "Artifact Registry repository created"
fi

# Setup Firestore
print_info "Setting up Firestore..."
FIRESTORE_EXISTS=$(gcloud firestore databases list 2>&1 | grep -c "(default)" || true)

if [ "$FIRESTORE_EXISTS" -gt 0 ]; then
    print_warning "Firestore database already exists"
else
    print_info "Creating Firestore database..."
    gcloud firestore databases create --location=$REGION --quiet
    print_status "Firestore database created"
fi

# Create secrets (empty - to be filled by user)
print_info "Creating Secret Manager secrets..."

# Gmail OAuth config secret
SECRET_NAME="${SERVICE_NAME}-gmail-oauth-config"
if gcloud secrets describe $SECRET_NAME &> /dev/null; then
    print_warning "Secret $SECRET_NAME already exists"
else
    echo '{"client_id":"","client_secret":"","redirect_uri":""}' | \
        gcloud secrets create $SECRET_NAME \
        --data-file=- \
        --replication-policy="automatic" \
        --labels="service=${SERVICE_NAME}"
    print_status "Secret $SECRET_NAME created"
fi

# API Key secret
SECRET_NAME="${SERVICE_NAME}-api-key"
if gcloud secrets describe $SECRET_NAME &> /dev/null; then
    print_warning "Secret $SECRET_NAME already exists"
else
    # Generate a random API key
    API_KEY=$(openssl rand -hex 32)
    echo $API_KEY | gcloud secrets create $SECRET_NAME \
        --data-file=- \
        --replication-policy="automatic" \
        --labels="service=${SERVICE_NAME}"
    print_status "Secret $SECRET_NAME created with random API key"
    print_info "Your API Key: $API_KEY"
    print_warning "Save this API key securely!"
fi

# Grant service account access to secrets
print_info "Granting service account access to secrets..."
for secret in "${SERVICE_NAME}-gmail-oauth-config" "${SERVICE_NAME}-api-key"; do
    gcloud secrets add-iam-policy-binding $secret \
        --member="serviceAccount:${SERVICE_ACCOUNT}" \
        --role="roles/secretmanager.secretAccessor" \
        --quiet
done
print_status "Secret access granted"

echo ""
echo "================================"
print_status "Setup completed successfully! 🎉"
echo "================================"
echo ""
echo "Next steps:"
echo "1. Update Gmail OAuth credentials:"
echo "   gcloud secrets versions add ${SERVICE_NAME}-gmail-oauth-config --data-file=credentials.json"
echo ""
echo "2. Build and push Docker image:"
echo "   gcloud builds submit --tag ${REGION}-docker.pkg.dev/${PROJECT_ID}/${SERVICE_NAME}/${SERVICE_NAME}:latest"
echo ""
echo "3. Deploy to Cloud Run:"
echo "   ./scripts/deploy_gcp.sh $PROJECT_ID $REGION"
echo ""
echo "Useful commands:"
echo "  - View secrets: gcloud secrets list"
echo "  - View logs: gcloud run services logs read ${SERVICE_NAME} --region=${REGION}"
echo ""
