from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"

    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/resume_analyzer"
    redis_url: str = "redis://localhost:6379/0"

    vector_db_provider: str = "pgvector"
    qdrant_url: str = "http://localhost:6333"

    model_provider: str = "anthropic"
    model_name: str = "claude-sonnet-5"
    embedding_provider: str = "local"
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    max_file_size_mb: int = 10
    upload_dir: str = "./uploads"

    cors_origins: str = "http://localhost:3000"

    skills_data_dir: Path = REPO_ROOT / "data" / "skills"

    @property
    def cors_origin_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
