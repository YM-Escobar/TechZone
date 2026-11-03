from datetime import datetime
from decimal import Decimal
from enum import StrEnum
from typing import Any

from sqlalchemy import JSON, Boolean, DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.db.types import enum_column


class ProductCategory(StrEnum):
    CPU = "cpu"
    GPU = "gpu"
    MOTHERBOARD = "placa_madre"
    RAM = "ram"
    STORAGE = "almacenamiento"
    PSU = "fuente"
    CASE = "gabinete"
    COOLING = "refrigeracion"
    MONITOR = "monitor"
    PERIPHERAL = "periferico"


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    brand: Mapped[str] = mapped_column(String(80), index=True)
    category: Mapped[ProductCategory] = mapped_column(enum_column(ProductCategory), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    image_url: Mapped[str | None] = mapped_column(String(500))
    specs: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
