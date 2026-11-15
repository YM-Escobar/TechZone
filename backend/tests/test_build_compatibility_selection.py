from unittest.mock import MagicMock, patch

import pytest

from app.Models.product import Product, ProductCategory
from app.Schema.build_schema import BuildItemIn
from app.Services.builds import BuildService
from app.core.exceptions import BadRequestError


@pytest.fixture
def service():
    with (
        patch("app.Services.builds.BuildRepository"),
        patch("app.Services.builds.ProductRepository") as product_repository,
        patch("app.Services.builds.AdvisoryRepository"),
        patch("app.Services.builds.CompatibilityService"),
    ):
        build_service = BuildService(db=MagicMock())
        yield build_service, product_repository.return_value


def make_product(product_id: int, category: ProductCategory) -> Product:
    return Product(
        id=product_id,
        name=f"Producto {product_id}",
        brand="Marca",
        category=category,
        price=100,
        stock=5,
        specs={},
        is_active=True,
        is_builder_eligible=True,
    )


@pytest.mark.parametrize(
    "category",
    [
        ProductCategory.CPU,
        ProductCategory.MOTHERBOARD,
        ProductCategory.PSU,
        ProductCategory.COOLING,
    ],
)
def test_compatibility_rejects_multiple_units_of_single_unit_categories(
    service,
    category,
):
    build_service, products_repository = service
    first_product = make_product(1, category)
    second_product = make_product(2, category)
    products_repository.get_many.return_value = [first_product, second_product]

    with pytest.raises(BadRequestError):
        build_service.evaluate_compatibility(
            [
                BuildItemIn(product_id=1),
                BuildItemIn(product_id=2),
            ]
        )

    build_service.compatibility.evaluate.assert_not_called()


def test_compatibility_rejects_accumulated_quantity_above_one_for_single_unit_category(
    service,
):
    build_service, products_repository = service
    cpu = make_product(1, ProductCategory.CPU)
    products_repository.get_many.return_value = [cpu]

    with pytest.raises(BadRequestError):
        build_service.evaluate_compatibility(
            [
                BuildItemIn(product_id=1, quantity=1),
                BuildItemIn(product_id=1, quantity=1),
            ]
        )

    build_service.compatibility.evaluate.assert_not_called()


@pytest.mark.parametrize(
    "category",
    [ProductCategory.RAM, ProductCategory.GPU, ProductCategory.STORAGE],
)
def test_compatibility_allows_multiple_units_of_multi_unit_categories(
    service,
    category,
):
    build_service, products_repository = service
    first_product = make_product(1, category)
    second_product = make_product(2, category)
    products_repository.get_many.return_value = [first_product, second_product]

    build_service.evaluate_compatibility(
        [
            BuildItemIn(product_id=1),
            BuildItemIn(product_id=2),
        ]
    )

    build_service.compatibility.evaluate.assert_called_once()


def test_compatibility_allows_one_unit_of_each_single_unit_category(service):
    build_service, products_repository = service
    products = [
        make_product(1, ProductCategory.CPU),
        make_product(2, ProductCategory.MOTHERBOARD),
        make_product(3, ProductCategory.PSU),
        make_product(4, ProductCategory.COOLING),
    ]
    products_repository.get_many.return_value = products

    build_service.evaluate_compatibility(
        [BuildItemIn(product_id=product.id) for product in products]
    )

    build_service.compatibility.evaluate.assert_called_once()
