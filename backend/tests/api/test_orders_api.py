import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_orders_crud_api_flow(async_client: AsyncClient) -> None:
    # 1. Prepare User and Product
    res_user = await async_client.post(
        "/api/v1/users",
        json={
            "email": "customer@example.com",
            "username": "customer",
            "full_name": "Customer One",
            "is_active": True,
        },
    )
    assert res_user.status_code == 201
    user_id = res_user.json()["id"]

    res_product = await async_client.post(
        "/api/v1/products",
        json={
            "name": "DevOps Course Voucher",
            "sku": "VOUCHER-01",
            "price": "99.00",
            "stock_quantity": 10,
            "is_available": True,
        },
    )
    assert res_product.status_code == 201
    product_id = res_product.json()["id"]

    # 2. Create Order
    create_payload = {
        "user_id": user_id,
        "product_id": product_id,
        "quantity": 2,
        "delivery_address": "Kyiv, Khreshchatyk 1",
    }
    res_order = await async_client.post("/api/v1/orders", json=create_payload)
    assert res_order.status_code == 201
    order_data = res_order.json()
    order_id = order_data["id"]
    assert order_data["total_price"] == "198.00"
    assert order_data["status"] == "PENDING"

    # 3. Get Order By ID
    res_get = await async_client.get(f"/api/v1/orders/{order_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == order_id
    assert res_get.json()["user"]["username"] == "customer"
    assert res_get.json()["product"]["sku"] == "VOUCHER-01"

    # 4. Get All Orders
    res_list = await async_client.get("/api/v1/orders", params={"user_id": user_id})
    assert res_list.status_code == 200
    assert len(res_list.json()) == 1

    # 5. Update Order (e.g. status)
    update_payload = {"status": "PAID", "delivery_address": "Kyiv, Khreshchatyk 2"}
    res_update = await async_client.put(f"/api/v1/orders/{order_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["status"] == "PAID"
    assert res_update.json()["delivery_address"] == "Kyiv, Khreshchatyk 2"

    # 6. Delete Order
    res_delete = await async_client.delete(f"/api/v1/orders/{order_id}")
    assert res_delete.status_code == 204

    # 7. Verify NotFound
    res_not_found = await async_client.get(f"/api/v1/orders/{order_id}")
    assert res_not_found.status_code == 404
