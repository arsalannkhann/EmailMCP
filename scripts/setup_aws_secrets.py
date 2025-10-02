#!/usr/bin/env python3
"""
Script to set up Gmail credentials in AWS Secrets Manager
Usage: python scripts/setup_aws_secrets.py
"""
import json
import boto3
import os
import sys
from botocore.exceptions import ClientError

def load_environment():
    """Load environment variables from .env file"""
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        print("Warning: python-dotenv not installed. Make sure environment variables are set manually.")

def get_gmail_credentials():
    """Get Gmail credentials from environment variables"""
    gmail_credentials = {
        "client_id": os.getenv('GMAIL_CLIENT_ID'),
        "client_secret": os.getenv('GMAIL_CLIENT_SECRET'),
        "refresh_token": os.getenv('GMAIL_REFRESH_TOKEN')
    }
    
    missing_vars = [key for key, value in gmail_credentials.items() if not value]
    if missing_vars:
        missing_upper = [var.upper() for var in missing_vars]
        print(f"❌ Error: Missing Gmail credentials in environment variables: {', '.join(missing_upper)}")
        print("\nPlease set the following environment variables:")
        for var in missing_vars:
            print(f"   export {var.upper()}=your_value_here")
        return None
    
    return gmail_credentials

def setup_gmail_secrets():
    """Set up Gmail API credentials in AWS Secrets Manager"""
    print("🔐 Setting up Gmail credentials in AWS Secrets Manager...")
    
    # Load environment
    load_environment()
    
    # Configuration
    region = os.getenv('AWS_REGION', 'us-east-1')
    secrets_name = os.getenv('AWS_SECRETS_NAME')
    
    if not secrets_name:
        print("❌ Error: AWS_SECRETS_NAME environment variable not set")
        print("Please set: export AWS_SECRETS_NAME=your-secrets-base-name")
        return False
    
    # Get Gmail credentials
    gmail_credentials = get_gmail_credentials()
    if not gmail_credentials:
        return False
    
    print(f"📍 AWS Region: {region}")
    print(f"🗂️ Secrets base name: {secrets_name}")
    print(f"📧 Gmail Client ID: {gmail_credentials['client_id'][:20]}...")
    
    try:
        # Create AWS Secrets Manager client
        print("🔗 Connecting to AWS Secrets Manager...")
        client = boto3.client('secretsmanager', region_name=region)
        
        # Create or update the secret
        secret_name = f"{secrets_name}/gmail"
        
        try:
            # Try to update existing secret
            response = client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(gmail_credentials)
            )
            print(f"✅ Updated existing secret: {secret_name}")
            
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                # Create new secret
                response = client.create_secret(
                    Name=secret_name,
                    SecretString=json.dumps(gmail_credentials),
                    Description="Gmail API credentials for MCP service"
                )
                print(f"✅ Created new secret: {secret_name}")
            else:
                raise
        
        print(f"🆔 Secret ARN: {response['ARN']}")
        print(f"🔄 Version ID: {response.get('VersionId', 'N/A')}")
        
        # Test retrieval
        print("🧪 Testing secret retrieval...")
        test_response = client.get_secret_value(SecretId=secret_name)
        test_data = json.loads(test_response['SecretString'])
        
        if test_data['client_id'] == gmail_credentials['client_id']:
            print("✅ Secret retrieval test passed!")
        else:
            print("⚠️ Warning: Secret retrieval test failed - data mismatch")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up secrets: {str(e)}")
        return False

def verify_aws_credentials():
    """Verify AWS credentials are configured"""
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            print("❌ Error: AWS credentials not configured")
            print("Please configure AWS credentials using one of:")
            print("   - AWS CLI: aws configure")
            print("   - Environment variables: AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY")
            print("   - IAM roles (if running on EC2)")
            return False
        
        print(f"✅ AWS credentials configured (Access Key: {credentials.access_key[:8]}...)")
        return True
        
    except Exception as e:
        print(f"❌ Error checking AWS credentials: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Gmail AWS Secrets Manager Setup")
    print("=" * 40)
    
    # Verify AWS credentials
    if not verify_aws_credentials():
        sys.exit(1)
    
    # Setup secrets
    success = setup_gmail_secrets()
    
    if success:
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Update your production .env file to remove Gmail credentials")
        print("2. Set ENVIRONMENT=production")
        print("3. Deploy your application")
        print("\nYour Gmail credentials are now securely stored in AWS Secrets Manager!")
    else:
        print("\n💥 Setup failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()