from collections.abc import Sequence
from decimal import Decimal

from loguru import logger

from src.core.exceptions import BusinessRuleException, EntityNotFoundException
from src.modules.orders.models import Order, OrderStatus
from src.modules.orders.repository import OrderRepository
from src.modules.orders.schemas import OrderCreate, OrderUpdate
from src.modules.products.repository import ProductRepository
from src.modules.users.repository import UserRepository


class OrderService:
    """Сервісний шар бізнес-логіки замовлень."""

    def __init__(
        self,
        order_repository: OrderRepository,
        user_repository: UserRepository,
        product_repository: ProductRepository,
    ):
        self.order_repository = order_repository
        self.user_repository = user_repository
        self.product_repository = product_repository

    async def get_order_by_id(self, order_id: int) -> Order:
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)
        return order

    async def get_all_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: int | None = None,
        status: OrderStatus | None = None,
    ) -> Sequence[Order]:
        return await self.order_repository.get_all(skip=skip, limit=limit, user_id=user_id, status=status)

    async def create_order(self, payload: OrderCreate) -> Order:
        user = await self.user_repository.get_by_id(payload.user_id)
        if not user:
            raise EntityNotFoundException("User", payload.user_id)
        if not user.is_active:
            raise BusinessRuleException("Cannot create order for inactive user")

        product = await self.product_repository.get_by_id(payload.product_id)
        if not product:
            raise EntityNotFoundException("Product", payload.product_id)
        if not product.is_available:
            raise BusinessRuleException("Product is not available for ordering")
        if product.stock_quantity < payload.quantity:
            raise BusinessRuleException(
                f"Insufficient stock: requested {payload.quantity}, available {product.stock_quantity}"
            )

        total_price = Decimal(str(product.price)) * Decimal(payload.quantity)

        # Резервування / зменшення кількості на складі
        product.stock_quantity -= payload.quantity
        await self.product_repository.update(product)

        order = Order(
            user_id=payload.user_id,
            product_id=payload.product_id,
            quantity=payload.quantity,
            total_price=total_price,
            status=OrderStatus.PENDING,
            delivery_address=payload.delivery_address,
        )
        created = await self.order_repository.create(order)
        logger.info(f"Order created: id={created.id}, total_price={total_price}")
        return created

    async def update_order(self, order_id: int, payload: OrderUpdate) -> Order:
        order = await self.get_order_by_id(order_id)

        update_data = payload.model_dump(exclude_unset=True)

        if (
            "quantity" in update_data
            and update_data["quantity"] is not None
            and update_data["quantity"] != order.quantity
        ):
            new_qty = update_data["quantity"]
            product = await self.product_repository.get_by_id(order.product_id)
            if not product:
                raise EntityNotFoundException("Product", order.product_id)

            diff = new_qty - order.quantity
            if diff > 0 and product.stock_quantity < diff:
                raise BusinessRuleException(
                    f"Insufficient stock for increase: need {diff}, available {product.stock_quantity}"
                )

            product.stock_quantity -= diff
            await self.product_repository.update(product)

            order.quantity = new_qty
            order.total_price = Decimal(str(product.price)) * Decimal(new_qty)

        if "status" in update_data and update_data["status"] is not None:
            order.status = update_data["status"]

        if "delivery_address" in update_data and update_data["delivery_address"] is not None:
            order.delivery_address = update_data["delivery_address"]

        updated = await self.order_repository.update(order)
        logger.info(f"Order updated: id={updated.id}, status={updated.status}")
        return updated

    async def delete_order(self, order_id: int) -> None:
        order = await self.get_order_by_id(order_id)
        # Повертаємо товар на склад при видаленні замовлення, якщо воно не було відправлене
        if order.status != OrderStatus.SHIPPED:
            product = await self.product_repository.get_by_id(order.product_id)
            if product:
                product.stock_quantity += order.quantity
                await self.product_repository.update(product)

        await self.order_repository.delete(order)
        logger.info(f"Order deleted: id={order_id}")
