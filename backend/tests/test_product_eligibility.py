# Importa la función que determina si un producto puede participar en el Builder.
from app.Services.product_eligibility.eligibility import (
    is_product_builder_eligible,
)

# Importa las categorías definidas en el modelo Product.
from app.Models.product import ProductCategory



# ============================================================
# CPU
# ============================================================

# Comprueba que una CPU con especificaciones válidas sea elegible.
def test_cpu_with_valid_specs_is_eligible():
    specs = {
        "socket": "AM5",
        "supported_memory_types": ["DDR5"],
        "max_memory_gb": 192,
        "tdp_w": 120,
    }

    assert is_product_builder_eligible(
        ProductCategory.CPU, specs
    ) is True


# Comprueba que una CPU sin socket no sea elegible.
def test_cpu_with_missing_required_field_is_not_eligible():
    specs = {
        "supported_memory_types": ["DDR5"],
        "max_memory_gb": 192,
        "tdp_w": 120,
    }

    assert is_product_builder_eligible(
        ProductCategory.CPU, specs
    ) is False


# ============================================================
# MOTHERBOARD
# ============================================================

# Comprueba que una motherboard con especificaciones válidas sea elegible.
def test_motherboard_with_valid_specs_is_eligible():
    specs = {
        "socket": "AM5",
        "chipset": "B650",
        "supported_cpu_models": [
            {"model": "Ryzen 5 7600"}
        ],
        "memory_type": "DDR5",
        "max_memory_gb": 192,
        "memory_slots": 4,
        "form_factor": "ATX",
        "sata_ports": 4,
        "pcie_slots_details": [],
        "m2_slots_details": [],
    }

    assert is_product_builder_eligible(
        ProductCategory.MOTHERBOARD, specs
    ) is True


# Comprueba que una motherboard sin socket no sea elegible.
def test_motherboard_with_missing_required_field_is_not_eligible():
    specs = {
        "chipset": "B650",
        "supported_cpu_models": [
            {"model": "Ryzen 5 7600"}
        ],
        "memory_type": "DDR5",
        "max_memory_gb": 192,
        "memory_slots": 4,
        "form_factor": "ATX",
        "sata_ports": 4,
        "pcie_slots_details": [],
        "m2_slots_details": [],
    }

    assert is_product_builder_eligible(
        ProductCategory.MOTHERBOARD, specs
    ) is False


# ============================================================
# RAM
# ============================================================

# Comprueba que una memoria RAM con especificaciones válidas sea elegible.
def test_ram_with_valid_specs_is_eligible():
    specs = {
        "memory_type": "DDR5",
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 32,
        "module_count": 2,
        "frequency_mhz": 6000,
        "cas_latency_cl": 30,
        "form_factor": "DIMM",
        "memory_profile": ["EXPO"],
    }

    assert is_product_builder_eligible(
        ProductCategory.RAM, specs
    ) is True


# Comprueba que una memoria RAM sin tipo de memoria no sea elegible.
def test_ram_with_missing_required_field_is_not_eligible():
    specs = {
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 32,
        "module_count": 2,
        "frequency_mhz": 6000,
        "cas_latency_cl": 30,
        "form_factor": "DIMM",
    }

    assert is_product_builder_eligible(
        ProductCategory.RAM, specs
    ) is False


# ============================================================
# GPU
# ============================================================

# Comprueba que una GPU con especificaciones válidas sea elegible.
def test_gpu_with_valid_specs_is_eligible():
    specs = {
        "interface": {
            "generation": "4.0",
            "physical_size": "x16",
            "electrical_lanes": 16,
        },
        "vram_gb": 12,
        "board_power_w": 250,
        "recommended_psu_w": 650,
        "power_connectors_required": [
            {"type": "8-pin PCIe", "quantity": 2}
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.GPU, specs
    ) is True


# Comprueba que una GPU sin interfaz PCIe no sea elegible.
def test_gpu_with_missing_required_field_is_not_eligible():
    specs = {
        "vram_gb": 12,
        "board_power_w": 250,
        "recommended_psu_w": 650,
        "power_connectors_required": [
            {"type": "8-pin PCIe", "quantity": 2}
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.GPU, specs
    ) is False


# ============================================================
# PSU (FUENTE DE PODER)
# ============================================================

# Comprueba que una fuente de poder con especificaciones válidas sea elegible.
def test_psu_with_valid_specs_is_eligible():
    specs = {
        "wattage_w": 750,
        "certification": "80 Plus Gold",
        "power_connectors": [
            {
                "type": "8-pin PCIe",
                "quantity": 2,
                "native": True,
            }
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.PSU, specs
    ) is True


# Comprueba que una fuente sin potencia no sea elegible.
def test_psu_with_missing_required_field_is_not_eligible():
    specs = {
        "certification": "80 Plus Gold",
        "power_connectors": [],
    }

    assert is_product_builder_eligible(
        ProductCategory.PSU, specs
    ) is False


# ============================================================
# COOLING (REFRIGERACIÓN)
# ============================================================

# Comprueba que un sistema de refrigeración válido sea elegible.
def test_cooling_with_valid_specs_is_eligible():
    specs = {
        "cooling_type": "AIO",
        "supported_sockets": ["AM5", "AM4"],
        "radiator_size_mm": 240,
        "tdp_rating_w": 250,
    }

    assert is_product_builder_eligible(
        ProductCategory.COOLING, specs
    ) is True


# Comprueba que un sistema de refrigeración sin sockets compatibles
# declarados no sea elegible.
def test_cooling_with_missing_required_field_is_not_eligible():
    specs = {
        "cooling_type": "AIO",
        "radiator_size_mm": 240,
        "tdp_rating_w": 250,
    }

    assert is_product_builder_eligible(
        ProductCategory.COOLING, specs
    ) is False


# ============================================================
# STORAGE (ALMACENAMIENTO)
# ============================================================

# Comprueba que una unidad de almacenamiento válida sea elegible.
def test_storage_with_valid_specs_is_eligible():
    specs = {
        "storage_type": "SSD",
        "capacity_gb": 1000,
        "interface": {
            "protocol": "NVMe",
            "connection": "PCIe",
            "generation": "4.0",
        },
        "form_factor": "M.2 2280",
    }

    assert is_product_builder_eligible(
        ProductCategory.STORAGE, specs
    ) is True


# Comprueba que una unidad de almacenamiento sin interfaz
# no sea elegible.
def test_storage_with_missing_required_field_is_not_eligible():
    specs = {
        "storage_type": "SSD",
        "capacity_gb": 1000,
        "form_factor": "M.2 2280",
    }

    assert is_product_builder_eligible(
        ProductCategory.STORAGE, specs
    ) is False



# ============================================================
# PRUEBAS DE VALORES INVÁLIDOS
# ============================================================

# CPU: comprueba que no se acepte una memoria máxima negativa.
def test_cpu_with_invalid_max_memory_is_not_eligible():
    specs = {
        "socket": "AM5",
        "supported_memory_types": ["DDR5"],
        "max_memory_gb": -1,
        "tdp_w": 120,
    }

    assert is_product_builder_eligible(
        ProductCategory.CPU, specs
    ) is False


# MOTHERBOARD: comprueba que no se acepte una cantidad negativa
# de ranuras de memoria.
def test_motherboard_with_invalid_memory_slots_is_not_eligible():
    specs = {
        "socket": "AM5",
        "chipset": "B650",
        "supported_cpu_models": [
            {"model": "Ryzen 5 7600"}
        ],
        "memory_type": "DDR5",
        "max_memory_gb": 192,
        "memory_slots": -1,
        "form_factor": "ATX",
        "sata_ports": 4,
        "pcie_slots_details": [],
        "m2_slots_details": [],
    }

    assert is_product_builder_eligible(
        ProductCategory.MOTHERBOARD, specs
    ) is False


# RAM: comprueba que la capacidad total coincida
# con la capacidad por módulo multiplicada por su cantidad.
def test_ram_with_inconsistent_total_capacity_is_not_eligible():
    specs = {
        "memory_type": "DDR5",
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 64,
        "module_count": 2,
        "frequency_mhz": 6000,
        "cas_latency_cl": 30,
        "form_factor": "DIMM",
        "memory_profile": ["EXPO"],
    }

    assert is_product_builder_eligible(
        ProductCategory.RAM, specs
    ) is False


# GPU: comprueba que interface deba ser un objeto
# y no una cadena de texto.
def test_gpu_with_invalid_interface_type_is_not_eligible():
    specs = {
        "interface": "PCIe 4.0 x16",
        "vram_gb": 12,
        "board_power_w": 250,
        "recommended_psu_w": 650,
        "power_connectors_required": [
            {"type": "8-pin PCIe", "quantity": 2}
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.GPU, specs
    ) is False


# PSU: comprueba que native deba ser un booleano.
def test_psu_with_invalid_native_type_is_not_eligible():
    specs = {
        "wattage_w": 750,
        "certification": "80 Plus Gold",
        "power_connectors": [
            {
                "type": "8-pin PCIe",
                "quantity": 2,
                "native": "yes",
            }
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.PSU, specs
    ) is False


# COOLING: comprueba que supported_sockets
# contenga una lista de cadenas y no una cadena individual.
def test_cooling_with_invalid_supported_sockets_is_not_eligible():
    specs = {
        "cooling_type": "AIO",
        "supported_sockets": "AM5",
        "radiator_size_mm": 240,
        "tdp_rating_w": 250,
    }

    assert is_product_builder_eligible(
        ProductCategory.COOLING, specs
    ) is False


# STORAGE: comprueba que capacity_gb sea un entero positivo.
def test_storage_with_invalid_capacity_is_not_eligible():
    specs = {
        "storage_type": "SSD",
        "capacity_gb": -500,
        "interface": {
            "protocol": "NVMe",
            "connection": "PCIe",
            "generation": "4.0",
        },
        "form_factor": "M.2 2280",
    }

    assert is_product_builder_eligible(
        ProductCategory.STORAGE, specs
    ) is False


# ============================================================
# PRUEBAS DE ESTRUCTURAS ANIDADAS
# ============================================================

# CPU: los tipos de memoria soportados deben ser una lista de cadenas.
def test_cpu_with_invalid_memory_types_is_not_eligible():
    specs = {
        "socket": "AM5",
        "supported_memory_types": ["DDR5", 123],
        "max_memory_gb": 192,
        "tdp_w": 120,
    }

    assert is_product_builder_eligible(
        ProductCategory.CPU, specs
    ) is False


# MOTHERBOARD: cada modelo de CPU soportado debe ser un objeto
# que contenga el campo model.
def test_motherboard_with_invalid_cpu_model_is_not_eligible():
    specs = {
        "socket": "AM5",
        "chipset": "B650",
        "supported_cpu_models": [
            {"min_bios_version": "1.0"}
        ],
        "memory_type": "DDR5",
        "max_memory_gb": 192,
        "memory_slots": 4,
        "form_factor": "ATX",
        "sata_ports": 4,
        "pcie_slots_details": [],
        "m2_slots_details": [],
    }

    assert is_product_builder_eligible(
        ProductCategory.MOTHERBOARD, specs
    ) is False


# RAM: memory_profile debe contener una lista de cadenas.
def test_ram_with_invalid_memory_profile_is_not_eligible():
    specs = {
        "memory_type": "DDR5",
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 32,
        "module_count": 2,
        "frequency_mhz": 6000,
        "cas_latency_cl": 30,
        "form_factor": "DIMM",
        "memory_profile": ["EXPO", 123],
    }

    assert is_product_builder_eligible(
        ProductCategory.RAM, specs
    ) is False


# GPU: cada conector debe contener type y quantity válidos.
def test_gpu_with_invalid_power_connector_is_not_eligible():
    specs = {
        "interface": {
            "generation": "4.0",
            "physical_size": "x16",
            "electrical_lanes": 16,
        },
        "vram_gb": 12,
        "board_power_w": 250,
        "recommended_psu_w": 650,
        "power_connectors_required": [
            {"type": "8-pin PCIe", "quantity": -1}
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.GPU, specs
    ) is False


# PSU: cada conector debe tener una cantidad positiva.
def test_psu_with_invalid_power_connector_is_not_eligible():
    specs = {
        "wattage_w": 750,
        "certification": "80 Plus Gold",
        "power_connectors": [
            {
                "type": "8-pin PCIe",
                "quantity": 0,
                "native": True,
            }
        ],
    }

    assert is_product_builder_eligible(
        ProductCategory.PSU, specs
    ) is False


# COOLING: supported_sockets no debe contener valores vacíos.
def test_cooling_with_empty_socket_is_not_eligible():
    specs = {
        "cooling_type": "AIO",
        "supported_sockets": ["AM5", ""],
        "radiator_size_mm": 240,
        "tdp_rating_w": 250,
    }

    assert is_product_builder_eligible(
        ProductCategory.COOLING, specs
    ) is False


# STORAGE: interface debe contener los campos internos válidos.
def test_storage_with_invalid_interface_is_not_eligible():
    specs = {
        "storage_type": "SSD",
        "capacity_gb": 1000,
        "interface": {
            "protocol": "NVMe",
            "connection": "PCIe",
        },
        "form_factor": "M.2 2280",
    }

    assert is_product_builder_eligible(
        ProductCategory.STORAGE, specs
    ) is False
