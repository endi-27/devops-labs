from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Order, OrderStatus
from src.repository import OrderRepository


@pytest.mark.asyncio
async def test_order_repository_crud(db_session: AsyncSession) -> None:
    repo = OrderRepository(db_session)

    order = Order(
        user_id=10,
        product_id=20,
        quantity=2,
        total_price=Decimal("49.98"),
        status=OrderStatus.PENDING,
        delivery_address="Dnipro, Central Ave, 1",
    )
    created = await repo.create(order)
    assert created.id is not None

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.total_price == Decimal("49.98")

    all_orders = await repo.get_all(user_id=10)
    assert len(all_orders) == 1

    created.status = OrderStatus.PAID
    updated = await repo.update(created)
    assert updated.status == OrderStatus.PAID

    await repo.delete(updated)
    assert await repo.get_by_id(created.id) is None
