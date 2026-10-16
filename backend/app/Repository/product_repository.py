from __future__ import annotations

from decimal import Decimal

from sqlalchemy import exists, or_, select

from app.Models.build import BuildItem
from app.Models.product import Product, ProductCategory
from app.Repository.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    model = Product

    def list(
        self,
        skip: int,
        limit: int,
        search: str | None = None,
        category: ProductCategory | None = None,
        brand: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        only_active: bool = True,
    ) -> tuple[list[Product], int]:
        stmt = select(Product).order_by(Product.name, Product.id)
        if search:
            pattern = f"%{search}%"
            stmt = stmt.where(or_(Product.name.ilike(pattern), Product.description.ilike(pattern)))
        if category is not None:
            stmt = stmt.where(Product.category == category)
        if brand:
            stmt = stmt.where(Product.brand.ilike(brand))
        if min_price is not None:
            stmt = stmt.where(Product.price >= min_price)
        if max_price is not None:
            stmt = stmt.where(Product.price <= max_price)
        if only_active:
            stmt = stmt.where(Product.is_active.is_(True))
        return self.paginate(stmt, skip, limit)

    def get_many(self, product_ids: list[int]) -> list[Product]:
        if not product_ids:
            return []
        return list(self.db.scalars(select(Product).where(Product.id.in_(product_ids))))

    def is_used_in_builds(self, product_id: int) -> bool:
        return bool(self.db.scalar(select(exists().where(BuildItem.product_id == product_id))))
