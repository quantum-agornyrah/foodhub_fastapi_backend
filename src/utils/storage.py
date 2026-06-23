import boto3
from src.utils.settings import settings

_s3_client = None

def get_s3_client():
    global _s3_client
    if _s3_client is None:
        if not settings.S3_ENDPOINT_URL:
            raise ValueError("S3_ENDPOINT_URL is not configured in settings.")
        _s3_client = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )
    return _s3_client

async def upload_to_s3(file_bytes: bytes, filename: str, content_type: str) -> str:
    client = get_s3_client()
    client.put_object(
        Bucket=settings.S3_BUCKET,
        Key=filename,
        Body=file_bytes,
        ContentType=content_type,
    )
    return f"{settings.S3_ENDPOINT_URL}/{settings.S3_BUCKET}/{filename}"