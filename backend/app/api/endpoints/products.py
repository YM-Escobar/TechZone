from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile, status

from app.api.deps import AdminUser, DbSession, OptionalUser, PaginationDep, read_upload
from app.Models.product import ProductCategory
from app.Schema.common_schema import Page
from app.Schema.product_schema import ProductCreate, ProductOut, ProductUpdate
from app.Services.products import ProductService

router = APIRouter(prefix="/products", tags=["productos"])


def get_service(db: DbSession) -> ProductService:
    return ProductService(db)


Service = Annotated[ProductService, Depends(get_service)]


@router.get("", response_model=Page[ProductOut])
def list_products(
    viewer: OptionalUser,
    service: Service,
    page: PaginationDep,
    search: str | None = None,
    category: ProductCategory | None = None,
    brand: str | None = None,
    min_price: Decimal | None = None,
    max_price: Decimal | None = None,
    include_inactive: bool = False,
):
    return service.list(
        viewer, page.skip, page.limit, search=search, category=category, brand=brand,
        min_price=min_price, max_price=max_price, include_inactive=include_inactive,
    )


@router.get("/{product_id}", response_model=ProductOut)
def read_product(product_id: int, viewer: OptionalUser, service: Service):
    return service.get(product_id, viewer)


@router.post("", response_model=ProductOut, status_code=status.HTTP_201_CREATED)
def create_product(data: ProductCreate, _: AdminUser, service: Service):
    return service.create(data)


@router.patch("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, data: ProductUpdate, _: AdminUser, service: Service):
    return service.update(product_id, data)


@router.put("/{product_id}/image", response_model=ProductOut)
def upload_product_image(product_id: int, file: UploadFile, _: AdminUser, service: Service):
    return service.set_image(product_id, read_upload(file))


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, _: AdminUser, service: Service):
    service.delete(product_id)
