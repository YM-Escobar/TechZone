from types import SimpleNamespace

from app.Models.product import ProductCategory
from app.Schema.build_schema import BuildItemIn
from app.Services.compatibility.compatibility_input import build_compatibility_components


def test_build_compatibility_components_maps_categories():
    products = [
        SimpleNamespace(
            id=1,
            name="Ryzen 5 5600",
            category=ProductCategory.CPU,
            specs={"socket": "AM4"},
        ),
        SimpleNamespace(
            id=2,
            name="B550M",
            category=ProductCategory.MOTHERBOARD,
            specs={"socket": "AM4"},
        ),
    ]

    items = [
        BuildItemIn(product_id=1, quantity=1),
        BuildItemIn(product_id=2, quantity=1),
    ]

    result = build_compatibility_components(products, items)

    assert result["cpu"] == [
        {"name": "Ryzen 5 5600", "specs": {"socket": "AM4"}, "quantity": 1}
    ]
    assert result["motherboard"] == [
        {"name": "B550M", "specs": {"socket": "AM4"}, "quantity": 1}
    ]


def test_build_compatibility_components_sums_quantities():
    products = [
        SimpleNamespace(
            id=1,
            name="RAM DDR4",
            category=ProductCategory.RAM,
            specs={"memory_type": "DDR4"},
        )
    ]

    items = [
        BuildItemIn(product_id=1, quantity=2),
        BuildItemIn(product_id=1, quantity=1),
    ]

    result = build_compatibility_components(products, items)

    assert result["ram"] == [
        {"name": "RAM DDR4", "specs": {"memory_type": "DDR4"}, "quantity": 3}
    ]


def test_build_compatibility_components_ignores_unsupported_categories():
    products = [
        SimpleNamespace(
            id=1,
            name="Monitor",
            category="monitor",
            specs={},
        )
    ]

    items = [BuildItemIn(product_id=1, quantity=1)]

    result = build_compatibility_components(products, items)

    assert all(not components for components in result.values())

    