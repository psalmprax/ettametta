import os
import logging
import shutil
import time
from datetime import datetime, timedelta
from typing import List, Dict
from sqlalchemy.orm import Session
from api.config import settings
from api.utils.database import SessionLocal
from api.utils.models import VideoJobDB, NexusJobDB, ScheduledPostDB
from .service import base_storage_service

class StorageManager:
    def __init__(self, threshold_gb: float = 140.0, output_dir: str = "outputs"):
        self.threshold_gb = threshold_gb
        self.threshold_bytes = threshold_gb * 1024 * 1024 * 1024
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

    def get_output_dir_size(self) -> int:
        """Calculates the total size of the output directory in bytes."""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(self.output_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                # skip if it is symbolic link
                if not os.path.islink(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    async def enforce_threshold(self):
        """Monitors disk usage and migrates files to OCI if over threshold."""
        current_size = self.get_output_dir_size()
        logging.info(f"[StorageManager] Current outputs size: {current_size / (1024**3):.2f} GB / {self.threshold_gb} GB")

        if current_size > self.threshold_bytes:
            logging.info(f"[StorageManager] Threshold exceeded. Starting migration.")
            # Sort files by modification time (oldest first)
            files = []
            for dirpath, _, filenames in os.walk(self.output_dir):
                for f in filenames:
                    fp = os.path.join(dirpath, f)
                    if os.path.isfile(fp):
                        files.append((fp, os.path.getmtime(fp)))
            
            files.sort(key=lambda x: x[1])

            # Migrate until we are at 80% of threshold
            bytes_to_liberate = current_size - (self.threshold_bytes * 0.8)
            bytes_liberated = 0

            db = SessionLocal()
            try:
                for file_path, _ in files:
                    if bytes_liberated >= bytes_to_liberate:
                        break
                    
                    file_size = os.path.getsize(file_path)
                    success = await self._safe_move_to_cloud(file_path, db)
                    if success:
                        bytes_liberated += file_size
                        logging.info(f"[StorageManager] Migrated {file_path}. Liberated {file_size / (1024**2):.2f} MB")
                    else:
                        logging.error(f"[StorageManager] Failed to migrate {file_path}")
            finally:
                db.close()

    async def _safe_move_to_cloud(self, local_path: str, db: Session) -> bool:
        """Moves a single file to OCI and updates DB references."""
        filename = os.path.basename(local_path)
        
        try:
            # 1. Upload to Cloud
            object_key = base_storage_service.upload_to_cloud(local_path, filename)
            
            if not object_key:
                logging.warning(f"[StorageManager] Upload for {filename} failed. Aborting move.")
                return False

            # 2. Update Database References
            # We search in multiple tables where this file might be referenced
            
            # VideoJobDB
            video_jobs = db.query(VideoJobDB).filter(VideoJobDB.output_path == local_path).all()
            for job in video_jobs:
                job.output_path = object_key
            
            # NexusJobDB
            nexus_jobs = db.query(NexusJobDB).filter(NexusJobDB.output_path == local_path).all()
            for n_job in nexus_jobs:
                n_job.output_path = object_key
            
            # ScheduledPostDB
            scheduled_posts = db.query(ScheduledPostDB).filter(ScheduledPostDB.video_path == local_path).all()
            for post in scheduled_posts:
                post.video_path = object_key
            
            db.commit()

            # 4. Verify (In a real scenario, we might want a checksum, but exist check is min)
            # 5. Delete Local
            os.remove(local_path)
            logging.info(f"[StorageManager] Successfully moved {filename} to cloud.")
            return True

        except Exception as e:
            logging.error(f"[StorageManager] Error moving {local_path} to cloud: {e}")
            db.rollback()
            return False

    async def apply_retention_policy(self, days: int = 90):
        """Deletes files from cloud storage that are older than specified days."""
        if base_storage_service.provider == "LOCAL":
            return

        logging.info(f"[StorageManager] Applying retention policy: {days} days")
        cutoff_date = datetime.now() - timedelta(days=days)
        
        try:
            # Note: We need to extend base_storage_service to support listing and deleting
            # For now, we assume base_storage_service has access to s3_client
            client = base_storage_service.s3_client
            bucket = base_storage_service.bucket
            
            paginator = client.get_paginator('list_objects_v2')
            for page in paginator.paginate(Bucket=bucket):
                if 'Contents' in page:
                    for obj in page['Contents']:
                        last_modified = obj['LastModified'].replace(tzinfo=None)
                        if last_modified < cutoff_date:
                            logging.info(f"[StorageManager] Deleting expired cloud object: {obj['Key']}")
                            client.delete_object(Bucket=bucket, Key=obj['Key'])
                            
                            # Optional: Clean up DB references if we want to mark them as 'purged'
                            # This is complex because we don't want to break the UI, just show 'Asset Expired'
                            
        except Exception as e:
            logging.error(f"[StorageManager] Error applying retention policy: {e}")

storage_manager = StorageManager()
