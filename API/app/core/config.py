from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


ROOT_DIR = Path(__file__).resolve().parents[2]
ENV_FILE = ROOT_DIR / ".env"


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

    model_config = SettingsConfigDict(env_file=str(ENV_FILE), env_file_encoding="utf-8", extra="ignore")

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


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
