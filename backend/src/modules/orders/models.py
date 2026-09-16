import enum
from decimal import Decimal

from sqlalchemy import Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.base_model import Base
from src.modules.products.models import Product
from src.modules.users.models import User


class OrderStatus(enum.StrEnum):
    PENDING = "PENDING"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"

    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status_enum", native_enum=False),
        default=OrderStatus.PENDING,
        nullable=False,
    )
    delivery_address: Mapped[str] = mapped_column(String(500), nullable=False)

    user: Mapped[User] = relationship(lazy="joined")
    product: Mapped[Product] = relationship(lazy="joined")
