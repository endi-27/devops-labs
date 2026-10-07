from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.products_client import ProductsClient
from src.clients.users_client import UsersClient
from src.core.exceptions import BusinessRuleException, EntityNotFoundException
from src.models import OrderStatus
from src.repository import OrderRepository
from src.schemas import OrderCreate, OrderUpdate
from src.service import OrderService


@pytest.fixture
def mock_users_client() -> UsersClient:
    client = UsersClient()
    client.get_user_by_id = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 1,
            "email": "buyer@example.com",
            "username": "buyer",
            "full_name": "Buyer One",
            "is_active": True,
        }
    )
    return client


@pytest.fixture
def mock_products_client() -> ProductsClient:
    client = ProductsClient()
    client.get_product_by_id = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 1,
            "name": "Cloud Handbook",
            "sku": "SKU-CLOUD",
            "price": "50.00",
            "stock_quantity": 10,
            "is_available": True,
        }
    )
    client.reserve_stock = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 1,
            "name": "Cloud Handbook",
            "sku": "SKU-CLOUD",
            "price": "50.00",
            "stock_quantity": 7,
            "is_available": True,
        }
    )
    client.release_stock = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 1,
            "name": "Cloud Handbook",
            "sku": "SKU-CLOUD",
            "price": "50.00",
            "stock_quantity": 10,
            "is_available": True,
        }
    )
    return client


@pytest.mark.asyncio
async def test_create_order_success(
    db_session: AsyncSession,
    mock_users_client: UsersClient,
    mock_products_client: ProductsClient,
) -> None:
    order_repo = OrderRepository(db_session)
    service = OrderService(order_repo, mock_users_client, mock_products_client)

    payload = OrderCreate(
        user_id=1,
        product_id=1,
        quantity=3,
        delivery_address="Kyiv, Polytech St, 10",
    )
    order = await service.create_order(payload)

    assert order.id is not None
    assert order.total_price == Decimal("150.00")
    assert order.status == OrderStatus.PENDING
    mock_products_client.reserve_stock.assert_awaited_once_with(1, 3)  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_create_order_inactive_user_raises(
    db_session: AsyncSession,
    mock_users_client: UsersClient,
    mock_products_client: ProductsClient,
) -> None:
    mock_users_client.get_user_by_id = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 2,
            "email": "inactive@example.com",
            "username": "inactive",
            "full_name": "Inactive User",
            "is_active": False,
        }
    )
    order_repo = OrderRepository(db_session)
    service = OrderService(order_repo, mock_users_client, mock_products_client)

    payload = OrderCreate(
        user_id=2,
        product_id=1,
        quantity=1,
        delivery_address="Lviv, Franko St, 1",
    )
    with pytest.raises(BusinessRuleException, match="inactive user"):
        await service.create_order(payload)


@pytest.mark.asyncio
async def test_update_order_status_and_delete(
    db_session: AsyncSession,
    mock_users_client: UsersClient,
    mock_products_client: ProductsClient,
) -> None:
    order_repo = OrderRepository(db_session)
    service = OrderService(order_repo, mock_users_client, mock_products_client)

    order = await service.create_order(
        OrderCreate(
            user_id=1,
            product_id=1,
            quantity=2,
            delivery_address="Odesa, Deribasivska St, 5",
        )
    )

    updated = await service.update_order(order.id, OrderUpdate(status=OrderStatus.PAID))
    assert updated.status == OrderStatus.PAID

    await service.delete_order(order.id)
    mock_products_client.release_stock.assert_awaited_once_with(1, 2)  # type: ignore[attr-defined]

    with pytest.raises(EntityNotFoundException):
        await service.get_raw_order(order.id)
