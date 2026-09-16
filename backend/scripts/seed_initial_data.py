import asyncio
from decimal import Decimal

from loguru import logger
from sqlalchemy import select

from src.core.database import async_session_factory, close_db
from src.modules.orders.models import Order, OrderStatus
from src.modules.products.models import Product
from src.modules.users.models import User


async def seed() -> None:
    logger.info("Seeding initial data...")
    async with async_session_factory() as session:
        # Check if users already seeded
        result = await session.execute(select(User))
        existing_user = result.scalars().first()
        if existing_user:
            logger.info("Database already seeded. Skipping.")
            return

        # 1. Create Users
        admin_user = User(
            email="admin@devops.org",
            username="admin",
            full_name="Platform Administrator",
            is_active=True,
        )
        test_user = User(
            email="student@devops.org",
            username="student",
            full_name="DevOps Student",
            is_active=True,
        )
        session.add_all([admin_user, test_user])
        await session.flush()

        # 2. Create Products
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
        await session.flush()

        # 3. Create Sample Order
        order = Order(
            user_id=test_user.id,
            product_id=p1.id,
            quantity=2,
            total_price=Decimal("99.98"),
            status=OrderStatus.PAID,
            delivery_address="Main Campus, DevOps Lab 304",
        )
        p1.stock_quantity -= 2
        session.add(order)

        await session.commit()
        logger.info("Initial data seeded successfully!")


async def main() -> None:
    try:
        await seed()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
