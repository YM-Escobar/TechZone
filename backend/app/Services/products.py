from __future__ import annotations

from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.Models.product import Product, ProductCategory
from app.Models.user import User
from app.Repository.product_repository import ProductRepository
from app.Schema.common_schema import PageResult, update_data
from app.Schema.product_schema import ProductCreate, ProductUpdate
from app.Services import storage


class ProductService:
    def __init__(self, db: Session):
        self.products = ProductRepository(db)

    def list(
        self,
        viewer: User | None,
        skip: int,
        limit: int,
        search: str | None = None,
        category: ProductCategory | None = None,
        brand: str | None = None,
        min_price: Decimal | None = None,
        max_price: Decimal | None = None,
        include_inactive: bool = False,
    ) -> PageResult[Product]:
        # Solo el admin puede ver productos desactivados
        only_active = not (include_inactive and viewer is not None and viewer.is_admin)
        items, total = self.products.list(
            skip, limit, search=search, category=category, brand=brand,
            min_price=min_price, max_price=max_price, only_active=only_active,
        )
        return PageResult(items, total, skip, limit)

    def get(self, product_id: int, viewer: User | None = None) -> Product:
        product = self.products.get(product_id)
        if product is None or (not product.is_active and not (viewer and viewer.is_admin)):
            raise NotFoundError("Producto no encontrado")
        return product

    def create(self, data: ProductCreate) -> Product:
        return self.products.add(Product(**data.model_dump()))

    def update(self, product_id: int, data: ProductUpdate) -> Product:
        product = self._get_any(product_id)
        changes = update_data(data, {"description", "image_url"})
        if "image_url" in changes and changes["image_url"] != product.image_url:
            storage.delete_image(product.image_url)
        for field, value in changes.items():
            setattr(product, field, value)
        return self.products.save(product)

    def set_image(self, product_id: int, content: bytes) -> Product:
        product = self._get_any(product_id)
        new_url = storage.save_image(content, "products")
        storage.delete_image(product.image_url)
        product.image_url = new_url
        return self.products.save(product)

    def delete(self, product_id: int) -> None:
        product = self._get_any(product_id)
        if self.products.is_used_in_builds(product_id):
            raise ConflictError("El producto se usa en una o más builds; desactívalo en lugar de eliminarlo")
        image_url = product.image_url
        self.products.delete(product)
        storage.delete_image(image_url)

    def _get_any(self, product_id: int) -> Product:
        product = self.products.get(product_id)
        if product is None:
            raise NotFoundError("Producto no encontrado")
        return product
