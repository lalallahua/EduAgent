from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str

    minio_endpoint: str = "127.0.0.1:9000"
    minio_root_user: str
    minio_root_password: str
    minio_bucket: str = "eduagent"
    minio_secure: bool = False

    material_max_bytes: int = 52_428_800

    chunk_max_chars: int = 1200
    chunk_overlap_chars: int = 200

    embedding_provider: str = "dev_hash"
    embedding_dimension: int = 1024
    embedding_batch_size: int = 20

    embedding_base_url: str = ""
    embedding_api_key: str = ""
    embedding_model: str = ""

    # Redis / ARQ background jobs
    redis_host: str = "127.0.0.1"
    redis_port: int = 6379
    redis_db: int = 0

    knowledge_queue_name: str = "arq:knowledge"
    knowledge_job_timeout_seconds: int = 600
    knowledge_job_max_tries: int = 3
    knowledge_worker_max_jobs: int = 1

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
