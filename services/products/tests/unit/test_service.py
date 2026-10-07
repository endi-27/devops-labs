from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import BusinessRuleException, DuplicateEntityException, EntityNotFoundException
from src.repository import ProductRepository
from src.schemas import ProductCreate, ProductUpdate
from src.service import ProductService


@pytest.mark.asyncio
async def test_create_product_success(db_session: AsyncSession) -> None:
    repo = ProductRepository(db_session)
    service = ProductService(repo)

    payload = ProductCreate(
        name="DevOps Manual",
        description="A great book",
        sku="SKU-100",
        price=Decimal("29.99"),
        stock_quantity=10,
        is_available=True,
    )
    product = await service.create_product(payload)

    assert product.id is not None
    assert product.name == "DevOps Manual"
    assert product.sku == "SKU-100"
    assert product.price == Decimal("29.99")
    assert product.stock_quantity == 10


@pytest.mark.asyncio
async def test_create_duplicate_product_sku_raises(db_session: AsyncSession) -> None:
    repo = ProductRepository(db_session)
    service = ProductService(repo)

    payload = ProductCreate(
        name="DevOps Manual",
        sku="SKU-UNIQUE",
        price=Decimal("15.00"),
        stock_quantity=5,
    )
    await service.create_product(payload)

    with pytest.raises(DuplicateEntityException):
        await service.create_product(
            ProductCreate(
                name="Another Manual",
                sku="SKU-UNIQUE",
                price=Decimal("20.00"),
                stock_quantity=2,
            )
        )


@pytest.mark.asyncio
async def test_update_and_delete_product(db_session: AsyncSession) -> None:
    repo = ProductRepository(db_session)
    service = ProductService(repo)

    product = await service.create_product(
        ProductCreate(
            name="Original Product",
            sku="SKU-UPDATE-1",
            price=Decimal("10.00"),
            stock_quantity=20,
        )
    )

    updated = await service.update_product(product.id, ProductUpdate(price=Decimal("12.50"), stock_quantity=15))
    assert updated.price == Decimal("12.50")
    assert updated.stock_quantity == 15

    await service.delete_product(product.id)

    with pytest.raises(EntityNotFoundException):
        await service.get_product_by_id(product.id)


@pytest.mark.asyncio
async def test_reserve_and_release_stock(db_session: AsyncSession) -> None:
    repo = ProductRepository(db_session)
    service = ProductService(repo)

    product = await service.create_product(
        ProductCreate(
            name="Stock Item",
            sku="SKU-STOCK-1",
            price=Decimal("10.00"),
            stock_quantity=10,
            is_available=True,
        )
    )

    # Успішне резервування
    reserved = await service.reserve_stock(product.id, 4)
    assert reserved.stock_quantity == 6

    # Спроба зарезервувати більше, ніж є в наявності
    with pytest.raises(BusinessRuleException):
        await service.reserve_stock(product.id, 10)

    # Повернення на склад
    released = await service.release_stock(product.id, 2)
    assert released.stock_quantity == 8
