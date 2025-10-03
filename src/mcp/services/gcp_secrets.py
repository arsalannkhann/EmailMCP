"""
GCP Secret Manager service for secure credential management in multi-tenant environment
"""
import json
from typing import Dict, Any, Optional
from google.cloud import secretmanager
from google.api_core import exceptions

from ..core.config import settings
from ..core.logging import log


class GCPSecretsManager:
    """GCP Secret Manager service for secure credential management"""
    
    def __init__(self):
        self.project_id = getattr(settings, 'gcp_project_id', None)
        if not self.project_id:
            raise ValueError("GCP_PROJECT_ID environment variable is required")
        
        self._client = None
    
    @property
    def client(self):
        """Lazy initialization of GCP Secret Manager client"""
        if self._client is None:
            self._client = secretmanager.SecretManagerServiceClient()
        return self._client
    
    def _get_secret_path(self, secret_name: str) -> str:
        """Get full secret path"""
        return f"projects/{self.project_id}/secrets/{secret_name}"
    
    def _get_secret_version_path(self, secret_name: str, version: str = "latest") -> str:
        """Get full secret version path"""
        return f"projects/{self.project_id}/secrets/{secret_name}/versions/{version}"
    
    async def get_secret(self, secret_name: str) -> Optional[Dict[str, Any]]:
        """
        Get secret from GCP Secret Manager
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            Dictionary containing secret data or None
        """
        try:
            version_path = self._get_secret_version_path(secret_name)
            response = self.client.access_secret_version(request={"name": version_path})
            
            # Decode the secret payload
            payload = response.payload.data.decode("UTF-8")
            secret_data = json.loads(payload)
            
            log.info(f"Successfully retrieved secret: {secret_name}")
            return secret_data
            
        except exceptions.NotFound:
            log.warning(f"Secret not found: {secret_name}")
            return None
        except exceptions.PermissionDenied:
            log.error(f"Permission denied accessing secret: {secret_name}")
            raise
        except Exception as e:
            log.error(f"Error retrieving secret {secret_name}: {e}")
            raise
    
    async def create_or_update_secret(
        self, 
        secret_name: str, 
        secret_data: Dict[str, Any]
    ) -> bool:
        """
        Create or update secret in GCP Secret Manager
        
        Args:
            secret_name: Name of the secret
            secret_data: Dictionary containing secret data
            
        Returns:
            True if successful
        """
        try:
            secret_path = self._get_secret_path(secret_name)
            payload = json.dumps(secret_data).encode("UTF-8")
            
            # Try to access the secret to see if it exists
            try:
                self.client.get_secret(request={"name": secret_path})
                secret_exists = True
            except exceptions.NotFound:
                secret_exists = False
            
            if not secret_exists:
                # Create the secret
                parent = f"projects/{self.project_id}"
                self.client.create_secret(
                    request={
                        "parent": parent,
                        "secret_id": secret_name,
                        "secret": {
                            "replication": {
                                "automatic": {}
                            }
                        }
                    }
                )
                log.info(f"Created new secret: {secret_name}")
            
            # Add a new version with the secret data
            self.client.add_secret_version(
                request={
                    "parent": secret_path,
                    "payload": {"data": payload}
                }
            )
            
            log.info(f"Successfully stored secret: {secret_name}")
            return True
            
        except Exception as e:
            log.error(f"Failed to store secret {secret_name}: {e}")
            raise
    
    async def delete_secret(self, secret_name: str) -> bool:
        """
        Delete secret from GCP Secret Manager
        
        Args:
            secret_name: Name of the secret
            
        Returns:
            True if successful
        """
        try:
            secret_path = self._get_secret_path(secret_name)
            self.client.delete_secret(request={"name": secret_path})
            
            log.info(f"Successfully deleted secret: {secret_name}")
            return True
            
        except exceptions.NotFound:
            log.warning(f"Secret not found for deletion: {secret_name}")
            return False
        except Exception as e:
            log.error(f"Failed to delete secret {secret_name}: {e}")
            raise
    
    async def get_email_credentials(self, provider: str = "gmail") -> Dict[str, Any]:
        """
        Get email credentials from GCP Secret Manager
        
        Args:
            provider: Email provider name (gmail, outlook, etc.)
            
        Returns:
            Dictionary containing credentials
        """
        secret_name = f"emailmcp-{provider}-credentials"
        return await self.get_secret(secret_name)
    
    async def get_user_credentials(self, user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user-specific Gmail credentials
        
        Args:
            user_id: User identifier
            
        Returns:
            Dictionary containing user credentials or None
        """
        secret_name = f"emailmcp-user-{user_id}-gmail"
        return await self.get_secret(secret_name)
    
    async def store_user_credentials(
        self, 
        user_id: str, 
        credentials: Dict[str, Any]
    ) -> bool:
        """
        Store user-specific Gmail credentials
        
        Args:
            user_id: User identifier
            credentials: User credentials dictionary
            
        Returns:
            True if successful
        """
        secret_name = f"emailmcp-user-{user_id}-gmail"
        return await self.create_or_update_secret(secret_name, credentials)
    
    async def delete_user_credentials(self, user_id: str) -> bool:
        """
        Delete user-specific Gmail credentials
        
        Args:
            user_id: User identifier
            
        Returns:
            True if successful
        """
        secret_name = f"emailmcp-user-{user_id}-gmail"
        return await self.delete_secret(secret_name)
    
    def is_configured(self) -> bool:
        """Check if GCP Secret Manager is properly configured"""
        return bool(self.project_id)
