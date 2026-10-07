import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    res = await async_client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "products-service"
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_products_crud_api_flow(async_client: AsyncClient) -> None:
    # 1. Create Product
    create_payload = {
        "name": "Docker & K8s Book",
        "description": "Comprehensive practical guide",
        "sku": "SKU-BOOK-001",
        "price": "39.99",
        "stock_quantity": 25,
        "is_available": True,
    }
    res_create = await async_client.post("/api/v1/products", json=create_payload)
    assert res_create.status_code == 201
    product_data = res_create.json()
    product_id = product_data["id"]
    assert product_data["sku"] == "SKU-BOOK-001"
    assert product_data["stock_quantity"] == 25

    # 2. Get Product By ID
    res_get = await async_client.get(f"/api/v1/products/{product_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == product_id

    # 3. Get All Products
    res_list = await async_client.get("/api/v1/products")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # 4. Reserve Stock
    res_reserve = await async_client.post(f"/api/v1/products/{product_id}/reserve", json={"quantity": 5})
    assert res_reserve.status_code == 200
    assert res_reserve.json()["stock_quantity"] == 20

    # 5. Release Stock
    res_release = await async_client.post(f"/api/v1/products/{product_id}/release", json={"quantity": 2})
    assert res_release.status_code == 200
    assert res_release.json()["stock_quantity"] == 22

    # 6. Update Product
    update_payload = {"price": "45.00"}
    res_update = await async_client.put(f"/api/v1/products/{product_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["price"] == "45.00"

    # 7. Delete Product
    res_delete = await async_client.delete(f"/api/v1/products/{product_id}")
    assert res_delete.status_code == 204

    # 8. Verify NotFound
    res_not_found = await async_client.get(f"/api/v1/products/{product_id}")
    assert res_not_found.status_code == 404
