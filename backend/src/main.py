from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from sqlalchemy import text

from src.core.config import settings
from src.core.database import close_db, engine
from src.core.exceptions import register_exception_handlers
from src.core.logger import setup_logging
from src.modules.orders.router import router as orders_router
from src.modules.products.router import router as products_router
from src.modules.users.router import router as users_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Життєвий цикл додатку: ініціалізація ресурсів при старті та очищення при зупинці."""
    setup_logging()
    logger.info(f"Starting application in '{settings.environment}' environment...")

    # Перевірка з'єднання з базою даних
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Database connection successfully established.")
    except Exception as exc:
        logger.warning(f"Could not connect to database on startup: {exc}")

    yield

    logger.info("Shutting down application and disposing DB engine...")
    await close_db()
    logger.info("Application successfully stopped.")


def create_app() -> FastAPI:
    """Фабрика створення екземпляра додатку FastAPI."""
    app = FastAPI(
        title="DevOps Course Platform API",
        version="0.1.0",
        description="Modular Monolith Backend with FastAPI, PostgreSQL, Redis, and uv",
        lifespan=lifespan,
    )

    # CORS Middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Реєстрація кастомних Exception Handlers
    register_exception_handlers(app)

    # Health Check & Readiness ендпоінти
    @app.get(f"{settings.api.v1_prefix}/health", tags=["Health"], status_code=status.HTTP_200_OK)
    async def health_check() -> dict[str, Any]:
        """Ендпоінт перевірки працездатності сервісу (Liveness Probe)."""
        return {
            "status": "ok",
            "environment": settings.environment,
            "version": "0.1.0",
        }

    @app.get(f"{settings.api.v1_prefix}/ready", tags=["Health"], status_code=status.HTTP_200_OK)
    async def readiness_check() -> dict[str, Any]:
        """Ендпоінт перевірки готовності сервісу (Readiness Probe з перевіркою DB)."""
        db_status = "healthy"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {e}"

        return {
            "status": "ready" if db_status == "healthy" else "degraded",
            "database": db_status,
        }

    # Підключення роутерів модулів
    app.include_router(users_router, prefix=settings.api.v1_prefix)
    app.include_router(products_router, prefix=settings.api.v1_prefix)
    app.include_router(orders_router, prefix=settings.api.v1_prefix)

    return app


app = create_app()
