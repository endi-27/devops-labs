import sys
from functools import lru_cache
from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, Field, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class DbSettings(BaseModel):
    user: Annotated[str, Field(description="PostgreSQL username")] = "devops_user"
    password: Annotated[str, Field(description="PostgreSQL password")] = "devops_secret_password"
    name: Annotated[str, Field(description="Database name")] = "orders_db"
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


class ServicesSettings(BaseModel):
    users_url: Annotated[str, Field(description="Users microservice URL")] = "http://127.0.0.1:8001"
    products_url: Annotated[str, Field(description="Products microservice URL")] = "http://127.0.0.1:8002"
    timeout: Annotated[float, Field(description="HTTP request timeout in seconds")] = 5.0


class ApiSettings(BaseModel):
    prefix: Annotated[str, Field(description="API URL prefix")] = "/api/v1/orders"
    port: Annotated[int, Field(description="Service port")] = 8003
    cors_origins: Annotated[list[str], Field(description="Allowed CORS origins")] = ["*"]


class LogSettings(BaseModel):
    dir: Annotated[Path, Field(description="Logs root directory")] = Path("logs")
    app_file: Annotated[str, Field(description="App log file name")] = "orders.log"
    level: Annotated[str, Field(description="Loguru logging level")] = "INFO"
    rotation: Annotated[str, Field(description="File rotation size")] = "50 MB"
    retention: Annotated[str, Field(description="Log retention duration")] = "30 days"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
        extra="ignore",
    )

    environment: Annotated[str, Field(description="Application environment: local, test, production")] = "local"
    debug: Annotated[bool, Field(description="Debug mode")] = True

    db: DbSettings = DbSettings()
    services: ServicesSettings = ServicesSettings()
    api: ApiSettings = ApiSettings()
    log: LogSettings = LogSettings()

    @property
    def is_testing(self) -> bool:
        return self.environment == "test" or "pytest" in sys.modules


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
