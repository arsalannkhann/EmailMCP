#!/usr/bin/env python3
"""
Gmail Credentials Setup Script for AWS Secrets Manager
This script helps you configure Gmail API credentials in AWS Secrets Manager
"""

import json
import sys
import boto3
import logging
from typing import Dict, Optional
from botocore.exceptions import ClientError, NoCredentialsError

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class GmailCredentialsSetup:
    def __init__(self, project_name: str = "emailmcp", aws_region: str = "us-east-1"):
        """
        Initialize the Gmail credentials setup
        
        Args:
            project_name: The project name (used for secret naming)
            aws_region: AWS region where secrets will be stored
        """
        self.project_name = project_name
        self.aws_region = aws_region
        self.secret_name = f"{project_name}/gmail"
        
        try:
            self.secrets_client = boto3.client('secretsmanager', region_name=aws_region)
            self.sts_client = boto3.client('sts', region_name=aws_region)
        except NoCredentialsError:
            logger.error("AWS credentials not configured. Please run 'aws configure' first.")
            sys.exit(1)
    
    def verify_aws_access(self) -> bool:
        """Verify AWS access and permissions"""
        try:
            # Check basic AWS access
            identity = self.sts_client.get_caller_identity()
            logger.info(f"AWS Account: {identity['Account']}")
            logger.info(f"AWS User/Role: {identity['Arn']}")
            
            # Test Secrets Manager access
            try:
                self.secrets_client.list_secrets(MaxResults=1)
                logger.info("AWS Secrets Manager access verified")
                return True
            except ClientError as e:
                logger.error(f"No access to AWS Secrets Manager: {e}")
                return False
                
        except ClientError as e:
            logger.error(f"AWS access verification failed: {e}")
            return False
    
    def get_gmail_credentials_interactive(self) -> Dict[str, str]:
        """Get Gmail credentials from user input"""
        print("\n" + "="*60)
        print("GMAIL API CREDENTIALS SETUP")
        print("="*60)
        print("\nTo get these credentials, you need to:")
        print("1. Go to Google Cloud Console (https://console.cloud.google.com/)")
        print("2. Create a new project or select existing one")
        print("3. Enable Gmail API")
        print("4. Create OAuth 2.0 credentials (Desktop application)")
        print("5. Use OAuth playground or generate refresh token")
        print("\nDetailed guide: https://developers.google.com/gmail/api/quickstart")
        print("-"*60)
        
        credentials = {}
        
        while True:
            client_id = input("\nEnter Gmail Client ID: ").strip()
            if client_id and client_id.endswith('.apps.googleusercontent.com'):
                credentials['client_id'] = client_id
                break
            print("❌ Invalid Client ID format. Should end with '.apps.googleusercontent.com'")
        
        while True:
            client_secret = input("Enter Gmail Client Secret: ").strip()
            if client_secret and len(client_secret) > 10:
                credentials['client_secret'] = client_secret
                break
            print("❌ Client Secret seems too short. Please check and re-enter.")
        
        while True:
            refresh_token = input("Enter Gmail Refresh Token: ").strip()
            if refresh_token and refresh_token.startswith('1//'):
                credentials['refresh_token'] = refresh_token
                break
            print("❌ Invalid Refresh Token format. Should start with '1//'")
        
        # Optional: Test email address
        from_email = input("Enter 'From' email address (optional): ").strip()
        if from_email and '@' in from_email:
            credentials['from_email'] = from_email
        
        return credentials
    
    def validate_credentials_format(self, credentials: Dict[str, str]) -> bool:
        """Validate credentials format"""
        required_fields = ['client_id', 'client_secret', 'refresh_token']
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate Client ID format
        if not credentials['client_id'].endswith('.apps.googleusercontent.com'):
            logger.error("Invalid Client ID format")
            return False
        
        # Validate Refresh Token format
        if not credentials['refresh_token'].startswith('1//'):
            logger.error("Invalid Refresh Token format")
            return False
        
        logger.info("✅ Credentials format validation passed")
        return True
    
    def test_gmail_credentials(self, credentials: Dict[str, str]) -> bool:
        """Test Gmail credentials by making a test API call"""
        try:
            import httpx
            
            logger.info("Testing Gmail credentials...")
            
            # Test token refresh
            token_url = "https://oauth2.googleapis.com/token"
            token_data = {
                'client_id': credentials['client_id'],
                'client_secret': credentials['client_secret'],
                'refresh_token': credentials['refresh_token'],
                'grant_type': 'refresh_token'
            }
            
            with httpx.Client() as client:
                response = client.post(token_url, data=token_data)
                
                if response.status_code == 200:
                    token_info = response.json()
                    access_token = token_info.get('access_token')
                    
                    if access_token:
                        # Test Gmail API access
                        gmail_url = "https://gmail.googleapis.com/gmail/v1/users/me/profile"
                        headers = {'Authorization': f'Bearer {access_token}'}
                        
                        profile_response = client.get(gmail_url, headers=headers)
                        
                        if profile_response.status_code == 200:
                            profile = profile_response.json()
                            logger.info(f"✅ Gmail API test successful for: {profile.get('emailAddress')}")
                            return True
                        else:
                            logger.error(f"Gmail API test failed: {profile_response.status_code}")
                            return False
                    else:
                        logger.error("No access token received")
                        return False
                else:
                    logger.error(f"Token refresh failed: {response.status_code} - {response.text}")
                    return False
                    
        except ImportError:
            logger.warning("httpx not available, skipping credential test")
            return True
        except Exception as e:
            logger.error(f"Credential test failed: {e}")
            return False
    
    def create_or_update_secret(self, credentials: Dict[str, str]) -> bool:
        """Create or update the secret in AWS Secrets Manager"""
        try:
            secret_value = json.dumps(credentials, indent=2)
            
            # Check if secret exists
            try:
                self.secrets_client.describe_secret(SecretId=self.secret_name)
                # Secret exists, update it
                response = self.secrets_client.update_secret(
                    SecretId=self.secret_name,
                    SecretString=secret_value,
                    Description=f"Gmail API credentials for {self.project_name} service"
                )
                logger.info(f"✅ Secret updated successfully: {self.secret_name}")
                
            except ClientError as e:
                if e.response['Error']['Code'] == 'ResourceNotFoundException':
                    # Secret doesn't exist, create it
                    response = self.secrets_client.create_secret(
                        Name=self.secret_name,
                        SecretString=secret_value,
                        Description=f"Gmail API credentials for {self.project_name} service",
                        Tags=[
                            {'Key': 'Project', 'Value': self.project_name},
                            {'Key': 'Service', 'Value': 'EmailMCP'},
                            {'Key': 'Type', 'Value': 'Gmail-Credentials'}
                        ]
                    )
                    logger.info(f"✅ Secret created successfully: {self.secret_name}")
                else:
                    raise e
            
            return True
            
        except ClientError as e:
            logger.error(f"Failed to create/update secret: {e}")
            return False
    
    def show_secret_info(self):
        """Show information about the created secret"""
        try:
            response = self.secrets_client.describe_secret(SecretId=self.secret_name)
            
            print("\n" + "="*60)
            print("SECRET INFORMATION")
            print("="*60)
            print(f"Secret Name: {response['Name']}")
            print(f"Secret ARN: {response['ARN']}")
            print(f"Region: {self.aws_region}")
            print(f"Created: {response.get('CreatedDate', 'N/A')}")
            print(f"Last Updated: {response.get('LastChangedDate', 'N/A')}")
            print("-"*60)
            print("This secret will be automatically used by your EmailMCP service")
            print("when deployed on AWS Fargate.")
            print("="*60)
            
        except ClientError as e:
            logger.error(f"Failed to get secret info: {e}")
    
    def run_interactive_setup(self):
        """Run the interactive setup process"""
        print("🚀 EmailMCP Gmail Credentials Setup")
        print(f"Project: {self.project_name}")
        print(f"AWS Region: {self.aws_region}")
        print(f"Secret Name: {self.secret_name}")
        
        # Verify AWS access
        if not self.verify_aws_access():
            logger.error("Cannot proceed without proper AWS access")
            sys.exit(1)
        
        # Get credentials from user
        credentials = self.get_gmail_credentials_interactive()
        
        # Validate credentials
        if not self.validate_credentials_format(credentials):
            logger.error("Credential validation failed")
            sys.exit(1)
        
        # Test credentials (optional)
        print("\n🧪 Testing Gmail credentials...")
        if self.test_gmail_credentials(credentials):
            logger.info("✅ Credential test passed")
        else:
            choice = input("\n⚠️  Credential test failed. Continue anyway? (y/N): ").strip().lower()
            if choice != 'y':
                logger.info("Setup cancelled")
                sys.exit(1)
        
        # Create/update secret
        print("\n💾 Storing credentials in AWS Secrets Manager...")
        if self.create_or_update_secret(credentials):
            logger.info("✅ Credentials stored successfully")
            self.show_secret_info()
        else:
            logger.error("Failed to store credentials")
            sys.exit(1)
        
        print("\n🎉 Setup completed successfully!")
        print("\nNext steps:")
        print("1. Deploy your CloudFormation stack: aws cloudformation deploy ...")
        print("2. Deploy your application: ./deploy-aws.sh deploy")
        print("3. Test your email service: curl http://your-alb-url/health")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print("Gmail Credentials Setup Script")
            print("\nUsage:")
            print("  python3 setup_gmail_credentials.py [project_name] [aws_region]")
            print("\nExamples:")
            print("  python3 setup_gmail_credentials.py")
            print("  python3 setup_gmail_credentials.py myproject us-west-2")
            print("\nEnvironment Variables:")
            print("  PROJECT_NAME - Project name (default: emailmcp)")
            print("  AWS_REGION   - AWS region (default: us-east-1)")
            sys.exit(0)
    
    # Get configuration from arguments or environment
    import os
    project_name = sys.argv[1] if len(sys.argv) > 1 else os.getenv('PROJECT_NAME', 'emailmcp')
    aws_region = sys.argv[2] if len(sys.argv) > 2 else os.getenv('AWS_REGION', 'us-east-1')
    
    # Run setup
    setup = GmailCredentialsSetup(project_name, aws_region)
    setup.run_interactive_setup()

if __name__ == "__main__":
    main()