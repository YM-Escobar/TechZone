
from app.Services.compatibility.engine import run_compatibility_rules


def test_engine_without_components_returns_empty_list():
    """Sin componentes seleccionados no debe ejecutar reglas."""
    results = run_compatibility_rules({})

    assert results == []


def test_engine_executes_cpu_motherboard_and_cooling_rules():
    """Ejecuta las reglas correspondientes a CPU, motherboard y cooling."""

    components = {
        "cpu": {
            "name": "AMD Ryzen 7 7800X3D",
            "specs": {
                "socket": "AM5",
                "tdp_w": 120,
                "supported_memory_types": ["DDR5"],
                "max_memory_gb": 128,
            },
        },
        "motherboard": {
            "name": "Motherboard AM5",
            "specs": {
                "socket": "AM5",
                "memory_type": "DDR5",
                "supported_cpu_models": [
                    {
                        "model": "AMD Ryzen 7 7800X3D",
                    }
                ],
            },
        },
        "cooling": {
            "name": "Liquid Cooling 240mm",
            "specs": {
                "supported_sockets": ["AM4", "AM5"],
                "tdp_rating_w": 180,
            },
        },
    }

    results = run_compatibility_rules(components)

    rule_ids = [result.rule_id for result in results]

    assert len(results) == 5

    assert "cpu_motherboard_socket" in rule_ids
    assert "cpu_motherboard_model" in rule_ids
    assert "cpu_motherboard_memory_type" in rule_ids
    assert "cpu_cooling_socket" in rule_ids
    assert "cpu_cooling_thermal_capacity" in rule_ids

    assert all(result.status == "compatible" for result in results)


def test_engine_accumulates_multiple_ram_kits():
    """Acumula capacidad y módulos cuando se seleccionan varios kits."""

    components = {
        "cpu": {
            "name": "CPU AM5",
            "specs": {
                "socket": "AM5",
                "tdp_w": 120,
                "supported_memory_types": ["DDR5"],
                "max_memory_gb": 128,
            },
        },
        "motherboard": {
            "name": "Motherboard AM5",
            "specs": {
                "socket": "AM5",
                "memory_type": "DDR5",
                "supported_cpu_models": [
                    {"model": "CPU AM5"}
                ],
                "max_memory_gb": 128,
                "memory_slots": 4,
            },
        },
        "ram": [
            {
                "name": "RAM DDR5 16GB",
                "quantity": 1,
                "specs": {
                    "memory_type": "DDR5",
                    "total_capacity_gb": 16,
                    "module_count": 2,
                },
            },
            {
                "name": "RAM DDR5 32GB",
                "quantity": 1,
                "specs": {
                    "memory_type": "DDR5",
                    "total_capacity_gb": 32,
                    "module_count": 2,
                },
            },
        ],
    }

    results = run_compatibility_rules(components)

    rule_results = {
        result.rule_id: result
        for result in results
    }

    assert rule_results["ram_motherboard_capacity"].status == "compatible"
    assert rule_results["ram_motherboard_slots"].status == "compatible"
    assert rule_results["ram_cpu_capacity"].status == "compatible"


def test_engine_detects_excessive_ram_capacity():
    """Detecta cuando la capacidad acumulada supera el límite de la CPU."""

    components = {
        "cpu": {
            "name": "CPU AM5",
            "specs": {
                "socket": "AM5",
                "tdp_w": 120,
                "supported_memory_types": ["DDR5"],
                "max_memory_gb": 32,
            },
        },
        "motherboard": {
            "name": "Motherboard AM5",
            "specs": {
                "socket": "AM5",
                "memory_type": "DDR5",
                "supported_cpu_models": [
                    {"model": "CPU AM5"}
                ],
                "max_memory_gb": 128,
                "memory_slots": 4,
            },
        },
        "ram": [
            {
                "name": "RAM DDR5 32GB",
                "quantity": 2,
                "specs": {
                    "memory_type": "DDR5",
                    "total_capacity_gb": 32,
                    "module_count": 2,
                },
            },
        ],
    }

    results = run_compatibility_rules(components)

    rule_results = {
        result.rule_id: result
        for result in results
    }

    assert rule_results["ram_cpu_capacity"].status == "incompatible"
    assert rule_results["ram_motherboard_capacity"].status == "compatible"
