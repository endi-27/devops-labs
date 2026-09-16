import pytest
from httpx import AsyncClient


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

    # 4. Update Product
    update_payload = {"price": "45.00", "stock_quantity": 30}
    res_update = await async_client.put(f"/api/v1/products/{product_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["price"] == "45.00"
    assert res_update.json()["stock_quantity"] == 30

    # 5. Delete Product
    res_delete = await async_client.delete(f"/api/v1/products/{product_id}")
    assert res_delete.status_code == 204

    # 6. Verify NotFound
    res_not_found = await async_client.get(f"/api/v1/products/{product_id}")
    assert res_not_found.status_code == 404
