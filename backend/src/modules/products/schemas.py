from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    sku: str = Field(..., min_length=3, max_length=50)
    price: Decimal = Field(..., gt=Decimal("0.00"), decimal_places=2)
    stock_quantity: int = Field(0, ge=0)
    is_available: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    sku: str | None = Field(None, min_length=3, max_length=50)
    price: Decimal | None = Field(None, gt=Decimal("0.00"), decimal_places=2)
    stock_quantity: int | None = Field(None, ge=0)
    is_available: bool | None = None


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
