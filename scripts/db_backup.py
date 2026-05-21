#!/usr/bin/env python3
"""
Database Backup Script
=======================
Dumps PostgreSQL database and uploads to S3-compatible storage.
Designed for cron scheduling or manual execution.

Usage:
    python scripts/db_backup.py [--retention-days 30] [--prefix backups]
"""

import os
import sys
import subprocess
import logging
import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import gzip

try:
    import boto3
    from botocore.exceptions import ClientError
except ImportError:
    print("boto3 is required. Install with: pip install boto3")
    sys.exit(1)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def get_db_config() -> dict:
    """Extract database connection details from DATABASE_URL."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise ValueError("DATABASE_URL environment variable not set")

    if db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "")
    elif db_url.startswith("postgresql+asyncpg://"):
        db_url = db_url.replace("postgresql+asyncpg://", "")

    user_pass, rest = db_url.split("@", 1)
    if ":" in user_pass:
        user, password = user_pass.split(":", 1)
    else:
        user = user_pass
        password = ""

    host_port, dbname = rest.split("/", 1)
    if ":" in host_port:
        host, port = host_port.split(":", 1)
    else:
        host = host_port
        port = "5432"

    return {
        "user": user,
        "password": password,
        "host": host,
        "port": port,
        "dbname": dbname,
    }


def get_s3_client():
    """Create S3 client from storage configuration."""
    storage_provider = os.getenv("STORAGE_PROVIDER", "LOCAL")
    endpoint = os.getenv("STORAGE_ENDPOINT")
    access_key = os.getenv("STORAGE_ACCESS_KEY")
    secret_key = os.getenv("STORAGE_SECRET_KEY")
    region = os.getenv("STORAGE_REGION", "us-east-1")

    if not access_key or not secret_key:
        raise ValueError("STORAGE_ACCESS_KEY and STORAGE_SECRET_KEY must be set")

    session = boto3.Session(
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        region_name=region,
    )

    s3_kwargs = {}
    if endpoint:
        s3_kwargs["endpoint_url"] = endpoint

    return session.client("s3", **s3_kwargs)


def dump_database(db_config: dict, output_path: str) -> bool:
    """Dump PostgreSQL database to file."""
    env = os.environ.copy()
    env["PGPASSWORD"] = db_config["password"]

    cmd = [
        "pg_dump",
        "-h", db_config["host"],
        "-p", db_config["port"],
        "-U", db_config["user"],
        "-F", "c",
        "-b",
        "-v",
        "-f", output_path,
        db_config["dbname"],
    ]

    logger.info(f"Running: {' '.join(cmd[:6])}...")
    try:
        result = subprocess.run(
            cmd,
            env=env,
            capture_output=True,
            text=True,
            timeout=3600,
        )
        if result.returncode == 0:
            size_mb = Path(output_path).stat().st_size / (1024 * 1024)
            logger.info(f"Database dump successful: {size_mb:.2f} MB")
            return True
        else:
            logger.error(f"pg_dump failed: {result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error("Database dump timed out after 1 hour")
        return False
    except FileNotFoundError:
        logger.error("pg_dump not found. Ensure PostgreSQL client is installed.")
        return False


def upload_to_s3(s3_client, bucket: str, file_path: str, key: str) -> bool:
    """Upload file to S3-compatible storage."""
    try:
        s3_client.upload_file(
            file_path,
            bucket,
            key,
            ExtraArgs={"ServerSideEncryption": "AES256"},
        )
        logger.info(f"Uploaded to s3://{bucket}/{key}")
        return True
    except ClientError as e:
        logger.error(f"S3 upload failed: {e}")
        return False


def list_old_backups(s3_client, bucket: str, prefix: str, retention_days: int) -> list:
    """List backups older than retention period."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
    old_backups = []

    try:
        response = s3_client.list_objects_v2(Bucket=bucket, Prefix=prefix)
        for obj in response.get("Contents", []):
            if obj["LastModified"].replace(tzinfo=None) < cutoff:
                old_backups.append(obj["Key"])
    except ClientError as e:
        logger.error(f"Failed to list backups: {e}")

    return old_backups


def delete_old_backups(s3_client, bucket: str, keys: list) -> int:
    """Delete old backups from S3."""
    deleted = 0
    for key in keys:
        try:
            s3_client.delete_object(Bucket=bucket, Key=key)
            logger.info(f"Deleted old backup: {key}")
            deleted += 1
        except ClientError as e:
            logger.error(f"Failed to delete {key}: {e}")
    return deleted


def main():
    parser = argparse.ArgumentParser(description="Database backup to S3")
    parser.add_argument("--retention-days", type=int, default=30, help="Days to retain backups")
    parser.add_argument("--prefix", type=str, default="backups", help="S3 key prefix")
    args = parser.parse_args()

    bucket = os.getenv("STORAGE_BUCKET")
    if not bucket:
        logger.error("STORAGE_BUCKET environment variable not set")
        sys.exit(1)

    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"ettametta_db_{timestamp}.dump"
    compressed_filename = f"{filename}.gz"

    with tempfile.TemporaryDirectory() as tmpdir:
        dump_path = os.path.join(tmpdir, filename)

        logger.info("Starting database backup...")
        db_config = get_db_config()

        if not dump_database(db_config, dump_path):
            logger.error("Backup failed at dump stage")
            sys.exit(1)

        logger.info("Compressing backup...")
        compressed_path = os.path.join(tmpdir, compressed_filename)
        with open(dump_path, "rb") as f_in:
            with gzip.open(compressed_path, "wb") as f_out:
                f_out.writelines(f_in)

        compressed_size = Path(compressed_path).stat().st_size / (1024 * 1024)
        logger.info(f"Compressed size: {compressed_size:.2f} MB")

        logger.info("Uploading to S3...")
        s3_client = get_s3_client()
        s3_key = f"{args.prefix}/{compressed_filename}"

        if not upload_to_s3(s3_client, bucket, compressed_path, s3_key):
            logger.error("Backup failed at upload stage")
            sys.exit(1)

        logger.info("Checking for old backups to clean up...")
        old_backups = list_old_backups(s3_client, bucket, args.prefix, args.retention_days)
        if old_backups:
            deleted = delete_old_backups(s3_client, bucket, old_backups)
            logger.info(f"Deleted {deleted} old backups")

    logger.info("Backup completed successfully!")


if __name__ == "__main__":
    main()
