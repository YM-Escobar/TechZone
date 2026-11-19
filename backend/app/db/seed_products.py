"""Carga el catálogo semilla de backend/seed/productos/ en la base de datos.

Uso (desde backend/, con DATABASE_URL apuntando a la base deseada):
    python -m app.db.seed_products            # crea o actualiza los productos
    python -m app.db.seed_products --dry-run  # solo valida, no escribe nada

Los productos se registran mediante ProductService, igual que la API, para que
el backend calcule is_builder_eligible. Se identifican por nombre y categoría:
si ya existen se actualizan (sin tocar su stock), así que el script se puede
ejecutar varias veces.
"""
from __future__ import annotations

import argparse
import json
import logging
import sys
from collections import Counter
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus

from sqlalchemy import select

from app.db.session import SessionLocal
from app.Models.product import Product, ProductCategory
from app.Schema.product_schema import ProductCreate, ProductUpdate
from app.Services.product_eligibility.eligibility import is_product_builder_eligible
from app.Services.products import ProductService

logger = logging.getLogger("techzone.seed")

SEED_DIR = Path(__file__).resolve().parents[2] / "seed" / "productos"


def amazon_search_url(name: str) -> str:
    """Enlace de búsqueda en Amazon para el nombre exacto del producto."""
    return f"https://www.amazon.com/s?k={quote_plus(name)}"


def load_catalog(seed_dir: Path = SEED_DIR) -> list[ProductCreate]:
    """Lee y valida todos los JSON del catálogo semilla."""
    products: list[ProductCreate] = []

    for path in sorted(seed_dir.glob("*.json")):
        for raw in json.loads(path.read_text(encoding="utf-8")):
            data: dict[str, Any] = dict(raw)
            data.setdefault("purchase_url", amazon_search_url(data["name"]))
            products.append(ProductCreate.model_validate(data))

    duplicates = [key for key, n in Counter((p.category, p.name) for p in products).items() if n > 1]
    if duplicates:
        raise ValueError(f"Productos duplicados en el catálogo: {duplicates}")

    return products


def seed_products(db, products: list[ProductCreate]) -> dict[str, int]:
    """Crea o actualiza los productos y devuelve un resumen."""
    service = ProductService(db)
    summary = {"creados": 0, "actualizados": 0, "no_elegibles": 0}

    for data in products:
        existing = db.scalar(
            select(Product).where(Product.name == data.name, Product.category == data.category)
        )

        if existing is None:
            product = service.create(data)
            summary["creados"] += 1
        else:
            # El stock real de la tienda no se pisa con el valor inicial del catálogo
            changes = ProductUpdate(**data.model_dump(exclude={"stock"}))
            product = service.update(existing.id, changes)
            summary["actualizados"] += 1

        if not product.is_builder_eligible:
            summary["no_elegibles"] += 1
            logger.warning("No elegible para el builder: %s (%s)", product.name, product.category)

    return summary


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="valida el catálogo sin escribir en la base")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    products = load_catalog()
    by_category = Counter(ProductCategory(p.category).value for p in products)
    logger.info("Catálogo: %d productos %s", len(products), dict(sorted(by_category.items())))

    if args.dry_run:
        ineligible = [p.name for p in products if not is_product_builder_eligible(p.category, p.specs)]
        for name in ineligible:
            logger.warning("No elegible para el builder: %s", name)
        logger.info("Validación terminada; %d no elegibles. No se escribió nada.", len(ineligible))
        return 1 if ineligible else 0

    with SessionLocal() as db:
        summary = seed_products(db, products)

    logger.info("Listo: %s", summary)
    return 1 if summary["no_elegibles"] else 0


if __name__ == "__main__":
    sys.exit(main())
