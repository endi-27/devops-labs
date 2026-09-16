from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessRuleException
from src.modules.orders.models import OrderStatus
from src.modules.orders.repository import OrderRepository
from src.modules.orders.schemas import OrderCreate, OrderUpdate
from src.modules.orders.service import OrderService
from src.modules.products.models import Product
from src.modules.products.repository import ProductRepository
from src.modules.users.models import User
from src.modules.users.repository import UserRepository


@pytest.mark.asyncio
async def test_create_order_success_and_stock_reduction(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    product_repo = ProductRepository(db_session)
    order_repo = OrderRepository(db_session)
    service = OrderService(order_repo, user_repo, product_repo)

    user = await user_repo.create(User(email="buyer@example.com", username="buyer", full_name="Buyer One"))
    product = await product_repo.create(
        Product(
            name="Cloud Handbook",
            sku="SKU-CLOUD",
            price=Decimal("50.00"),
            stock_quantity=10,
            is_available=True,
        )
    )

    payload = OrderCreate(
        user_id=user.id,
        product_id=product.id,
        quantity=3,
        delivery_address="Kyiv, Polytech St, 10",
    )
    order = await service.create_order(payload)

    assert order.id is not None
    assert order.total_price == Decimal("150.00")
    assert order.status == OrderStatus.PENDING

    # Verify stock reduction
    updated_product = await product_repo.get_by_id(product.id)
    assert updated_product is not None
    assert updated_product.stock_quantity == 7


@pytest.mark.asyncio
async def test_create_order_insufficient_stock_raises(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    product_repo = ProductRepository(db_session)
    order_repo = OrderRepository(db_session)
    service = OrderService(order_repo, user_repo, product_repo)

    user = await user_repo.create(User(email="buyer2@example.com", username="buyer2", full_name="Buyer Two"))
    product = await product_repo.create(
        Product(
            name="Limited Product",
            sku="SKU-LIMITED",
            price=Decimal("100.00"),
            stock_quantity=2,
            is_available=True,
        )
    )

    payload = OrderCreate(
        user_id=user.id,
        product_id=product.id,
        quantity=5,
        delivery_address="Lviv, Franko St, 1",
    )
    with pytest.raises(BusinessRuleException, match="Insufficient stock"):
        await service.create_order(payload)


@pytest.mark.asyncio
async def test_update_order_status_and_delete_returns_stock(db_session: AsyncSession) -> None:
    user_repo = UserRepository(db_session)
    product_repo = ProductRepository(db_session)
    order_repo = OrderRepository(db_session)
    service = OrderService(order_repo, user_repo, product_repo)

    user = await user_repo.create(User(email="buyer3@example.com", username="buyer3", full_name="Buyer Three"))
    product = await product_repo.create(
        Product(
            name="Gadget",
            sku="SKU-GADGET",
            price=Decimal("20.00"),
            stock_quantity=10,
            is_available=True,
        )
    )

    order = await service.create_order(
        OrderCreate(
            user_id=user.id,
            product_id=product.id,
            quantity=2,
            delivery_address="Odesa, Deribasivska St, 5",
        )
    )

    # Update status to PAID
    updated_order = await service.update_order(order.id, OrderUpdate(status=OrderStatus.PAID))
    assert updated_order.status == OrderStatus.PAID

    # Delete order -> stock returned
    await service.delete_order(order.id)
    refreshed_product = await product_repo.get_by_id(product.id)
    assert refreshed_product is not None
    assert refreshed_product.stock_quantity == 10
