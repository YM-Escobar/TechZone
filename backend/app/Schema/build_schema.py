from datetime import datetime

from pydantic import BaseModel, Field

from app.Schema.common_schema import Money, ORMModel
from app.Schema.product_schema import ProductOut
from app.Schema.user_schema import UserSummary


class BuildItemIn(BaseModel):
    product_id: int
    quantity: int = Field(default=1, ge=1, le=20)


class BuildCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    description: str | None = None
    is_public: bool = False
    items: list[BuildItemIn] = Field(default_factory=list)


class BuildUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    description: str | None = None
    is_public: bool | None = None
    # Si se envía, reemplaza la lista completa de componentes
    items: list[BuildItemIn] | None = None


class BuildItemOut(ORMModel):
    id: int
    quantity: int
    product: ProductOut
    subtotal: Money


class BuildOut(ORMModel):
    id: int
    name: str
    description: str | None
    is_public: bool
    owner: UserSummary
    items: list[BuildItemOut]
    total_price: Money
    created_at: datetime
    updated_at: datetime
