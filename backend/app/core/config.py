from functools import lru_cache

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = Field(default="Construction Safety AI Backend", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    app_debug: bool = Field(default=False, alias="APP_DEBUG")
    api_v1_prefix: str = Field(default="/api/v1", alias="API_V1_PREFIX")

    postgres_host: str = Field(default="localhost", alias="POSTGRES_HOST")
    postgres_port: int = Field(default=5432, alias="POSTGRES_PORT")
    postgres_db: str = Field(default="construction_safety", alias="POSTGRES_DB")
    postgres_user: str = Field(default="postgres", alias="POSTGRES_USER")
    postgres_password: str = Field(default="postgres", alias="POSTGRES_PASSWORD")
    database_url: str | None = Field(default=None, alias="DATABASE_URL")
    db_schema: str = Field(default="meerkat_pjt", alias="DB_SCHEMA")

    openai_api_key: str | None = Field(default=None, alias="OPENAI_API_KEY")
    law_api_oc: str | None = Field(default=None, alias="LAW_API_OC")
    kosha_api_key: str | None = Field(default=None, alias="DATA_KEY")
    embedding_model: str = Field(default="text-embedding-3-large", alias="EMBEDDING_MODEL")
    vector_dimension: int = Field(default=1536, alias="VECTOR_DIMENSION")
    use_pgvector: bool = Field(default=False, alias="USE_PGVECTOR")
    auth_secret_key: str = Field(default="change-me-in-production", alias="AUTH_SECRET_KEY")
    auth_access_token_expire_minutes: int = Field(default=60 * 12, alias="AUTH_ACCESS_TOKEN_EXPIRE_MINUTES")
    auth_allow_legacy_user_header: bool = Field(default=False, alias="AUTH_ALLOW_LEGACY_USER_HEADER")

    cors_origins: list[str] = Field(
        default=[
            "http://localhost:5173",
            "http://localhost:3000",
            "https://meercat-b.vercel.app",
        ],
        alias="CORS_ORIGINS",
    )

    @field_validator("cors_origins", mode="before")
    @classmethod
    def _split_cors_origins(cls, value):
        if isinstance(value, str):
            return [origin.strip() for origin in value.split(",") if origin.strip()]
        return value

    @property
    def sqlalchemy_database_uri(self) -> str:
        if self.database_url:
            return self.database_url
        return (
            f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
