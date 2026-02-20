import os
import logging
import boto3
from api.config import settings
from typing import Optional

class StorageService:
    def __init__(self):
        self.provider = settings.STORAGE_PROVIDER.upper()
        self.bucket = settings.STORAGE_BUCKET
        self.s3_client = None
        
        # Determine credentials
        access_key = settings.STORAGE_ACCESS_KEY or settings.AWS_ACCESS_KEY_ID
        secret_key = settings.STORAGE_SECRET_KEY or settings.AWS_SECRET_ACCESS_KEY
        
        if self.provider == "LOCAL":
            logging.info("[StorageService] Initialized in LOCAL mode.")
            return

        # Initialize S3 client for OCI/Cloud regardless of primary provider
        # This allows background migration even if primary is LOCAL
        if self.provider != "LOCAL" or (settings.STORAGE_ENDPOINT and settings.STORAGE_BUCKET):
            try:
                from botocore import UNSIGNED
                from botocore.config import Config
                
                # Most providers (OCI, GCP, MinIO, NAS) are S3-compatible
                client_kwargs = {
                    'service_name': 's3',
                    'region_name': settings.STORAGE_REGION or settings.AWS_REGION
                }
                
                # Use credentials if provided, otherwise prepare for UNSIGNED access
                if access_key and secret_key:
                    client_kwargs['aws_access_key_id'] = access_key
                    client_kwargs['aws_secret_access_key'] = secret_key
                else:
                    logging.warning(f"[StorageService] No access keys provided. Attempting unsigned access.")
                    client_kwargs['config'] = Config(signature_version=UNSIGNED)
                
                # Handle Custom Endpoints (OCI, NAS, GCP Interoperability)
                endpoint = settings.STORAGE_ENDPOINT
                if endpoint:
                    client_kwargs['endpoint_url'] = endpoint
                    logging.info(f"[StorageService] Using custom endpoint: {endpoint}")

                self.s3_client = boto3.client(**client_kwargs)
                logging.info(f"[StorageService] Cloud client initialized (Bucket: {self.bucket})")
                
            except Exception as e:
                logging.error(f"[StorageService] Failed to initialize cloud client: {e}")

    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to the configured provider. 
        Returns the object key (Cloud) or absolute file path (Local).
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        if self.provider != "LOCAL" and self.s3_client:
            return self.upload_to_cloud(file_path, object_name)
        else:
            # Local storage fallback
            return os.path.abspath(file_path)

    def upload_to_cloud(self, file_path: str, object_name: Optional[str] = None) -> Optional[str]:
        """Forces an upload to the cloud provider, regardless of self.provider setting."""
        if not self.s3_client:
            logging.error("[StorageService] Cannot upload to cloud: s3_client not initialized.")
            return None
            
        if object_name is None:
            object_name = os.path.basename(file_path)
            
        try:
            self.s3_client.upload_file(file_path, self.bucket, object_name)
            logging.info(f"[StorageService] Force-uploaded {file_path} to {self.bucket}/{object_name}")
            return object_name
        except Exception as e:
            logging.error(f"[StorageService] Cloud upload failed: {e}")
            return None

    def get_public_url(self, object_key_or_path: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL (Cloud) or returns a local static URL path.
        """
        if self.provider != "LOCAL" and self.s3_client and not object_key_or_path.startswith("/"):
            try:
                # OCI and standard S3 use the same presigned URL logic
                response = self.s3_client.generate_presigned_url(
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
            return f"{settings.PRODUCTION_DOMAIN}/static/outputs/{filename}"

base_storage_service = StorageService()
