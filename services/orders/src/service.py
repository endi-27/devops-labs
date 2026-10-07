from collections.abc import Sequence
from decimal import Decimal
from typing import Any

from loguru import logger

from src.clients.products_client import ProductsClient
from src.clients.users_client import UsersClient
from src.core.exceptions import BusinessRuleException, EntityNotFoundException
from src.models import Order, OrderStatus
from src.repository import OrderRepository
from src.schemas import OrderCreate, OrderResponse, OrderUpdate, ProductSummary, UserSummary


class OrderService:
    """Сервісний шар бізнес-логіки замовлень у мікросервісній архітектурі."""

    def __init__(
        self,
        order_repository: OrderRepository,
        users_client: UsersClient,
        products_client: ProductsClient,
    ) -> None:
        self.order_repository = order_repository
        self.users_client = users_client
        self.products_client = products_client

    async def get_raw_order(self, order_id: int) -> Order:
        order = await self.order_repository.get_by_id(order_id)
        if not order:
            raise EntityNotFoundException("Order", order_id)
        return order

    async def get_order_by_id(self, order_id: int) -> OrderResponse:
        order = await self.get_raw_order(order_id)

        user_data: dict[str, Any] | None = None
        product_data: dict[str, Any] | None = None

        try:
            user_data = await self.users_client.get_user_by_id(order.user_id)
        except Exception as exc:
            logger.warning(f"Could not fetch user details for order {order_id}: {exc}")

        try:
            product_data = await self.products_client.get_product_by_id(order.product_id)
        except Exception as exc:
            logger.warning(f"Could not fetch product details for order {order_id}: {exc}")

        response = OrderResponse.model_validate(order)
        if user_data:
            response.user = UserSummary.model_validate(user_data)
        if product_data:
            response.product = ProductSummary.model_validate(product_data)
        return response

    async def get_all_orders(
        self,
        skip: int = 0,
        limit: int = 100,
        user_id: int | None = None,
        status: OrderStatus | None = None,
    ) -> Sequence[Order]:
        return await self.order_repository.get_all(skip=skip, limit=limit, user_id=user_id, status=status)

    async def create_order(self, payload: OrderCreate) -> OrderResponse:
        # 1. Перевірка користувача через UsersClient
        user = await self.users_client.get_user_by_id(payload.user_id)
        if not user.get("is_active", True):
            raise BusinessRuleException("Cannot create order for inactive user")

        # 2. Перевірка та резервування товару через ProductsClient
        product = await self.products_client.reserve_stock(payload.product_id, payload.quantity)
        price = Decimal(str(product["price"]))
        total_price = price * Decimal(payload.quantity)

        # 3. Створення запису замовлення
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

        response = OrderResponse.model_validate(created)
        response.user = UserSummary.model_validate(user)
        response.product = ProductSummary.model_validate(product)
        return response

    async def update_order(self, order_id: int, payload: OrderUpdate) -> OrderResponse:
        order = await self.get_raw_order(order_id)
        update_data = payload.model_dump(exclude_unset=True)

        if (
            "quantity" in update_data
            and update_data["quantity"] is not None
            and update_data["quantity"] != order.quantity
        ):
            new_qty = update_data["quantity"]
            diff = new_qty - order.quantity
            if diff > 0:
                product = await self.products_client.reserve_stock(order.product_id, diff)
            else:
                product = await self.products_client.release_stock(order.product_id, abs(diff))

            price = Decimal(str(product["price"]))
            order.quantity = new_qty
            order.total_price = price * Decimal(new_qty)

        if "status" in update_data and update_data["status"] is not None:
            order.status = update_data["status"]

        if "delivery_address" in update_data and update_data["delivery_address"] is not None:
            order.delivery_address = update_data["delivery_address"]

        updated = await self.order_repository.update(order)
        logger.info(f"Order updated: id={updated.id}, status={updated.status}")
        return await self.get_order_by_id(updated.id)

    async def delete_order(self, order_id: int) -> None:
        order = await self.get_raw_order(order_id)
        if order.status != OrderStatus.SHIPPED:
            await self.products_client.release_stock(order.product_id, order.quantity)

        await self.order_repository.delete(order)
        logger.info(f"Order deleted: id={order_id}")
