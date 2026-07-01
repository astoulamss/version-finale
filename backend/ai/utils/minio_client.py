import os
import re
from pathlib import Path

S3_CLIENT = None
BUCKET_NAME = None


def _get_client():
    global S3_CLIENT
    if S3_CLIENT is not None:
        return S3_CLIENT
    import boto3
    from botocore.client import Config
    import socket

    endpoint = os.getenv("MINIO_ENDPOINT", "minio:9000")
    access_key = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
    secret_key = os.getenv("MINIO_SECRET_KEY", "minioadminpassword")

    if endpoint == "minio:9000":
        try:
            socket.gethostbyname("minio")
            url = f"http://{endpoint}"
        except socket.gaierror:
            url = "http://localhost:9000"
    else:
        url = f"http://{endpoint}"

    S3_CLIENT = boto3.client(
        's3',
        endpoint_url=url,
        aws_access_key_id=access_key,
        aws_secret_access_key=secret_key,
        config=Config(signature_version='s3v4'),
        region_name='us-east-1',
    )
    return S3_CLIENT


def _get_bucket():
    global BUCKET_NAME
    if BUCKET_NAME is None:
        BUCKET_NAME = os.getenv("MINIO_BUCKET_NAME", "document")
    return BUCKET_NAME


def _ensure_bucket():
    s3 = _get_client()
    bucket = _get_bucket()
    try:
        s3.head_bucket(Bucket=bucket)
    except Exception:
        s3.create_bucket(Bucket=bucket)


def _sanitize_filename(title: str, extension: str = ".pdf") -> str:
    safe = re.sub(r'[^\w\s-]', '', title).strip().lower()
    safe = re.sub(r'[-\s]+', '-', safe)
    if not safe:
        safe = "document"
    return f"{safe}{extension}"


def upload_pdf(pdf_bytes: bytes, title: str) -> str:
    s3 = _get_client()
    bucket = _get_bucket()
    _ensure_bucket()
    filename = _sanitize_filename(title)
    s3.put_object(
        Bucket=bucket,
        Key=filename,
        Body=pdf_bytes,
        ContentType='application/pdf',
    )
    return f"{bucket}/{filename}"


def download_pdf(file_url: str) -> bytes:
    s3 = _get_client()
    parts = file_url.split('/', 1)
    if len(parts) == 2:
        bucket_name, key = parts
    else:
        bucket_name = _get_bucket()
        key = file_url
    response = s3.get_object(Bucket=bucket_name, Key=key)
    return response['Body'].read()
