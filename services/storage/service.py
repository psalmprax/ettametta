from api.utils.vault import get_secret
from typing import Optional
import os
import logging
import boto3

class StorageService:
    def __init__(self):
        self._s3_client = None
        self._last_keys = None

    @property
    def provider(self):
        return get_secret("storage_provider", "LOCAL").upper()

    @property
    def bucket(self):
        return get_secret("storage_bucket", "")

    @property
    def endpoint(self):
        return get_secret("storage_endpoint")

    @property
    def region(self):
        return get_secret("storage_region", "us-east-1")

    def _get_client(self):
        # Determine credentials
        access_key = get_secret("storage_access_key") or get_secret("aws_access_key_id")
        secret_key = get_secret("storage_secret_key") or get_secret("aws_secret_access_key")
        
        current_keys = (access_key, secret_key, self.endpoint, self.region)
        
        if self._s3_client and self._last_keys == current_keys:
            return self._s3_client

        # Initialize S3 client for OCI/Cloud
        try:
            from botocore import UNSIGNED
            from botocore.config import Config
            
            client_kwargs = {
                'service_name': 's3',
                'region_name': self.region
            }
            
            if access_key and secret_key:
                client_kwargs['aws_access_key_id'] = access_key
                client_kwargs['aws_secret_access_key'] = secret_key
            else:
                logging.warning(f"[StorageService] No access keys provided. Attempting unsigned access.")
                client_kwargs['config'] = Config(signature_version=UNSIGNED)
            
            if self.endpoint:
                client_kwargs['endpoint_url'] = self.endpoint

            self._s3_client = boto3.client(**client_kwargs)
            self._last_keys = current_keys
            logging.info(f"[StorageService] Cloud client (re)initialized")
            return self._s3_client
            
        except Exception as e:
            logging.error(f"[StorageService] Failed to initialize cloud client: {e}")
            return None
        

    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to the configured provider. 
        Returns the object key (Cloud) or absolute file path (Local).
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        s3_client = self._get_client()
        if self.provider != "LOCAL" and s3_client:
            return self.upload_to_cloud(file_path, object_name)
        else:
            # Local storage fallback
            return os.path.abspath(file_path)

    def upload_to_cloud(self, file_path: str, object_name: Optional[str] = None) -> Optional[str]:
        """Forces an upload to the cloud provider, regardless of self.provider setting."""
        s3_client = self._get_client()
        if not s3_client:
            logging.error("[StorageService] Cannot upload to cloud: s3_client not initialized.")
            return None
            
        if object_name is None:
            object_name = os.path.basename(file_path)
            
        try:
            s3_client.upload_file(file_path, self.bucket, object_name)
            logging.info(f"[StorageService] Force-uploaded {file_path} to {self.bucket}/{object_name}")
            return object_name
        except Exception as e:
            logging.error(f"[StorageService] Cloud upload failed: {e}")
            return None

    def get_public_url(self, object_key_or_path: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL (Cloud) or returns a local static URL path.
        """
        s3_client = self._get_client()
        if self.provider != "LOCAL" and s3_client and not object_key_or_path.startswith("/"):
            try:
                # OCI and standard S3 use the same presigned URL logic
                response = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': self.bucket, 'Key': object_key_or_path},
                    ExpiresIn=expiration
                )
                return response
            except Exception as e:
                logging.error(f"[StorageService] Failed to generate presigned URL for {self.provider}: {e}")
                return object_key_or_path
        else:
            # Local fallback logic
            filename = os.path.basename(object_key_or_path)
            from api.config import settings
            return f"{get_secret('production_domain', settings.PRODUCTION_DOMAIN)}/static/outputs/{filename}"

base_storage_service = StorageService()
