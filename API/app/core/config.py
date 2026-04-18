from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"
ENV_LOCAL_FILE = ROOT_DIR / ".env.local"


class Settings(BaseSettings):
    project_name: str = "API Contratos"
    project_version: str = "0.1.0"
    api_v1_prefix: str = "/api/v1"

    db_host: str = Field(alias="DB_HOST")
    db_port: int = Field(alias="DB_PORT")
    db_user: str = Field(alias="DB_USER")
    db_password: str = Field(alias="DB_PASSWORD")
    db_name: str = Field(alias="DB_NAME")
    jwt_secret_key: str = Field(alias="JWT_SECRET_KEY")
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(default=60, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    jwt_refresh_token_expire_minutes: int = Field(default=10080, alias="JWT_REFRESH_TOKEN_EXPIRE_MINUTES")
    api_key_header_name: str = Field(default="X-API-Key", alias="API_KEY_HEADER_NAME")
    cepaberto_token: str | None = Field(default=None, alias="CEPABERTO_TOKEN")
    quepasa_apiwpp_url: str = Field(default="https://apiwpp.vstec.net", alias="QUEPASA_APIWPP_URL")
    quepasa_middleware_url: str = Field(default="http://middleware.vstec.net", alias="QUEPASA_MIDDLEWARE_URL")
    quepasa_user: str | None = Field(default=None, alias="QUEPASA_USER")
    quepasa_token: str = Field(default="CONTRATOS", alias="QUEPASA_TOKEN")
    quepasa_health_password: str = Field(alias="QUEPASA_HEALTH_PASSWORD")
    quepasa_timeout_seconds: float = Field(default=15.0, alias="QUEPASA_TIMEOUT_SECONDS")
    secret_encryption_key: str | None = Field(default=None, alias="SECRET_ENCRYPTION_KEY")
    public_api_base_url: str | None = Field(default=None, alias="PUBLIC_API_BASE_URL")
    cors_allow_origins_raw: str = Field(
        default="http://127.0.0.1:5174,http://localhost:5174,http://127.0.0.1:5173,http://localhost:5173",
        alias="CORS_ALLOW_ORIGINS",
    )
    cors_allow_origin_regex: str = Field(
        default=r"https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        alias="CORS_ALLOW_ORIGIN_REGEX",
    )

    model_config = SettingsConfigDict(
        env_file=tuple(str(path) for path in (ENV_FILE, ENV_LOCAL_FILE) if path.exists()),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def sqlalchemy_sync_database_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/{self.db_name}"
        )

    @property
    def admin_database_uri(self) -> str:
        return (
            f"postgresql+psycopg2://{self.db_user}:{self.db_password}"
            f"@{self.db_host}:{self.db_port}/postgres"
        )

    @property
    def cors_allow_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_allow_origins_raw.split(",") if origin.strip()]

    @property
    def cors_origin_regex(self) -> str | None:
        value = self.cors_allow_origin_regex.strip()
        return value or None


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
