import sys
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseModel):
    user: Annotated[str, Field(description="PostgreSQL username")] = "devops_user"
    password: Annotated[str, Field(description="PostgreSQL password")] = "devops_secret_password"
    name: Annotated[str, Field(description="Database name")] = "devops_db"
    host: Annotated[str, Field(description="PostgreSQL host")] = "127.0.0.1"
    port: Annotated[int, Field(description="PostgreSQL port")] = 5432
    echo: Annotated[bool, Field(description="SQLAlchemy echo SQL queries")] = False

    pool_size: Annotated[int, Field(description="Connection pool size", ge=1, le=100)] = 10
    max_overflow: Annotated[int, Field(description="Max pool overflow connections", ge=0, le=100)] = 10
    pool_timeout: Annotated[
        float,
        Field(description="Seconds to wait before timing out on getting connection", ge=1.0),
    ] = 30.0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        return f"postgresql+asyncpg://{self.user}:{self.password}@{self.host}:{self.port}/{self.name}"


class RedisSettings(BaseModel):
    host: Annotated[str, Field(description="Redis host")] = "127.0.0.1"
    port: Annotated[int, Field(description="Redis port")] = 6379
    password: Annotated[str | None, Field(description="Redis password")] = "devops_redis_password"
    db: Annotated[int, Field(description="Redis DB index", ge=0, le=15)] = 0

    @computed_field  # type: ignore[prop-decorator]
    @property
    def url(self) -> str:
        if self.password:
            return f"redis://:{self.password}@{self.host}:{self.port}/{self.db}"
        return f"redis://{self.host}:{self.port}/{self.db}"


class AuthSettings(BaseModel):
    access_secret_key: Annotated[str, Field(description="JWT signing secret key", min_length=32)] = (
        "super-secret-jwt-signing-key-minimum-32-characters-devops-platform"
    )
    algorithm: Annotated[str, Field(description="JWT algorithm")] = "HS256"
    access_token_expire_minutes: Annotated[int, Field(description="Access token TTL in minutes", ge=1)] = 60


class ApiSettings(BaseModel):
    v1_prefix: Annotated[str, Field(description="API v1 URL prefix")] = "/api/v1"
    cors_origins: Annotated[list[str], Field(description="Allowed CORS origins")] = [
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://localhost:8000",
    ]


class LogSettings(BaseModel):
    dir: Annotated[Path, Field(description="Logs root directory")] = Path("logs")
    app_file: Annotated[str, Field(description="FastAPI app log file name")] = "app.log"
    level: Annotated[str, Field(description="Loguru logging level")] = "INFO"
    rotation: Annotated[str, Field(description="File rotation size")] = "50 MB"
    retention: Annotated[str, Field(description="Log retention duration")] = "30 days"

    @property
    def app_log_path(self) -> Path:
        return self.dir / self.app_file


class StorageSettings(BaseModel):
    dir: Annotated[Path, Field(description="Storage root directory")] = Path("storage")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        extra="ignore",
    )

    environment: Annotated[str, Field(description="Application environment: local, test, production")] = "local"
    debug: Annotated[bool, Field(description="Debug mode")] = True

    db: DbSettings = DbSettings()
    redis: RedisSettings = RedisSettings()
    auth: AuthSettings = AuthSettings()
    api: ApiSettings = ApiSettings()
    log: LogSettings = LogSettings()
    storage: StorageSettings = StorageSettings()

    @property
    def is_testing(self) -> bool:
        """Визначає, чи додаток виконується в тестовому середовищі."""
        return self.environment == "test" or "pytest" in sys.modules


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
