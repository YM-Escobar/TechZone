"""Comprueba que el catálogo semilla sea elegible y coherente con el motor de compatibilidad."""
from collections import Counter

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.seed_products import load_catalog, seed_products
from app.db.session import Base
from app.Models.product import ProductCategory as Cat
from app.Services.compatibility.compatibility_service import CompatibilityService
from app.Services.compatibility.engine import run_compatibility_rules
from app.Services.product_eligibility.eligibility import is_product_builder_eligible

CATALOG = load_catalog()


def of(category: Cat) -> list:
    return [p for p in CATALOG if p.category == category]


def by_name(name: str):
    return next(p for p in CATALOG if p.name == name)


def component(product, quantity: int = 1) -> dict:
    return {"name": product.name, "specs": product.specs, "quantity": quantity}


def test_catalog_has_at_least_20_products_per_category():
    counts = Counter(p.category for p in CATALOG)
    builder_categories = [Cat.CPU, Cat.MOTHERBOARD, Cat.RAM, Cat.GPU, Cat.PSU, Cat.COOLING, Cat.STORAGE]
    assert set(counts) == set(builder_categories)
    assert all(counts[c] >= 20 for c in builder_categories), counts


@pytest.mark.parametrize("product", CATALOG, ids=lambda p: p.name)
def test_every_product_is_builder_eligible_and_has_store_link(product):
    assert is_product_builder_eligible(product.category, product.specs)
    assert product.purchase_url and product.purchase_url.startswith("https://")


def test_motherboards_list_only_catalog_cpus_of_their_socket():
    cpus = {c.name: c.specs["socket"] for c in of(Cat.CPU)}
    listed = set()
    for board in of(Cat.MOTHERBOARD):
        for entry in board.specs["supported_cpu_models"]:
            # El motor compara el nombre exacto del producto CPU con "model"
            assert cpus.get(entry["model"]) == board.specs["socket"], (board.name, entry["model"])
            listed.add(entry["model"])
    assert listed == set(cpus), "Hay CPU que ninguna placa declara como compatible"


def test_every_component_has_a_compatible_partner():
    sockets = {c.specs["socket"] for c in of(Cat.CPU)}
    board_memory = {b.specs["memory_type"] for b in of(Cat.MOTHERBOARD)}
    board_m2_forms = {
        form for b in of(Cat.MOTHERBOARD) for slot in b.specs["m2_slots_details"] for form in slot["supported_form_factors"]
    }

    for cooler in of(Cat.COOLING):
        assert set(cooler.specs["supported_sockets"]) <= sockets | {"AM4", "AM5", "LGA1700", "LGA1851"}
        assert set(cooler.specs["supported_sockets"]) & sockets, cooler.name

    for ram in of(Cat.RAM):
        assert ram.specs["memory_type"] in board_memory, ram.name

    for drive in of(Cat.STORAGE):
        if drive.specs["interface"]["connection"] == "PCIe":
            assert drive.specs["form_factor"] in board_m2_forms, drive.name

    psu_native = Counter()
    for psu in of(Cat.PSU):
        for conn in psu.specs["power_connectors"]:
            if conn["native"]:
                psu_native[conn["type"]] = max(psu_native[conn["type"]], conn["quantity"])
    for gpu in of(Cat.GPU):
        for conn in gpu.specs["power_connectors_required"]:
            assert psu_native[conn["type"]] >= conn["quantity"], (gpu.name, conn)


@pytest.mark.parametrize("board", of(Cat.MOTHERBOARD), ids=lambda b: b.name)
def test_every_cpu_fits_boards_of_its_socket(board):
    service = CompatibilityService()
    for cpu in of(Cat.CPU):
        if cpu.specs["socket"] != board.specs["socket"]:
            continue
        result = service.evaluate({"cpu": [component(cpu)], "motherboard": [component(board)]})
        assert result.incompatible_count == 0, (cpu.name, [r.message for r in result.results])


BUILDS = {
    "AM5 gama alta": [
        "AMD Ryzen 7 9800X3D", "ASUS ROG STRIX X870E-E GAMING WIFI",
        "G.Skill Flare X5 DDR5 32GB (2x16GB) 6000MHz CL30 (F5-6000J3038F16GX2-FX5)",
        "NVIDIA GeForce RTX 5080 Founders Edition", "Corsair RM850x (2024) ATX 3.1",
        "ARCTIC Liquid Freezer III 360", "Samsung 990 PRO 2TB (MZ-V9P2T0BW)",
    ],
    "AM5 media con Radeon": [
        "AMD Ryzen 5 7600", "MSI PRO B650M-A WIFI",
        "Kingston FURY Beast DDR5 32GB (2x16GB) 6000MHz CL36 (KF560C36BBEK2-32)",
        "Sapphire PULSE AMD Radeon RX 9070 XT 16GB", "Seasonic FOCUS GX-850 ATX 3.1",
        "Thermalright Peerless Assassin 120 SE", "Crucial P3 Plus 1TB (CT1000P3PSSD8)",
    ],
    "AM4 económica": [
        "AMD Ryzen 5 5600", "ASRock B550M Pro4",
        "Corsair Vengeance LPX DDR4 16GB (2x8GB) 3200MHz CL16 (CMK16GX4M2B3200C16)",
        "AMD Radeon RX 7600", "Corsair CX650 (2023)", "DeepCool AK400",
        "Kingston NV3 1TB (SNV3S/1000G)", "Seagate BarraCuda 2TB (ST2000DM008)",
    ],
    "LGA1700 DDR4": [
        "Intel Core i5-13400F", "MSI PRO B760M-A WIFI DDR4",
        "Kingston FURY Beast DDR4 32GB (2x16GB) 3200MHz CL16 (KF432C16BBK2/32)",
        "NVIDIA GeForce RTX 4060 Founders Edition", "Thermaltake Smart BX1 650W",
        "be quiet! Pure Rock 2", "Crucial MX500 1TB (CT1000MX500SSD1)",
    ],
    "LGA1851 tope": [
        "Intel Core Ultra 9 285K", "MSI MAG Z890 TOMAHAWK WIFI",
        "Corsair Vengeance DDR5 64GB (2x32GB) 6000MHz CL30 (CMK64GX5M2B6000C30)",
        "NVIDIA GeForce RTX 5090 Founders Edition", "Corsair HX1500i (2025) ATX 3.1",
        "NZXT Kraken Elite 360", "Crucial T705 2TB (CT2000T705SSD3)",
    ],
}
ENGINE_KEYS = {
    Cat.CPU: "cpu", Cat.MOTHERBOARD: "motherboard", Cat.RAM: "ram", Cat.GPU: "gpu",
    Cat.PSU: "psu", Cat.COOLING: "cooling", Cat.STORAGE: "storage",
}


@pytest.mark.parametrize("names", BUILDS.values(), ids=BUILDS.keys())
def test_reference_builds_have_no_incompatibilities(names):
    components: dict[str, list] = {key: [] for key in ENGINE_KEYS.values()}
    for name in names:
        product = by_name(name)
        components[ENGINE_KEYS[product.category]].append(component(product))

    results = run_compatibility_rules(components)
    assert [r.message for r in results if r.status == "incompatible"] == []
    # Solo se tolera no poder comparar la capacidad térmica: muchos fabricantes
    # de disipadores no publican tdp_rating_w y la guía prohíbe inventarlo.
    undetermined = {r.rule_id for r in results if r.status == "indeterminate"}
    assert undetermined <= {"cpu_cooling_thermal_capacity"}


def test_seed_is_idempotent_and_keeps_stock():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    with sessionmaker(bind=engine)() as db:
        assert seed_products(db, CATALOG) == {"creados": len(CATALOG), "actualizados": 0, "no_elegibles": 0}

        from app.Models.product import Product
        first = db.query(Product).first()
        first.stock = 999
        db.commit()

        assert seed_products(db, CATALOG) == {"creados": 0, "actualizados": len(CATALOG), "no_elegibles": 0}
        db.refresh(first)
        assert first.stock == 999
        assert db.query(Product).count() == len(CATALOG)
