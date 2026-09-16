from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import get_db_session
from src.modules.orders.models import OrderStatus
from src.modules.orders.repository import OrderRepository
from src.modules.orders.schemas import OrderCreate, OrderResponse, OrderUpdate
from src.modules.orders.service import OrderService
from src.modules.products.repository import ProductRepository
from src.modules.users.repository import UserRepository

router = APIRouter(prefix="/orders", tags=["Orders"])


def get_order_service(session: AsyncSession = Depends(get_db_session)) -> OrderService:
    order_repo = OrderRepository(session)
    user_repo = UserRepository(session)
    product_repo = ProductRepository(session)
    return OrderService(order_repo, user_repo, product_repo)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """Створення нового замовлення."""
    order = await service.create_order(payload)
    return OrderResponse.model_validate(order)


@router.get("", response_model=list[OrderResponse])
async def get_all_orders(
    skip: int = Query(0, ge=0, description="Кількість записів для пропуску"),
    limit: int = Query(100, ge=1, le=500, description="Максимальна кількість записів"),
    user_id: int | None = Query(None, description="Фільтр за ID користувача"),
    status: OrderStatus | None = Query(None, description="Фільтр за статусом"),
    service: OrderService = Depends(get_order_service),
) -> list[OrderResponse]:
    """Отримання списку замовлень з фільтрацією."""
    orders = await service.get_all_orders(skip=skip, limit=limit, user_id=user_id, status=status)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """Отримання інформації про замовлення за ID."""
    order = await service.get_order_by_id(order_id)
    return OrderResponse.model_validate(order)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    payload: OrderUpdate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    """Оновлення інформації або статусу замовлення."""
    order = await service.update_order(order_id, payload)
    return OrderResponse.model_validate(order)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> None:
    """Видалення або скасування замовлення."""
    await service.delete_order(order_id)
