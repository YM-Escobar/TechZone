from typing import Any
from app.Services.product_eligibility.eligibility_helpers import is_positive_int,is_non_negative_int,is_non_empty_string,is_dict,is_list_of_dicts,has_required_keys,is_string_list



# ______________________ VALIDAR CPU _______________________

def validate_cpu_specs(specs: dict[str, Any]) -> bool:

    if not is_non_empty_string(specs.get("socket")):
        return False

    if not is_string_list(specs.get("supported_memory_types")):
        return False

    supported_memory_types = specs.get("supported_memory_types")

    if not is_string_list(supported_memory_types) or not supported_memory_types:
        return False

    if not is_positive_int(specs.get("max_memory_gb")):
        return False

    if not is_positive_int(specs.get("tdp_w")):
        return False
    
    #Todas las especificaciones obligatorias son válidas.
    return True

# ______________________ VALIDAR MOTHERBOARD _______________________

def validate_motherboard_specs(specs: dict[str, Any]) -> bool:

    if not is_non_empty_string(specs.get("socket")):
        return False

    if not is_non_empty_string(specs.get("memory_type")):
        return False

    if not is_positive_int(specs.get("max_memory_gb")):
        return False

    if not is_positive_int(specs.get("memory_slots")):
        return False

    if not is_non_negative_int(specs.get("sata_ports")):
        return False

    # Comprueba que exista una lista de procesadores soportados
    # y que no esté vacía.
    supported_cpus = specs.get("supported_cpu_models")

    if not is_list_of_dicts(supported_cpus) or not supported_cpus:
        return False

    # Cada procesador debe tener un modelo identificado.
    for cpu in supported_cpus:
        if not has_required_keys(cpu, {"model"}):
            return False

        # Si se proporciona una versión mínima de BIOS,
        # debe ser un texto no vacío.
        if "min_bios_version" in cpu:
            if not is_non_empty_string(cpu["min_bios_version"]):
                return False

    # Comprueba que exista una lista de ranuras PCIe.
    pcie_slots = specs.get("pcie_slots_details")

    if not is_list_of_dicts(pcie_slots):
        return False

    # Cada ranura PCIe debe describir su generación,
    # tamaño físico, líneas eléctricas y cantidad.
    for slot in pcie_slots:
        if not has_required_keys(
            slot,
            {"generation", "physical_size", "electrical_lanes", "quantity"}
        ):
            return False

        if not is_non_empty_string(slot["generation"]):
            return False

        if not is_non_empty_string(slot["physical_size"]):
            return False

        if not is_positive_int(slot["electrical_lanes"]):
            return False

        if not is_positive_int(slot["quantity"]):
            return False

    # Comprueba que exista una lista de ranuras M.2.
    m2_slots = specs.get("m2_slots_details")

    if not is_list_of_dicts(m2_slots):
        return False

    # Cada ranura M.2 debe indicar su interfaz y
    # los formatos físicos que admite.
    for slot in m2_slots:
        if not has_required_keys(
            slot,
            {"interface", "supported_form_factors"}
        ):
            return False

        if not is_non_empty_string(slot["interface"]):
            return False

        if not is_string_list(slot["supported_form_factors"]):
            return False

        if not slot["supported_form_factors"]:
            return False

        # Los recursos compartidos son opcionales.
        # Si existen, deben ser un diccionario.
        if "shared_resources" in slot:
            shared = slot["shared_resources"]

            if not is_dict(shared):
                return False

            # Si se declaran puertos SATA deshabilitados,
            # deben ser una lista de enteros no negativos.
            if "disabled_sata_ports" in shared:
                disabled_ports = shared["disabled_sata_ports"]

                if not isinstance(disabled_ports, list):
                    return False

                if not all(
                    is_non_negative_int(port)
                    for port in disabled_ports
                ):
                    return False

    # Todas las especificaciones obligatorias son válidas.
    return True

# ______________________ VALIDAR RAM _______________________

def validate_ram_specs(specs: dict[str, Any]) -> bool:
    
    if not is_non_empty_string(specs.get("memory_type")):
        return False
    
    if not is_positive_int(specs.get("capacity_per_module_gb")):
        return False
    
    if not is_positive_int(specs.get("total_capacity_gb")):
        return False
    
    if not is_positive_int(specs.get("module_count")):
        return False
    
    if not is_positive_int(specs.get("frequency_mhz")):
        return False
    
    if not is_non_empty_string(specs.get("form_factor")):
        return False
    
    #Si la capacidad total y (la capacidad por modulo multiplicado por la cantidad de modulos) no coincide devuelva false
    if specs["total_capacity_gb"] != (
        specs["capacity_per_module_gb"] * specs["module_count"]
    ):
        return False
    
        # Si se proporciona memory_profile, debe ser una lista de cadenas.
    if "memory_profile" in specs:
        memory_profile = specs["memory_profile"]

        if not isinstance(memory_profile, list):
            return False

        if not all(isinstance(profile, str) for profile in memory_profile):
            return False
    
    return True

# ______________________ VALIDAR GPU _______________________

def validate_gpu_specs(specs: dict[str, Any]) -> bool:

    interface = specs.get("interface")

    if not is_dict(interface):
        return False

    if not has_required_keys(
        interface,
        {"generation", "physical_size", "electrical_lanes"}
    ):
        return False

    if not is_non_empty_string(interface["generation"]):
        return False

    if not is_non_empty_string(interface["physical_size"]):
        return False

    if not is_positive_int(interface["electrical_lanes"]):
        return False

    if not is_positive_int(specs.get("vram_gb")):
        return False

    if not is_positive_int(specs.get("board_power_w")):
        return False

    if not is_positive_int(specs.get("recommended_psu_w")):
        return False

    power_connectors = specs.get("power_connectors_required")

    # Comprueba que sea una lista cuyos elementos sean diccionarios.
    # Se permite que esté vacía porque algunas GPU no necesitan
    # conectores de alimentación adicionales.
    if not is_list_of_dicts(power_connectors):
        return False

    # Recorre cada conector para validar su información.
    for connector in power_connectors:

        if not has_required_keys(connector, {"type", "quantity"}):
            return False

        if not is_non_empty_string(connector["type"]):
            return False

        if not is_positive_int(connector["quantity"]):
            return False

    return True

# ______________________ VALIDAR PSU _______________________

def validate_psu_specs(specs: dict[str, Any]) -> bool: 
    
    if not is_positive_int(specs.get("wattage_w")):
        return False
    
    connectors = specs.get("power_connectors")
    
    if not is_list_of_dicts(connectors):
        return False
    
    for conn in connectors:
        if not has_required_keys(
            conn,
            {"type","quantity","native"}
        ):
            return False
        
        if not is_non_empty_string(conn["type"]):
            return False
            
        if not is_positive_int(conn["quantity"]):
            return False
            
        if not isinstance(conn["native"], bool):
            return False
    
    return True
   
# ______________________ VALIDAR COOLING _______________________ 

def validate_cooling_specs(specs: dict[str, Any]) -> bool:

    if not is_non_empty_string(specs.get("cooling_type")):
        return False

    supported_sockets = specs.get("supported_sockets")

    if not is_string_list(supported_sockets) or not supported_sockets:
        return False

    if "tdp_rating_w" in specs:
        if not is_positive_int(specs["tdp_rating_w"]):
            return False

    return True
    
# ______________________ VALIDAR STORAGE _______________________ 

def validate_storage_specs(specs: dict[str, Any]) -> bool:

    if not is_non_empty_string(specs.get("storage_type")):
        return False

    if not is_positive_int(specs.get("capacity_gb")):
        return False

    interface = specs.get("interface")

    if not is_dict(interface):
        return False

    if not has_required_keys(interface, {"protocol", "connection"}):
        return False

    if not is_non_empty_string(interface["protocol"]):
        return False

    if not is_non_empty_string(interface["connection"]):
        return False

    if interface["connection"] == "PCIe":
        if not is_non_empty_string(interface.get("generation")):
            return False

    if not is_non_empty_string(specs.get("form_factor")):
        return False

    return True
    
    
