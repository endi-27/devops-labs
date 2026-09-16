from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.modules.users.repository import UserRepository
from src.modules.users.schemas import UserCreate, UserResponse, UserUpdate
from src.modules.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(session: AsyncSession = Depends(get_db_session)) -> UserService:
    repository = UserRepository(session)
    return UserService(repository)


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    payload: UserCreate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Створення нового користувача."""
    user = await service.create_user(payload)
    return UserResponse.model_validate(user)


@router.get("", response_model=list[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0, description="Кількість записів для пропуску"),
    limit: int = Query(100, ge=1, le=500, description="Максимальна кількість записів"),
    service: UserService = Depends(get_user_service),
) -> list[UserResponse]:
    """Отримання списку користувачів з пагінацією."""
    users = await service.get_all_users(skip=skip, limit=limit)
    return [UserResponse.model_validate(u) for u in users]


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Отримання користувача за ID."""
    user = await service.get_user_by_id(user_id)
    return UserResponse.model_validate(user)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    payload: UserUpdate,
    service: UserService = Depends(get_user_service),
) -> UserResponse:
    """Оновлення інформації користувача."""
    user = await service.update_user(user_id, payload)
    return UserResponse.model_validate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    service: UserService = Depends(get_user_service),
) -> None:
    """Видалення користувача."""
    await service.delete_user(user_id)
