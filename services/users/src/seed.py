import asyncio

from loguru import logger
from sqlalchemy import select

from src.core.database import async_session_factory, close_db
from src.models import User


async def seed() -> None:
    logger.info("Users Service: Seeding initial data...")
    async with async_session_factory() as session:
        result = await session.execute(select(User))
        if result.scalars().first():
            logger.info("Users Service: Database already has users. Skipping.")
            return

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
        await session.commit()
        logger.info("Users Service: Seeded admin and student users.")


async def main() -> None:
    try:
        await seed()
    finally:
        await close_db()


if __name__ == "__main__":
    asyncio.run(main())
