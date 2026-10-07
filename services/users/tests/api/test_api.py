import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(async_client: AsyncClient) -> None:
    res = await async_client.get("/health")
    assert res.status_code == 200
    assert res.json()["service"] == "users-service"
    assert res.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_users_crud_api_flow(async_client: AsyncClient) -> None:
    create_payload = {
        "email": "devops_student@example.com",
        "username": "devops_student",
        "full_name": "DevOps Student",
        "is_active": True,
    }
    res_create = await async_client.post("/api/v1/users", json=create_payload)
    assert res_create.status_code == 201
    user_data = res_create.json()
    user_id = user_data["id"]
    assert user_data["email"] == create_payload["email"]
    assert user_data["username"] == create_payload["username"]

    res_get = await async_client.get(f"/api/v1/users/{user_id}")
    assert res_get.status_code == 200
    assert res_get.json()["id"] == user_id

    res_list = await async_client.get("/api/v1/users")
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    update_payload = {"full_name": "Senior DevOps Engineer"}
    res_update = await async_client.put(f"/api/v1/users/{user_id}", json=update_payload)
    assert res_update.status_code == 200
    assert res_update.json()["full_name"] == "Senior DevOps Engineer"

    res_delete = await async_client.delete(f"/api/v1/users/{user_id}")
    assert res_delete.status_code == 204

    res_not_found = await async_client.get(f"/api/v1/users/{user_id}")
    assert res_not_found.status_code == 404
