from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

from app.Models.product import ProductCategory
from app.Schema.common_schema import Money, ORMModel


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    brand: str = Field(min_length=1, max_length=80)
    category: ProductCategory
    description: str | None = None
    price: Money = Field(gt=0, max_digits=10, decimal_places=2)
    stock: int = Field(default=0, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    specs: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    brand: str | None = Field(default=None, min_length=1, max_length=80)
    category: ProductCategory | None = None
    description: str | None = None
    price: Money | None = Field(default=None, gt=0, max_digits=10, decimal_places=2)
    stock: int | None = Field(default=None, ge=0)
    image_url: str | None = Field(default=None, max_length=500)
    specs: dict[str, Any] | None = None
    is_active: bool | None = None


class ProductOut(ORMModel):
    id: int
    name: str
    brand: str
    category: ProductCategory
    description: str | None
    price: Money
    stock: int
    image_url: str | None
    specs: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
