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
from src.router import router as products_router


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logging()
    logger.info(f"Starting Products Service in '{settings.environment}' environment...")

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        logger.info("Products Service: Database connection successfully established.")
    except Exception as exc:
        logger.warning(f"Products Service: Could not connect to database on startup: {exc}")

    yield

    logger.info("Shutting down Products Service and disposing DB engine...")
    await close_db()
    logger.info("Products Service: Stopped.")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Products Service API",
        version="0.1.0",
        description="DevOps Platform Products Microservice",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    @app.get("/health", tags=["Health"], status_code=status.HTTP_200_OK)
    @app.get("/api/v1/products/health", tags=["Health"], status_code=status.HTTP_200_OK)
    async def health_check() -> dict[str, Any]:
        return {
            "service": "products-service",
            "status": "ok",
            "environment": settings.environment,
            "version": "0.1.0",
        }

    @app.get("/ready", tags=["Health"], status_code=status.HTTP_200_OK)
    @app.get("/api/v1/products/ready", tags=["Health"], status_code=status.HTTP_200_OK)
    async def readiness_check() -> dict[str, Any]:
        db_status = "healthy"
        try:
            async with engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
        except Exception as e:
            db_status = f"unhealthy: {e}"

        return {
            "service": "products-service",
            "status": "ready" if db_status == "healthy" else "degraded",
            "database": db_status,
        }

    app.include_router(products_router)

    return app


app = create_app()
