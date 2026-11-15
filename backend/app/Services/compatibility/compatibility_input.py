
from typing import Any

from app.Models.product import Product, ProductCategory
from app.Schema.build_schema import BuildItemIn


# Relaciona las categorías de la base de datos con las claves
# que utiliza el motor de compatibilidad.
CATEGORY_MAPPING = {
    ProductCategory.CPU: "cpu",
    ProductCategory.MOTHERBOARD: "motherboard",
    ProductCategory.RAM: "ram",
    ProductCategory.GPU: "gpu",
    ProductCategory.PSU: "psu",
    ProductCategory.COOLING: "cooling",
    ProductCategory.STORAGE: "storage",
}


def build_compatibility_components(
    products: list[Product],
    items: list[BuildItemIn],
) -> dict[str, Any]:
    """
    Convierte productos y cantidades en la estructura
    que necesita run_compatibility_rules().

    Los componentes no contemplados en el configurador,
    como gabinetes, monitores y periféricos, se excluyen.
    """

    # Acumular cantidades por producto para evitar duplicados.
    quantities: dict[int, int] = {}

    for item in items:
        quantities[item.product_id] = (
            quantities.get(item.product_id, 0) + item.quantity
        )

    # Preparar las categorías que recibe el Engine.
    components: dict[str, Any] = {
        "cpu": [],
        "motherboard": [],
        "ram": [],
        "gpu": [],
        "psu": [],
        "cooling": [],
        "storage": [],
    }

    # Transformar cada producto al formato esperado.
    for product in products:
        category = product.category

        # Obtener el valor del enum o utilizar el valor directamente.
        if isinstance(category, str):
            category_value = category
        else:
            category_value = getattr(category, "value", None)

        # Excluir categorías que no participan en compatibilidad.
        try:
            category_enum = ProductCategory(category_value)
        except (ValueError, TypeError):
            continue

        engine_category = CATEGORY_MAPPING.get(category_enum)

        if engine_category is None:
            continue

        # Recuperar la cantidad solicitada.
        quantity = quantities.get(product.id, 0)

        if quantity <= 0:
            continue

        # Crear la estructura que consume el Engine.
        component = {
            "name": product.name,
            "specs": product.specs,
            "quantity": quantity,
        }

        components[engine_category].append(component)

    return components
