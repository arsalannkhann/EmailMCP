#!/bin/bash
set -e

echo "🚀 Deploying MCP Service to Production..."
echo "========================================="

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
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️ $1${NC}"
}

# Check if production environment file exists
if [ ! -f ".env.production" ]; then
    print_error "Production environment file (.env.production) not found!"
    echo "Please create .env.production based on the template"
    exit 1
fi

# Backup current .env if it exists
if [ -f ".env" ]; then
    print_info "Backing up current .env to .env.backup"
    cp .env .env.backup
fi

# Set environment to production
export ENVIRONMENT=production
print_status "Environment set to production"

# Copy production environment
cp .env.production .env
print_status "Production environment configuration loaded"

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if (( $(echo "$python_version < $required_version" | bc -l) )); then
    print_error "Python $required_version or higher is required. Found: $python_version"
    exit 1
fi
print_status "Python version check passed ($python_version)"

# Install dependencies
print_info "Installing dependencies..."
if [ -f "requirements.txt" ]; then
    pip install -r requirements.txt
else
    pip install -e .
fi
print_status "Dependencies installed"

# Verify AWS credentials
print_info "Verifying AWS credentials..."
if aws sts get-caller-identity > /dev/null 2>&1; then
    print_status "AWS credentials verified"
else
    print_error "AWS credentials not configured or invalid"
    print_info "Please configure AWS credentials using:"
    print_info "  - aws configure"
    print_info "  - IAM roles (if running on EC2)"
    print_info "  - Environment variables"
    exit 1
fi

# Set up AWS secrets (optional - may already be done)
print_info "Setting up AWS Secrets Manager (if needed)..."
if python scripts/setup_aws_secrets.py; then
    print_status "AWS Secrets Manager setup completed"
else
    print_warning "AWS Secrets Manager setup failed or already configured"
    print_info "If this is first deployment, make sure to run:"
    print_info "  python scripts/setup_aws_secrets.py"
fi

# Run any database migrations (if needed)
print_info "Running database migrations..."
# Add your migration commands here if you have a database
# Example: alembic upgrade head
print_status "Database migrations completed (none required)"

# Health check function
health_check() {
    local url="http://localhost:${MCP_PORT:-8001}/v1/health"
    local max_attempts=30
    local attempt=1
    
    print_info "Performing health check..."
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$url" > /dev/null 2>&1; then
            print_status "Health check passed!"
            return 0
        fi
        
        echo -n "."
        sleep 2
        attempt=$((attempt + 1))
    done
    
    print_error "Health check failed after $max_attempts attempts"
    return 1
}

# Start the service
print_info "Starting MCP Service..."
print_info "Service will be available at: http://0.0.0.0:${MCP_PORT:-8001}"
print_info "API Documentation: http://0.0.0.0:${MCP_PORT:-8001}/docs"

# Check if we should run in background or foreground
if [ "$1" = "--background" ] || [ "$1" = "-b" ]; then
    print_info "Starting service in background..."
    nohup uvicorn src.mcp.main:app --host 0.0.0.0 --port ${MCP_PORT:-8001} --env-file .env > mcp-service.log 2>&1 &
    
    # Get the PID
    SERVICE_PID=$!
    echo $SERVICE_PID > mcp-service.pid
    
    print_status "Service started with PID: $SERVICE_PID"
    print_info "Logs: tail -f mcp-service.log"
    print_info "Stop: kill $SERVICE_PID or pkill -f 'uvicorn.*mcp'"
    
    # Wait a bit and do health check
    sleep 5
    if health_check; then
        print_status "Deployment completed successfully! 🎉"
    else
        print_error "Service started but health check failed"
        exit 1
    fi
    
else
    print_info "Starting service in foreground (Ctrl+C to stop)..."
    uvicorn src.mcp.main:app --host 0.0.0.0 --port ${MCP_PORT:-8001} --env-file .env
fi

print_status "Deployment completed successfully! 🎉"