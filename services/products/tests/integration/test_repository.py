from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Product
from src.repository import ProductRepository


@pytest.mark.asyncio
async def test_product_repository_crud(db_session: AsyncSession) -> None:
    repo = ProductRepository(db_session)

    product = Product(
        name="Repo Product",
        description="Repo Description",
        sku="SKU-REPO-1",
        price=Decimal("19.99"),
        stock_quantity=50,
        is_available=True,
    )
    created = await repo.create(product)
    assert created.id is not None

    fetched = await repo.get_by_id(created.id)
    assert fetched is not None
    assert fetched.sku == "SKU-REPO-1"

    by_sku = await repo.get_by_sku("SKU-REPO-1")
    assert by_sku is not None

    all_products = await repo.get_all()
    assert len(all_products) >= 1

    created.name = "Updated Repo Product"
    updated = await repo.update(created)
    assert updated.name == "Updated Repo Product"

    await repo.delete(updated)
    assert await repo.get_by_id(created.id) is None
