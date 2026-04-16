import os
import boto3
from botocore.exceptions import NoCredentialsError
from typing import Optional

class StorageService:
    def __init__(self):
        self.s3_client = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        self.bucket_name = os.getenv('AWS_STORAGE_BUCKET_NAME')

    async def upload_asset(self, local_path: str, remote_name: str) -> Optional[str]:
        """Uploads a local file to S3 and returns the URL."""
        if not self.bucket_name:
            print("[StorageService] WARNING: No bucket name provided, skipping upload.")
            return f"local://{local_path}"
            
        try:
            self.s3_client.upload_file(local_path, self.bucket_name, remote_name)
            url = f"https://{self.bucket_name}.s3.amazonaws.com/{remote_name}"
            return url
        except NoCredentialsError:
            print("[StorageService] ERROR: AWS credentials not found.")
            return None
        except Exception as e:
            print(f"[StorageService] ERROR: {e}")
            return None

    async def download_asset(self, remote_name: str, local_path: str) -> bool:
        """Downloads an asset from S3 to a local path."""
        try:
            self.s3_client.download_file(self.bucket_name, remote_name, local_path)
            return True
        except Exception as e:
            print(f"[StorageService] ERROR: {e}")
            return False

storage_service = StorageService()
