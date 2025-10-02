import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
from typing import Dict, Any, Optional
from ..core.config import settings
from ..core.logging import log

class AWSSecretsManager:
    """AWS Secrets Manager service for secure credential management"""
    
    def __init__(self):
        self.region = settings.aws_region
        self.secrets_name = settings.aws_secrets_name
        self._client = None
        
    @property
    def client(self):
        """Lazy initialization of AWS Secrets Manager client"""
        if self._client is None:
            self._client = boto3.client('secretsmanager', region_name=self.region)
        return self._client
    
    async def get_email_credentials(self, provider: str = "gmail") -> Dict[str, Any]:
        """
        Get email credentials from AWS Secrets Manager
        
        Args:
            provider: Email provider name (gmail, outlook, etc.)
            
        Returns:
            Dictionary containing credentials
        """
        try:
            secret_name = f"{self.secrets_name}/{provider}"
            
            response = self.client.get_secret_value(SecretId=secret_name)
            secret_data = json.loads(response['SecretString'])
            
            log.info(f"Successfully retrieved {provider} credentials from AWS Secrets Manager")
            return secret_data
            
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'ResourceNotFoundException':
                log.error(f"Secret {secret_name} not found in AWS Secrets Manager")
            elif error_code == 'InvalidRequestException':
                log.error(f"Invalid request for secret {secret_name}")
            elif error_code == 'InvalidParameterException':
                log.error(f"Invalid parameter for secret {secret_name}")
            else:
                log.error(f"AWS Secrets Manager error: {error_code}")
            raise
            
        except BotoCoreError as e:
            log.error(f"AWS SDK error: {str(e)}")
            raise
            
        except json.JSONDecodeError as e:
            log.error(f"Invalid JSON in secret {secret_name}: {str(e)}")
            raise
    
    async def update_refresh_token(self, provider: str, new_refresh_token: str) -> bool:
        """
        Update refresh token in AWS Secrets Manager
        
        Args:
            provider: Email provider name
            new_refresh_token: New refresh token to store
            
        Returns:
            True if successful, False otherwise
        """
        try:
            secret_name = f"{self.secrets_name}/{provider}"
            
            # Get current secret
            current_secret = await self.get_email_credentials(provider)
            
            # Update refresh token
            current_secret['refresh_token'] = new_refresh_token
            
            # Store updated secret
            self.client.update_secret(
                SecretId=secret_name,
                SecretString=json.dumps(current_secret)
            )
            
            log.info(f"Successfully updated {provider} refresh token in AWS Secrets Manager")
            return True
            
        except Exception as e:
            log.error(f"Failed to update refresh token for {provider}: {str(e)}")
            return False
    
    def is_configured(self) -> bool:
        """Check if AWS Secrets Manager is properly configured"""
        return bool(self.region and self.secrets_name)