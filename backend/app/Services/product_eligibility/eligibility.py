from typing import Any
from app.Models.product import ProductCategory


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

