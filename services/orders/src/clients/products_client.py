from typing import Any

import httpx
from loguru import logger

from src.core.config import settings
from src.core.exceptions import (
    BusinessRuleException,
    EntityNotFoundException,
    ServiceUnavailableException,
)


class ProductsClient:
    """HTTP-клієнт для взаємодії з мікросервісом товарів."""

    def __init__(self, base_url: str | None = None, timeout: float | None = None) -> None:
        self.base_url = (base_url or settings.services.products_url).rstrip("/")
        self.timeout = timeout or settings.services.timeout

    async def get_product_by_id(self, product_id: int) -> dict[str, Any]:
        """Отримання даних товару за ID."""
        url = f"{self.base_url}/api/v1/products/{product_id}"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url)
        except httpx.RequestError as exc:
            logger.error(f"Error connecting to products-service at {url}: {exc}")
            raise ServiceUnavailableException("products-service", str(exc)) from exc

        if response.status_code == 404:
            raise EntityNotFoundException("Product", product_id)
        if response.is_error:
            logger.error(f"products-service returned error {response.status_code}: {response.text}")
            raise ServiceUnavailableException("products-service", f"Status {response.status_code}")

        data: dict[str, Any] = response.json()
        return data

    async def reserve_stock(self, product_id: int, quantity: int) -> dict[str, Any]:
        """Резервування та списання залишку товару для замовлення."""
        url = f"{self.base_url}/api/v1/products/{product_id}/reserve"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json={"quantity": quantity})
        except httpx.RequestError as exc:
            logger.error(f"Error connecting to products-service at {url}: {exc}")
            raise ServiceUnavailableException("products-service", str(exc)) from exc

        if response.status_code == 404:
            raise EntityNotFoundException("Product", product_id)
        if response.status_code == 422:
            body = response.json()
            message = body.get("message") or body.get("detail") or "Insufficient stock or product unavailable"
            raise BusinessRuleException(message)
        if response.is_error:
            raise ServiceUnavailableException("products-service", f"Status {response.status_code}")

        data: dict[str, Any] = response.json()
        return data

    async def release_stock(self, product_id: int, quantity: int) -> dict[str, Any]:
        """Повернення залишку товару на склад."""
        url = f"{self.base_url}/api/v1/products/{product_id}/release"
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json={"quantity": quantity})
        except httpx.RequestError as exc:
            logger.warning(f"Could not release stock on products-service: {exc}")
            return {}

        if response.is_error:
            logger.warning(f"Failed to release stock for product {product_id}: status={response.status_code}")
            return {}

        data: dict[str, Any] = response.json()
        return data
