from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    # Application
    app_name: str = "HoistScout"
    environment: str = "development"
    debug: bool = True
    log_level: str = "INFO"
    
    # Database
    database_url: str
    redis_url: str
    
    # Security
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # MinIO
    minio_endpoint: str
    minio_access_key: str
    minio_secret_key: str
    minio_bucket_name: str = "hoistscout-documents"
    minio_secure: bool = False
    
    # Ollama
    ollama_base_url: str = "http://localhost:11434"
    ollama_model: str = "llama3.1"
    
    # Anti-detection
    flaresolverr_url: str = "http://localhost:8191"
    captcha_api_key: Optional[str] = None
    
    # Monitoring
    sentry_dsn: Optional[str] = None
    prometheus_port: int = 9090
    
    # Scraping
    max_concurrent_scrapers: int = 10
    scraper_timeout: int = 300  # 5 minutes
    max_retries: int = 3
    retry_delay: int = 60  # seconds
    
    # PDF Processing
    max_pdf_size_mb: int = 100
    pdf_processing_timeout: int = 600  # 10 minutes
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )


@lru_cache()
def get_settings() -> Settings:
    return Settings()