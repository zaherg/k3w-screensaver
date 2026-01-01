"""Cloudflare R2 uploader (S3 compatible)."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

import boto3
from botocore.config import Config as BotoConfig

from .config import R2Config

LOGGER = logging.getLogger(__name__)


class R2Uploader:
    def __init__(self, config: R2Config) -> None:
        if not config.enabled:
            raise ValueError("R2 uploading is disabled in configuration")
        missing = [
            name
            for name, value in {
                "R2_ACCESS_KEY_ID": config.access_key_id,
                "R2_SECRET_ACCESS_KEY": config.secret_access_key,
                "R2_BUCKET": config.bucket,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(
                f"Missing required R2 credentials/settings: {', '.join(missing)}"
            )
        endpoint_url = config.endpoint_url
        self.bucket = config.bucket
        self.key_prefix = config.key_prefix.strip("/")
        LOGGER.info("Initializing R2 client targeting bucket %s", self.bucket)
        session = boto3.session.Session()
        self.client = session.client(
            "s3",
            endpoint_url=endpoint_url,
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.secret_access_key,
            region_name="auto",
            config=BotoConfig(signature_version="s3v4", retries={"max_attempts": 3}),
        )

    def upload(self, file_path: Path, *, object_key: Optional[str] = None) -> str:
        if object_key is None:
            object_key = file_path.name
        key = (
            f"{self.key_prefix}/{object_key}" if self.key_prefix else object_key
        )
        LOGGER.info("Uploading %s to r2://%s/%s", file_path, self.bucket, key)
        self.client.upload_file(str(file_path), self.bucket, key)
        return key

