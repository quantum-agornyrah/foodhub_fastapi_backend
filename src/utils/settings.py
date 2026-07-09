import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore"
    )

    DB_CONNECTION: str
    SECRET_KEY: str
    ALGORITHM: str
    EXPIRY_TIME: int
    FRONTEND_LINK: str
    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    ENVIRONMENT: str

    # Redis connection string
    REDIS_URL: str = "redis://localhost:6379/0"

    # S3 upload parameters for menu images
    S3_ENDPOINT_URL: str = os.getenv("S3_ENDPOINT_URL", "")
    S3_ACCESS_KEY: str = os.getenv("S3_ACCESS_KEY", "")
    S3_SECRET_KEY: str = os.getenv("S3_SECRET_KEY", "")
    S3_REGION: str = os.getenv("S3_REGION", "us-east-1")
    S3_BUCKET: str = os.getenv("S3_BUCKET", "foodhub-uploads")

settings = Settings()
