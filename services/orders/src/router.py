from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.clients.products_client import ProductsClient
from src.clients.users_client import UsersClient
from src.core.database import get_db_session
from src.models import OrderStatus
from src.repository import OrderRepository
from src.schemas import OrderCreate, OrderResponse, OrderUpdate
from src.service import OrderService

router = APIRouter(prefix="/api/v1/orders", tags=["Orders"])


def get_users_client() -> UsersClient:
    return UsersClient()


def get_products_client() -> ProductsClient:
    return ProductsClient()


def get_order_service(
    session: AsyncSession = Depends(get_db_session),
    users_client: UsersClient = Depends(get_users_client),
    products_client: ProductsClient = Depends(get_products_client),
) -> OrderService:
    repository = OrderRepository(session)
    return OrderService(repository, users_client, products_client)


@router.post("", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return await service.create_order(payload)


@router.get("", response_model=list[OrderResponse])
async def get_all_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    user_id: int | None = Query(None),
    status: OrderStatus | None = Query(None),
    service: OrderService = Depends(get_order_service),
) -> list[OrderResponse]:
    orders = await service.get_all_orders(skip=skip, limit=limit, user_id=user_id, status=status)
    return [OrderResponse.model_validate(o) for o in orders]


@router.get("/{order_id}", response_model=OrderResponse)
async def get_order_by_id(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return await service.get_order_by_id(order_id)


@router.put("/{order_id}", response_model=OrderResponse)
async def update_order(
    order_id: int,
    payload: OrderUpdate,
    service: OrderService = Depends(get_order_service),
) -> OrderResponse:
    return await service.update_order(order_id, payload)


@router.delete("/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_order(
    order_id: int,
    service: OrderService = Depends(get_order_service),
) -> None:
    await service.delete_order(order_id)
