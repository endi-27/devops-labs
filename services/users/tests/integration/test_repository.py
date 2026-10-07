import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import User
from src.repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository_crud(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    user = User(
        email="repo_user@example.com",
        username="repo_user",
        full_name="Repo User",
        is_active=True,
    )
    created = await repo.create(user)
    assert created.id is not None

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.email == "repo_user@example.com"

    by_email = await repo.get_by_email("repo_user@example.com")
    assert by_email is not None

    by_username = await repo.get_by_username("repo_user")
    assert by_username is not None

    all_users = await repo.get_all()
    assert len(all_users) >= 1

    created.full_name = "Updated Repo User"
    updated = await repo.update(created)
    assert updated.full_name == "Updated Repo User"

    await repo.delete(updated)
    assert await repo.get_by_id(created.id) is None
