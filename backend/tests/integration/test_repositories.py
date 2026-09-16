from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.orders.models import Order, OrderStatus
from src.modules.orders.repository import OrderRepository
from src.modules.products.models import Product
from src.modules.products.repository import ProductRepository
from src.modules.users.models import User
from src.modules.users.repository import UserRepository


@pytest.mark.asyncio
async def test_user_repository_crud(db_session: AsyncSession) -> None:
    repo = UserRepository(db_session)

    # 1. Create
    user = User(email="test@repo.com", username="repouser", full_name="Repo User")
    created = await repo.create(user)
    assert created.id is not None

    # 2. Get by ID & Email & Username
    assert await repo.get_by_id(created.id) is not None
    assert await repo.get_by_email("test@repo.com") is not None
    assert await repo.get_by_username("repouser") is not None

    # 3. Get All
    all_users = await repo.get_all()
    assert len(all_users) == 1

    # 4. Update
    created.full_name = "Repo User Updated"
    updated = await repo.update(created)
    assert updated.full_name == "Repo User Updated"

    # 5. Delete
    await repo.delete(created)
    assert await repo.get_by_id(created.id) is None


@pytest.mark.asyncio
async def test_product_repository_crud_and_filtering(db_session: AsyncSession) -> None:
    repo = ProductRepository(db_session)

    p1 = Product(name="Item 1", sku="SKU-1", price=Decimal("10.00"), stock_quantity=5, is_available=True)
    p2 = Product(name="Item 2", sku="SKU-2", price=Decimal("20.00"), stock_quantity=0, is_available=False)
    await repo.create(p1)
    await repo.create(p2)

    all_products = await repo.get_all()
    assert len(all_products) == 2

    available_products = await repo.get_all(only_available=True)
    assert len(available_products) == 1
    assert available_products[0].sku == "SKU-1"


@pytest.mark.asyncio
async def test_order_repository_with_relations(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    product_repo = ProductRepository(db_session)
    order_repo = OrderRepository(db_session)

    user = await user_repo.create(User(email="u@test.com", username="utest", full_name="U Test"))
    product = await product_repo.create(Product(name="P Test", sku="SKU-P", price=Decimal("15.00"), stock_quantity=10))

    order = Order(
        user_id=user.id,
        product_id=product.id,
        quantity=2,
        total_price=Decimal("30.00"),
        status=OrderStatus.PENDING,
        delivery_address="Delivery 1",
    )
    created_order = await order_repo.create(order)

    fetched = await order_repo.get_by_id(created_order.id)
    assert fetched is not None
    assert fetched.user.email == "u@test.com"
    assert fetched.product.sku == "SKU-P"
