"""Cloudflare R2 (S3-compatible) storage service for document vault."""

import uuid

from app.config import settings


def _get_s3_client():
    """Create an S3 client configured for Cloudflare R2."""
    import boto3
    from botocore.config import Config
    return boto3.client(
        "s3",
        endpoint_url=f"https://{settings.R2_ACCOUNT_ID}.r2.cloudflarestorage.com",
        aws_access_key_id=settings.R2_ACCESS_KEY,
        aws_secret_access_key=settings.R2_SECRET_KEY,
        config=Config(signature_version="s3v4"),
        region_name="auto",
    )


def upload_file(file_bytes: bytes, filename: str, user_id: uuid.UUID) -> str:
    """Upload a file to R2 and return the file key."""
    file_ext = filename.rsplit(".", 1)[-1] if "." in filename else ""
    file_key = f"documents/{user_id}/{uuid.uuid4()}.{file_ext}" if file_ext else f"documents/{user_id}/{uuid.uuid4()}"

    client = _get_s3_client()
    client.put_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=file_key,
        Body=file_bytes,
    )
    return file_key


def get_presigned_url(file_key: str) -> str:
    """Generate a temporary presigned download URL (1 hour expiry)."""
    client = _get_s3_client()
    url = client.generate_presigned_url(
        "get_object",
        Params={"Bucket": settings.R2_BUCKET_NAME, "Key": file_key},
        ExpiresIn=3600,
    )
    return url


def delete_file(file_key: str) -> None:
    """Delete a file from R2."""
    client = _get_s3_client()
    client.delete_object(
        Bucket=settings.R2_BUCKET_NAME,
        Key=file_key,
    )
