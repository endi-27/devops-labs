from collections.abc import Sequence

from loguru import logger

from src.core.exceptions import BusinessRuleException, DuplicateEntityException, EntityNotFoundException
from src.models import Product
from src.repository import ProductRepository
from src.schemas import ProductCreate, ProductUpdate


class ProductService:
    """Сервісний шар бізнес-логіки товарів."""

    def __init__(self, repository: ProductRepository) -> None:
        self.repository = repository

    async def get_product_by_id(self, product_id: int) -> Product:
        product = await self.repository.get_by_id(product_id)
        if not product:
            raise EntityNotFoundException("Product", product_id)
        return product

    async def get_all_products(
        self,
        skip: int = 0,
        limit: int = 100,
        only_available: bool = False,
    ) -> Sequence[Product]:
        return await self.repository.get_all(skip=skip, limit=limit, only_available=only_available)

    async def create_product(self, payload: ProductCreate) -> Product:
        if await self.repository.get_by_sku(payload.sku):
            raise DuplicateEntityException("sku", payload.sku)

        product = Product(
            name=payload.name,
            description=payload.description,
            sku=payload.sku,
            price=payload.price,
            stock_quantity=payload.stock_quantity,
            is_available=payload.is_available,
        )
        created = await self.repository.create(product)
        logger.info(f"Product created: id={created.id}, sku={created.sku}")
        return created

    async def update_product(self, product_id: int, payload: ProductUpdate) -> Product:
        product = await self.get_product_by_id(product_id)

        update_data = payload.model_dump(exclude_unset=True)
        if (
            "sku" in update_data
            and update_data["sku"] != product.sku
            and await self.repository.get_by_sku(update_data["sku"])
        ):
            raise DuplicateEntityException("sku", update_data["sku"])

        for field, value in update_data.items():
            setattr(product, field, value)

        updated = await self.repository.update(product)
        logger.info(f"Product updated: id={updated.id}")
        return updated

    async def delete_product(self, product_id: int) -> None:
        product = await self.get_product_by_id(product_id)
        await self.repository.delete(product)
        logger.info(f"Product deleted: id={product_id}")

    async def reserve_stock(self, product_id: int, quantity: int) -> Product:
        """Атомарне резервування та списання залишку товару для замовлення."""
        product = await self.get_product_by_id(product_id)
        if not product.is_available:
            raise BusinessRuleException("Product is not available for ordering")
        if product.stock_quantity < quantity:
            raise BusinessRuleException(f"Insufficient stock: requested {quantity}, available {product.stock_quantity}")

        product.stock_quantity -= quantity
        updated = await self.repository.update(product)
        logger.info(f"Stock reserved for product {product_id}: -{quantity}, remaining={updated.stock_quantity}")
        return updated

    async def release_stock(self, product_id: int, quantity: int) -> Product:
        """Повернення залишку товару на склад при скасуванні або видаленні замовлення."""
        product = await self.get_product_by_id(product_id)
        product.stock_quantity += quantity
        updated = await self.repository.update(product)
        logger.info(f"Stock released for product {product_id}: +{quantity}, total={updated.stock_quantity}")
        return updated
