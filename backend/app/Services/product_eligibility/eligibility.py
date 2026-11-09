from typing import Any
from app.Models.product import ProductCategory
from app.Services.product_eligibility.eligibility_validators import validate_cpu_specs, validate_motherboard_specs,validate_ram_specs
from app.Services.product_eligibility.eligibility_validators import validate_gpu_specs, validate_psu_specs, validate_cooling_specs, validate_storage_specs
from app.Services.product_eligibility.eligibility_helpers import has_required_keys

#CAMPOS REQUERIDOS PARA QUE LA CATEGORIA PARTICIPE/SE PUEDA ELEGIR EN EL BUILDER 

REQUIRED_FIELDS = {
    ProductCategory.CPU:{
        "socket",
        "supported_memory_types",
        "max_memory_gb",
        "tdp_w"
    },
    ProductCategory.MOTHERBOARD:{
        "socket",
        "supported_cpu_models",
        "memory_type",
        "max_memory_gb",
        "memory_slots",
        "pcie_slots_details",
        "m2_slots_details",
        "sata_ports"
    },
    ProductCategory.RAM:{
        "memory_type",
        "capacity_per_module_gb",
        "total_capacity_gb",
        "module_count",
        "frequency_mhz",
        "form_factor"
    },
    ProductCategory.GPU:{
    "interface",
    "vram_gb",
    "board_power_w",
    "recommended_psu_w",
    "power_connectors_required"
    },
    ProductCategory.PSU:{
        "wattage_w",
        "power_connectors"
    },
    ProductCategory.COOLING:{
        "cooling_type",
        "supported_sockets"
    },
    ProductCategory.STORAGE:{
        "storage_type",
        "capacity_gb",
        "interface",
        "form_factor"
    } 
}

CATEGORY_VALIDATORS = {
    ProductCategory.CPU: validate_cpu_specs,
    ProductCategory.MOTHERBOARD: validate_motherboard_specs,
    ProductCategory.RAM: validate_ram_specs,
    ProductCategory.GPU: validate_gpu_specs,
    ProductCategory.PSU: validate_psu_specs,
    ProductCategory.COOLING: validate_cooling_specs,
    ProductCategory.STORAGE: validate_storage_specs
}

# Determina si un producto tiene las especificaciones necesarias para participar en el Builder.
def is_product_builder_eligible(
    category: ProductCategory,
    specs: dict[str, Any]
) -> bool:

    # Comprueba que la categoría tenga campos requeridos definidos.
    if category not in REQUIRED_FIELDS:
        return False

    # Comprueba que estén presentes todos los campos obligatorios.
    if not has_required_keys(
        specs,
        REQUIRED_FIELDS[category]
    ):
        return False

    # Obtiene el validador correspondiente a la categoría.
    validator = CATEGORY_VALIDATORS.get(category)

    # Comprueba que exista un validador para esa categoría.
    if validator is None:
        return False

    # Ejecuta el validador y devuelve su resultado.
    return validator(specs)


