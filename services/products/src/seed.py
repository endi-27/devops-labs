import asyncio
from decimal import Decimal

from loguru import logger
from sqlalchemy import select

from src.core.database import async_session_factory, close_db
from src.models import Product


async def seed() -> None:
    logger.info("Products Service: Seeding initial data...")
    async with async_session_factory() as session:
        result = await session.execute(select(Product))
        if result.scalars().first():
            logger.info("Products Service: Database already has products. Skipping.")
            return

        p1 = Product(
            name="DevOps Handbook",
            description="Comprehensive guide to DevOps practices and principles",
            sku="BOOK-DEVOPS-01",
            price=Decimal("49.99"),
            stock_quantity=50,
            is_available=True,
        )
        p2 = Product(
            name="Kubernetes in Action",
            description="Hands-on guide to container orchestration",
            sku="BOOK-K8S-02",
            price=Decimal("59.99"),
            stock_quantity=30,
            is_available=True,
        )
        p3 = Product(
            name="Docker Container Sticker Pack",
            description="Vinyl stickers for laptop decoration",
            sku="STK-DOCKER-01",
            price=Decimal("9.99"),
            stock_quantity=100,
            is_available=True,
        )
        session.add_all([p1, p2, p3])
        await session.commit()
        logger.info("Products Service: Seeded initial products.")


async def main() -> None:
    try:
        await seed()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
