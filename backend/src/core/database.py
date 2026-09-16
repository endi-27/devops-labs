from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from src.core.config import settings

# For SQLite in tests vs PostgreSQL in dev/prod
is_sqlite = settings.db.url.startswith("sqlite")
connect_args = {} if is_sqlite else {"server_settings": {"timezone": "utc"}}

engine: AsyncEngine = create_async_engine(
    settings.db.url,
    echo=settings.db.echo,
    pool_size=settings.db.pool_size if not is_sqlite else 5,
    max_overflow=settings.db.max_overflow if not is_sqlite else 0,
    pool_timeout=settings.db.pool_timeout,
    pool_pre_ping=True,
    connect_args=connect_args,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Асинхронний генератор сесій для ін'єкції залежностей у Services / Repositories."""
    async with async_session_factory() as session:
        yield session


async def close_db() -> None:
    """Закриття рушія та пулу з'єднань БД при зупинці додатку."""
    await engine.dispose()
