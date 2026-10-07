from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from loguru import logger


class AppException(Exception):
    def __init__(self, message: str, status_code: int = status.HTTP_400_BAD_REQUEST, details: Any = None) -> None:
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details


class EntityNotFoundException(AppException):
    def __init__(self, entity_name: str, entity_id: Any) -> None:
        super().__init__(
            message=f"{entity_name} with id={entity_id} not found",
            status_code=status.HTTP_404_NOT_FOUND,
        )


class DuplicateEntityException(AppException):
    def __init__(self, field_name: str, value: Any) -> None:
        super().__init__(
            message=f"Entity with {field_name}='{value}' already exists",
            status_code=status.HTTP_409_CONFLICT,
        )


UNPROCESSABLE_STATUS = getattr(status, "HTTP_422_UNPROCESSABLE_CONTENT", 422)


class BusinessRuleException(AppException):
    def __init__(self, message: str) -> None:
        super().__init__(
            message=message,
            status_code=UNPROCESSABLE_STATUS,
        )


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
        logger.warning(f"Application exception on {request.method} {request.url.path}: {exc.message}")
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": True,
                "message": exc.message,
                "details": exc.details,
            },
        )
