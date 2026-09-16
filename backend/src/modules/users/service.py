from collections.abc import Sequence

from loguru import logger

from src.core.exceptions import DuplicateEntityException, EntityNotFoundException
from src.modules.users.models import User
from src.modules.users.repository import UserRepository
from src.modules.users.schemas import UserCreate, UserUpdate


class UserService:
    """Сервісний шар бізнес-логіки користувачів."""

    def __init__(self, repository: UserRepository):
        self.repository = repository

    async def get_user_by_id(self, user_id: int) -> User:
        user = await self.repository.get_by_id(user_id)
        if not user:
            raise EntityNotFoundException("User", user_id)
        return user

    async def get_all_users(self, skip: int = 0, limit: int = 100) -> Sequence[User]:
        return await self.repository.get_all(skip=skip, limit=limit)

    async def create_user(self, payload: UserCreate) -> User:
        if await self.repository.get_by_email(payload.email):
            raise DuplicateEntityException("email", payload.email)
        if await self.repository.get_by_username(payload.username):
            raise DuplicateEntityException("username", payload.username)

        user = User(
            email=payload.email,
            username=payload.username,
            full_name=payload.full_name,
            is_active=payload.is_active,
        )
        created = await self.repository.create(user)
        logger.info(f"User created: id={created.id}, username={created.username}")
        return created

    async def update_user(self, user_id: int, payload: UserUpdate) -> User:
        user = await self.get_user_by_id(user_id)

        update_data = payload.model_dump(exclude_unset=True)
        if (
            "email" in update_data
            and update_data["email"] != user.email
            and await self.repository.get_by_email(update_data["email"])
        ):
            raise DuplicateEntityException("email", update_data["email"])

        if (
            "username" in update_data
            and update_data["username"] != user.username
            and await self.repository.get_by_username(update_data["username"])
        ):
            raise DuplicateEntityException("username", update_data["username"])

        for field, value in update_data.items():
            setattr(user, field, value)

        updated = await self.repository.update(user)
        logger.info(f"User updated: id={updated.id}")
        return updated

    async def delete_user(self, user_id: int) -> None:
        user = await self.get_user_by_id(user_id)
        await self.repository.delete(user)
        logger.info(f"User deleted: id={user_id}")
