from typing import Any

import httpx
from loguru import logger

from src.core.config import settings
from src.core.exceptions import EntityNotFoundException, ServiceUnavailableException


class UsersClient:
    """HTTP-клієнт для взаємодії з мікросервісом користувачів."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or settings.services.users_url).rstrip("/")
        self.timeout = timeout or settings.services.timeout

    async def get_user_by_id(self, user_id: int) -> dict[str, Any]:
        """Отримання даних користувача за ID."""
        url = f"{self.base_url}/api/v1/users/{user_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
        except httpx.RequestError as exc:
            logger.error(f"Error connecting to users-service at {url}: {exc}")
            raise ServiceUnavailableException("users-service", str(exc)) from exc

        if response.status_code == 404:
            raise EntityNotFoundException("User", user_id)
        if response.is_error:
            logger.error(f"users-service returned error {response.status_code}: {response.text}")
            raise ServiceUnavailableException("users-service", f"Status {response.status_code}")

        data: dict[str, Any] = response.json()
        return data
