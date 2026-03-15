import os
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Redis Configuration
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # AWS Configuration
    AWS_ACCESS_KEY_ID: str = os.getenv("AWS_ACCESS_KEY_ID", "")
    AWS_SECRET_ACCESS_KEY: str = os.getenv("AWS_SECRET_ACCESS_KEY", "")
    AWS_REGION: str = os.getenv("AWS_REGION", "us-east-1")
    S3_BUCKET_NAME: str = os.getenv("S3_BUCKET_NAME", "autoedge-models")
    
    # Webhook Configuration (The Go API)
    WEBHOOK_URL: str = os.getenv("WEBHOOK_URL", "http://go-api:8080/internal/webhooks/conversion-complete")
    WEBHOOK_SECRET: str = os.getenv("WEBHOOK_SECRET", "change-me-in-prod")

    # Worker Settings
    WORKER_CONCURRENCY: int = int(os.getenv("WORKER_CONCURRENCY", "1"))

settings = Settings()
