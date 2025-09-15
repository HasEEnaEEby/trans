from pydantic_settings import BaseSettings
from pydantic import BaseModel
from typing import Optional


class Settings(BaseSettings):
    app_env: str = "dev"
    use_mock_mode: bool = True

    # Limits & privacy
    max_upload_mb: int = 10
    data_retention_hours: int = 24

    # Batching & caching
    max_batch_size: int = 8
    batch_timeout_ms: int = 10
    cache_ttl_seconds: int = 3600

    # Rate limiting
    rate_limit_rpm: int = 60

    # Auth
    jwt_secret: str = "change-me"
    jwt_issuer: str = "magazine.ai"
    jwt_audience: str = "magazine-users"
    jwt_algorithm: str = "HS256"

    # External
    redis_url: Optional[str] = None

    # Models
    translation_model: str = "Helsinki-NLP/opus-mt-ja-en"
    intent_model: str = "cl-tohoku/bert-base-japanese"
    ner_model: str = "cl-tohoku/bert-base-japanese"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()


class VersionInfo(BaseModel):
    app_version: str = "0.1.0"
    translation_model: str = settings.translation_model
    intent_model: str = settings.intent_model
    ner_model: str = settings.ner_model
