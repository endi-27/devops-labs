from collections.abc import Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.modules.orders.models import Order, OrderStatus


class OrderRepository:
    """Шар доступу до даних для замовлень."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order).options(selectinload(Order.user), selectinload(Order.product)).where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_all(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: int | None = None,
        status: OrderStatus | None = None,
    ) -> Sequence[Order]:
        query = select(Order).options(selectinload(Order.user), selectinload(Order.product))
        if user_id is not None:
            query = query.where(Order.user_id == user_id)
        if status is not None:
            query = query.where(Order.status == status)
        result = await self.session.execute(query.offset(skip).limit(limit).order_by(Order.id.desc()))
        return result.scalars().all()

    async def create(self, order: Order) -> Order:
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order, ["user", "product"])
        return order

    async def update(self, order: Order) -> Order:
        await self.session.commit()
        await self.session.refresh(order, ["user", "product"])
        return order

    async def delete(self, order: Order) -> None:
        await self.session.delete(order)
        await self.session.commit()
