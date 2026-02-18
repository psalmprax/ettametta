import os
import logging
from api.config import settings
from typing import Optional

class StorageService:
    def __init__(self):
        self.use_s3 = bool(settings.AWS_ACCESS_KEY_ID and settings.AWS_SECRET_ACCESS_KEY and settings.AWS_STORAGE_BUCKET_NAME)
        self.s3_client = None
        
        if self.use_s3:
            try:
                import boto3
                self.s3_client = boto3.client(
                    's3',
                    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                    region_name=settings.AWS_REGION
                )
                logging.info(f"[StorageService] Initialized S3 storage (Bucket: {settings.AWS_STORAGE_BUCKET_NAME})")
            except ImportError:
                logging.error("[StorageService] boto3 not installed, falling back to local storage")
                self.use_s3 = False
            except Exception as e:
                logging.error(f"[StorageService] Failed to initialize S3: {e}")
                self.use_s3 = False
        else:
            logging.info("[StorageService] Initialized Local storage (No AWS credentials provided)")

    def upload_file(self, file_path: str, object_name: Optional[str] = None) -> str:
        """
        Uploads a file to S3 if configured, otherwise returns the local path.
        Returns the object key (S3) or file path (Local).
        """
        if object_name is None:
            object_name = os.path.basename(file_path)

        if self.use_s3 and self.s3_client:
            try:
                self.s3_client.upload_file(file_path, settings.AWS_STORAGE_BUCKET_NAME, object_name)
                logging.info(f"[StorageService] Uploaded {file_path} to s3://{settings.AWS_STORAGE_BUCKET_NAME}/{object_name}")
                return object_name
            except Exception as e:
                logging.error(f"[StorageService] Upload failed: {e}")
                return file_path
        else:
            # Local storage - file is already there, just return path
            return file_path

    def get_public_url(self, object_key_or_path: str, expiration: int = 3600) -> str:
        """
        Generates a presigned URL (S3) or returns a local static URL path.
        """
        if self.use_s3 and self.s3_client and not object_key_or_path.startswith("/"):
             # Assume it's an S3 object key if it doesn't start with /
            try:
                response = self.s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': object_key_or_path},
                                                    ExpiresIn=expiration)
                return response
            except Exception as e:
                logging.error(f"[StorageService] Failed to generate presigned URL: {e}")
                return object_key_or_path
        else:
            # Local fallback: Assuming served via static mount (if configured) or just returning raw path for debug
            # In a real local setup, we'd map this to a /static/ URL.
            # For now, we return the path but might want to fix this for frontend access.
            if os.path.exists(object_key_or_path):
                 # Quick hack for localhost dashboard: if path is inside 'outputs', serve it?
                 # ideally we need Nginx or FastAPI static mount.
                 # Let's assume FastAPI mounts 'outputs' at /static/outputs (common pattern)
                 filename = os.path.basename(object_key_or_path)
                 return f"{settings.PRODUCTION_DOMAIN}/static/outputs/{filename}"
            return object_key_or_path

base_storage_service = StorageService()
