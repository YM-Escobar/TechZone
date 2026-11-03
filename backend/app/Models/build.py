from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.Models.product import Product

if TYPE_CHECKING:
    from app.Models.user import User


class Build(Base):
    __tablename__ = "builds"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    description: Mapped[str | None] = mapped_column(Text)
    is_public: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    owner: Mapped["User"] = relationship(back_populates="builds", lazy="joined")
    items: Mapped[list["BuildItem"]] = relationship(
        back_populates="build", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def total_price(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0"))


class BuildItem(Base):
    __tablename__ = "build_items"
    __table_args__ = (UniqueConstraint("build_id", "product_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    build_id: Mapped[int] = mapped_column(ForeignKey("builds.id", ondelete="CASCADE"), index=True)
    # RESTRICT: un producto usado en builds no se puede borrar, solo desactivar
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="RESTRICT"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)

    build: Mapped[Build] = relationship(back_populates="items")
    product: Mapped[Product] = relationship(lazy="selectin")

    @property
    def subtotal(self) -> Decimal:
        return self.product.price * self.quantity
