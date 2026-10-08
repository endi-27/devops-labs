import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import DuplicateEntityException, EntityNotFoundException
from src.repository import UserRepository
from src.schemas import UserCreate, UserUpdate
from src.service import UserService


@pytest.mark.asyncio
async def test_create_user_success(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    service = UserService(repo)

    payload = UserCreate(
        email="john@example.com",
        username="johndoe",
        full_name="John Doe",
    )
    user = await service.create_user(payload)

    assert user.id is not None
    assert user.email == "john@example.com"
    assert user.username == "johndoe"
    assert user.full_name == "John Doe"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_create_duplicate_user_raises(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    service = UserService(repo)

    payload = UserCreate(
        email="alice@example.com",
        username="alice",
        full_name="Alice Wonder",
    )
    await service.create_user(payload)

    with pytest.raises(DuplicateEntityException):
        await service.create_user(
            UserCreate(
                email="alice@example.com",
                username="alice_new",
                full_name="Alice Two",
            )
        )

    with pytest.raises(DuplicateEntityException):
        await service.create_user(
            UserCreate(
                email="alice_other@example.com",
                username="alice",
                full_name="Alice Three",
            )
        )


@pytest.mark.asyncio
async def test_get_nonexistent_user_raises(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    service = UserService(repo)

    with pytest.raises(EntityNotFoundException):
        await service.get_user_by_id(99999)


@pytest.mark.asyncio
async def test_update_and_delete_user(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)
    service = UserService(repo)

    user = await service.create_user(UserCreate(email="bob@example.com", username="bobby", full_name="Bob Smith"))

    updated = await service.update_user(user.id, UserUpdate(full_name="Robert Smith"))
    assert updated.full_name == "Robert Smith"

    await service.delete_user(user.id)

    with pytest.raises(EntityNotFoundException):
        await service.get_user_by_id(user.id)
