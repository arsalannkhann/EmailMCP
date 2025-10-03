#!/usr/bin/env python3
"""
Gmail Credentials Setup Script for GCP Secret Manager
This script helps you configure Gmail API credentials in GCP Secret Manager
"""

import json
import sys
import subprocess
import logging
from typing import Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class GCPGmailCredentialsSetup:
    """Setup Gmail credentials in GCP Secret Manager"""
    
    def __init__(self, project_id: str, service_name: str = "emailmcp"):
        """
        Initialize the Gmail credentials setup
        
        Args:
            project_id: GCP project ID
            service_name: Service name (used for secret naming)
        """
        self.project_id = project_id
        self.service_name = service_name
        self.secret_name = f"{service_name}-gmail-oauth-config"
        
    def verify_gcloud_auth(self) -> bool:
        """Verify gcloud authentication"""
        try:
            result = subprocess.run(
                ['gcloud', 'auth', 'list', '--format=value(account)'],
                capture_output=True,
                text=True,
                check=True
            )
            
            if result.stdout.strip():
                logger.info(f"✅ Authenticated as: {result.stdout.strip()}")
                return True
            else:
                logger.error("❌ No authenticated accounts found")
                return False
                
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Failed to verify authentication: {e}")
            return False
    
    def verify_project_access(self) -> bool:
        """Verify access to GCP project"""
        try:
            result = subprocess.run(
                ['gcloud', 'projects', 'describe', self.project_id],
                capture_output=True,
                text=True,
                check=True
            )
            
            logger.info(f"✅ Access verified for project: {self.project_id}")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"❌ Cannot access project {self.project_id}: {e}")
            return False
    
    def get_gmail_credentials(self) -> Optional[Dict[str, str]]:
        """Get Gmail API credentials from user input"""
        print("\n📧 Gmail API Credentials Setup")
        print("=" * 50)
        print("\nYou need to provide your Gmail API OAuth credentials.")
        print("Get them from: https://console.cloud.google.com/apis/credentials")
        print()
        
        try:
            client_id = input("Enter Gmail Client ID: ").strip()
            if not client_id:
                logger.error("Client ID cannot be empty")
                return None
            
            client_secret = input("Enter Gmail Client Secret: ").strip()
            if not client_secret:
                logger.error("Client Secret cannot be empty")
                return None
            
            redirect_uri = input("Enter Redirect URI (e.g., https://your-domain.com/v1/oauth/callback): ").strip()
            if not redirect_uri:
                logger.error("Redirect URI cannot be empty")
                return None
            
            return {
                "client_id": client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri
            }
            
        except KeyboardInterrupt:
            print("\n\n⚠️  Setup cancelled by user")
            return None
    
    def test_credentials(self, credentials: Dict[str, str]) -> bool:
        """Test Gmail credentials format"""
        required_fields = ["client_id", "client_secret", "redirect_uri"]
        
        for field in required_fields:
            if field not in credentials or not credentials[field]:
                logger.error(f"❌ Missing required field: {field}")
                return False
        
        # Basic validation
        if not credentials["client_id"].endswith(".apps.googleusercontent.com"):
            logger.warning("⚠️  Client ID doesn't look like a Google OAuth client ID")
        
        if not credentials["redirect_uri"].startswith(("http://", "https://")):
            logger.error("❌ Redirect URI must start with http:// or https://")
            return False
        
        logger.info("✅ Credentials format validated")
        return True
    
    def create_or_update_secret(self, credentials: Dict[str, str]) -> bool:
        """Create or update the secret in GCP Secret Manager"""
        try:
            secret_value = json.dumps(credentials, indent=2)
            
            # Check if secret exists
            try:
                subprocess.run(
                    ['gcloud', 'secrets', 'describe', self.secret_name, '--project', self.project_id],
                    capture_output=True,
                    check=True
                )
                secret_exists = True
                logger.info(f"📝 Secret {self.secret_name} exists, will update")
            except subprocess.CalledProcessError:
                secret_exists = False
                logger.info(f"📝 Secret {self.secret_name} doesn't exist, will create")
            
            if not secret_exists:
                # Create the secret
                subprocess.run(
                    [
                        'gcloud', 'secrets', 'create', self.secret_name,
                        '--project', self.project_id,
                        '--replication-policy=automatic',
                        f'--labels=service={self.service_name},type=oauth-config'
                    ],
                    check=True
                )
                logger.info(f"✅ Created secret: {self.secret_name}")
            
            # Add new version with credentials
            process = subprocess.Popen(
                [
                    'gcloud', 'secrets', 'versions', 'add', self.secret_name,
                    '--project', self.project_id,
                    '--data-file=-'
                ],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            stdout, stderr = process.communicate(input=secret_value)
            
            if process.returncode != 0:
                logger.error(f"❌ Failed to add secret version: {stderr}")
                return False
            
            logger.info(f"✅ Secret stored successfully: {self.secret_name}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error storing secret: {str(e)}")
            return False
    
    def test_secret_retrieval(self) -> bool:
        """Test retrieving the secret"""
        try:
            result = subprocess.run(
                [
                    'gcloud', 'secrets', 'versions', 'access', 'latest',
                    '--secret', self.secret_name,
                    '--project', self.project_id
                ],
                capture_output=True,
                text=True,
                check=True
            )
            
            test_data = json.loads(result.stdout)
            
            if "client_id" in test_data:
                logger.info("✅ Secret retrieval test passed!")
                return True
            else:
                logger.warning("⚠️  Secret retrieval test failed - data mismatch")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error testing secret retrieval: {str(e)}")
            return False
    
    def run_interactive_setup(self):
        """Run the interactive setup process"""
        print("\n🚀 Gmail Credentials Setup for GCP Secret Manager")
        print("=" * 60)
        print(f"Project ID: {self.project_id}")
        print(f"Secret Name: {self.secret_name}")
        print()
        
        # Verify authentication
        if not self.verify_gcloud_auth():
            logger.error("Please authenticate with: gcloud auth login")
            sys.exit(1)
        
        # Verify project access
        if not self.verify_project_access():
            logger.error("Please check your project ID and permissions")
            sys.exit(1)
        
        # Get credentials
        credentials = self.get_gmail_credentials()
        if not credentials:
            sys.exit(1)
        
        # Test credentials format
        if not self.test_credentials(credentials):
            sys.exit(1)
        
        # Store in Secret Manager
        if not self.create_or_update_secret(credentials):
            sys.exit(1)
        
        # Test retrieval
        self.test_secret_retrieval()
        
        print("\n" + "=" * 60)
        print("🎉 Setup completed successfully!")
        print("=" * 60)
        print("\nNext steps:")
        print("1. Deploy your application to Cloud Run")
        print("2. Test the OAuth flow with a user")
        print("3. Monitor logs for any issues")
        print("\nUseful commands:")
        print(f"  - View secret: gcloud secrets versions access latest --secret={self.secret_name}")
        print(f"  - Update secret: gcloud secrets versions add {self.secret_name} --data-file=credentials.json")
        print()


def main():
    """Main function"""
    if len(sys.argv) > 1:
        if sys.argv[1] in ['-h', '--help', 'help']:
            print("Gmail Credentials Setup for GCP Secret Manager")
            print("\nUsage:")
            print("  python3 setup_gcp_gmail_credentials.py [project_id] [service_name]")
            print("\nExamples:")
            print("  python3 setup_gcp_gmail_credentials.py my-project")
            print("  python3 setup_gcp_gmail_credentials.py my-project emailmcp")
            print("\nEnvironment Variables:")
            print("  GCP_PROJECT_ID - GCP project ID (default: required)")
            print("  SERVICE_NAME   - Service name (default: emailmcp)")
            sys.exit(0)
    
    # Get configuration from arguments or environment
    import os
    project_id = sys.argv[1] if len(sys.argv) > 1 else os.getenv('GCP_PROJECT_ID')
    service_name = sys.argv[2] if len(sys.argv) > 2 else os.getenv('SERVICE_NAME', 'emailmcp')
    
    if not project_id:
        logger.error("Project ID is required")
        print("\nUsage: python3 setup_gcp_gmail_credentials.py <project_id> [service_name]")
        sys.exit(1)
    
    # Run setup
    setup = GCPGmailCredentialsSetup(project_id, service_name)
    setup.run_interactive_setup()


if __name__ == "__main__":
    main()
