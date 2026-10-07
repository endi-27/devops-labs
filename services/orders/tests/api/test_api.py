from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from src.clients.products_client import ProductsClient
from src.clients.users_client import UsersClient
from src.main import app
from src.router import get_products_client, get_users_client


@pytest.fixture(autouse=True)
def mock_external_clients() -> None:
    users_mock = UsersClient()
    users_mock.get_user_by_id = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 1,
            "email": "customer@example.com",
            "username": "customer",
            "full_name": "Customer One",
            "is_active": True,
        }
    )

    products_mock = ProductsClient()
    products_mock.get_product_by_id = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 2,
            "name": "DevOps Course Voucher",
            "sku": "VOUCHER-01",
            "price": "99.00",
            "stock_quantity": 10,
            "is_available": True,
        }
    )
    products_mock.reserve_stock = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 2,
            "name": "DevOps Course Voucher",
            "sku": "VOUCHER-01",
            "price": "99.00",
            "stock_quantity": 8,
            "is_available": True,
        }
    )
    products_mock.release_stock = AsyncMock(  # type: ignore[method-assign]
        return_value={
            "id": 2,
            "name": "DevOps Course Voucher",
            "sku": "VOUCHER-01",
            "price": "99.00",
            "stock_quantity": 10,
            "is_available": True,
        }
    )

    app.dependency_overrides[get_users_client] = lambda: users_mock
    app.dependency_overrides[get_products_client] = lambda: products_mock


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    res = await async_client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "orders-service"
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_orders_crud_api_flow(async_client: AsyncClient) -> None:
    # 1. Create Order
    create_payload = {
        "user_id": 1,
        "product_id": 2,
        "quantity": 2,
        "delivery_address": "Kyiv, Khreshchatyk 1",
    }
    res_order = await async_client.post("/api/v1/orders", json=create_payload)
    assert res_order.status_code == 201
    order_data = res_order.json()
    order_id = order_data["id"]
    assert order_data["total_price"] == "198.00"
    assert order_data["status"] == "PENDING"
    assert order_data["user"]["username"] == "customer"
    assert order_data["product"]["sku"] == "VOUCHER-01"

    # 2. Get Order By ID
    res_get = await async_client.get(f"/api/v1/orders/{order_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == order_id

    # 3. Get All Orders
    res_list = await async_client.get("/api/v1/orders", params={"user_id": 1})
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 4. Update Order
    update_payload = {"status": "PAID", "delivery_address": "Kyiv, Khreshchatyk 2"}
    res_update = await async_client.put(f"/api/v1/orders/{order_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "PAID"
    assert res_update.json()["delivery_address"] == "Kyiv, Khreshchatyk 2"

    # 5. Delete Order
    res_delete = await async_client.delete(f"/api/v1/orders/{order_id}")
    assert res_delete.status_code == 204

    # 6. Verify NotFound
    res_not_found = await async_client.get(f"/api/v1/orders/{order_id}")
    assert res_not_found.status_code == 404
