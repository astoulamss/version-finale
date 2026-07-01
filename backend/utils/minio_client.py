import os
import boto3
from botocore.client import Config

def get_minio_client():
    """
    Get MinIO S3 client instance.
    Falls back to localhost:9000 if minio:9000 is unreachable (e.g. running test scripts locally).
    """
    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")

    # If endpoint is custom, check connectivity or use fallback
    if endpoint == "minio:9000":
        # Check if we are running in docker or not.
        # A simple check: if we cannot resolve 'minio', we use localhost.
        import socket
        try:
            socket.gethostbyname("minio")
            url = f"http://{endpoint}"
        except socket.gaierror:
            url = "http://localhost:9000"
    else:
        url = f"http://{endpoint}"

    return boto3.client(
        's3',
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1'
    )

def ensure_bucket_exists(s3_client, bucket_name):
    """Ensure the target bucket exists, creating it if it doesn't."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
    except Exception:
        s3_client.create_bucket(Bucket=bucket_name)

def upload_to_minio(filename: str, file_data: bytes) -> str:
    """Upload PDF bytes to MinIO and return the storage key (bucket/filename)."""
    return upload_raw_to_minio(filename, file_data, 'application/pdf')

def upload_raw_to_minio(filename: str, file_data: bytes, content_type: str = 'application/octet-stream') -> str:
    """Upload raw bytes to MinIO and return the storage key (bucket/filename)."""
    s3 = get_minio_client()
    bucket_name = os.getenv("MINIO_BUCKET_NAME", "document")
    ensure_bucket_exists(s3, bucket_name)
    
    s3.put_object(
        Bucket=bucket_name,
        Key=filename,
        Body=file_data,
        ContentType=content_type
    )
    return f"{bucket_name}/{filename}"

def download_from_minio(file_url: str) -> bytes:
    """Download file bytes from MinIO using the storage key."""
    s3 = get_minio_client()
    parts = file_url.split('/', 1)
    if len(parts) == 2:
        bucket_name, key = parts
    else:
        bucket_name = os.getenv("MINIO_BUCKET_NAME", "document")
        key = file_url
        
    response = s3.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read()
