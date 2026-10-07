from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from src.models import OrderStatus


class OrderBase(BaseModel):
    user_id: int = Field(..., gt=0)
    product_id: int = Field(..., gt=0)
    quantity: int = Field(1, ge=1, le=1000)
    delivery_address: str = Field(..., min_length=5, max_length=500)


class OrderCreate(OrderBase):
    pass


class OrderUpdate(BaseModel):
    status: OrderStatus | None = None
    quantity: int | None = Field(None, ge=1, le=1000)
    delivery_address: str | None = Field(None, min_length=5, max_length=500)


class UserSummary(BaseModel):
    id: int
    email: str
    username: str
    full_name: str
    is_active: bool = True

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class ProductSummary(BaseModel):
    id: int
    name: str
    sku: str
    price: Decimal
    stock_quantity: int = 0
    is_available: bool = True

    model_config = ConfigDict(from_attributes=True, extra="ignore")


class OrderResponse(BaseModel):
    id: int
    user_id: int
    product_id: int
    quantity: int
    total_price: Decimal
    status: OrderStatus
    delivery_address: str
    created_at: datetime
    updated_at: datetime

    user: UserSummary | None = None
    product: ProductSummary | None = None

    model_config = ConfigDict(from_attributes=True)
