
from typing import Any

from app.Services.compatibility.rule_result import RuleResult

# Reglas de CPU y motherboard.
from app.Services.compatibility.rules.motherboard.cpu_motherboard import (
    check_cpu_motherboard_socket,
    check_cpu_motherboard_model,
    check_cpu_motherboard_memory_type,
)

# Reglas de RAM.
from app.Services.compatibility.rules.ram.ram_motherboard import (
    check_ram_motherboard_memory_type,
    check_ram_motherboard_capacity,
    check_ram_motherboard_slots,
)
from app.Services.compatibility.rules.ram.ram_cpu import (
    check_ram_cpu_capacity,
)

# Reglas de GPU.
from app.Services.compatibility.rules.gpu.gpu_motherboard import (
    check_gpu_motherboard_pcie_interface,
    check_gpu_motherboard_pcie_generation,
)
from app.Services.compatibility.rules.gpu.gpu_psu import (
    check_gpu_psu_wattage,
    check_gpu_psu_connectors,
)

# Reglas de CPU y refrigeración.
from app.Services.compatibility.rules.cpu.cpu_cooling import (
    check_cpu_cooling_socket,
    check_cpu_cooling_thermal_capacity,
)

# Reglas de almacenamiento.
from app.Services.compatibility.rules.storage.storage_motherboard import (
    check_storage_motherboard_interface,
    check_storage_motherboard_form_factor,
    check_storage_motherboard_connection_availability,
)


def _normalize_entries(value: Any) -> list[dict[str, Any]]:
    """
    Normaliza un componente individual o una lista de componentes.

    Permite recibir:
    - Un diccionario para componentes individuales.
    - Una lista de diccionarios para componentes múltiples.
    """
    if isinstance(value, dict):
        return [value]

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    return []


def _get_specs(component: dict[str, Any]) -> dict[str, Any]:
    """Obtiene las especificaciones técnicas de un componente."""
    specs = component.get("specs")

    if not isinstance(specs, dict):
        return {}

    return specs


def _get_quantity(component: dict[str, Any]) -> int:
    """Obtiene la cantidad de unidades de un componente."""
    quantity = component.get("quantity", 1)

    if (
        not isinstance(quantity, int)
        or isinstance(quantity, bool)
        or quantity <= 0
    ):
        return 0

    return quantity


def _get_component_name(component: dict[str, Any]) -> str:
    """Obtiene el nombre de un componente para las reglas que lo necesitan."""
    name = component.get("name")

    if isinstance(name, str) and name.strip():
        return name.strip()

    return ""


def _build_ram_aggregate(
    ram_components: list[dict[str, Any]],
) -> dict[str, Any] | None:
    """
    Acumula la capacidad total y la cantidad de módulos de todos
    los kits de RAM seleccionados.

    Esto permite evaluar varios modelos de RAM sin limitarse
    a multiplicar un único kit.
    """
    total_capacity = 0
    total_modules = 0

    for component in ram_components:
        specs = _get_specs(component)
        quantity = _get_quantity(component)

        if quantity == 0:
            return None

        capacity = specs.get("total_capacity_gb")
        module_count = specs.get("module_count")

        if (
            not isinstance(capacity, int)
            or isinstance(capacity, bool)
            or capacity <= 0
            or not isinstance(module_count, int)
            or isinstance(module_count, bool)
            or module_count <= 0
        ):
            return None

        total_capacity += capacity * quantity
        total_modules += module_count * quantity

    if total_capacity <= 0 or total_modules <= 0:
        return None

    return {
        "total_capacity_gb": total_capacity,
        "module_count": total_modules,
    }


def _find_storage_slot_index(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    occupied_indexes: list[int],
) -> int | None:
    """
    Encuentra una ranura M.2 adecuada para reservarla después
    de comprobar que el almacenamiento puede utilizarla.

    La cantidad de ranuras indicada en cada registro se considera
    un grupo de ranuras equivalentes. Al reservar su índice,
    se reserva ese grupo completo.
    """
    interface = storage_specs.get("interface")

    if not isinstance(interface, dict):
        return None

    protocol = interface.get("protocol")
    connection = interface.get("connection")
    form_factor = storage_specs.get("form_factor")

    if not isinstance(protocol, str) or not isinstance(connection, str):
        return None

    if not isinstance(form_factor, str):
        return None

    protocol = protocol.strip().casefold()
    connection = connection.strip().casefold()

    if protocol == "nvme" and connection == "pcie":
        required_interface = "pcie"
    elif protocol == "sata" and connection == "m.2":
        required_interface = "sata"
    else:
        # El almacenamiento SATA convencional no ocupa una ranura M.2.
        return None

    slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(slots, list):
        return None

    for index, slot in enumerate(slots):
        if index in occupied_indexes or not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")
        supported_form_factors = slot.get("supported_form_factors")
        quantity = slot.get("quantity")

        if not isinstance(slot_interface, str):
            continue

        if slot_interface.strip().casefold() != required_interface:
            continue

        if not isinstance(supported_form_factors, list):
            continue

        if not any(
            isinstance(item, str)
            and item.strip().casefold() == form_factor.strip().casefold()
            for item in supported_form_factors
        ):
            continue

        if (
            not isinstance(quantity, int)
            or isinstance(quantity, bool)
            or quantity <= 0
        ):
            continue

        return index

    return None


def run_compatibility_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    """
    Ejecuta todas las reglas de compatibilidad correspondientes
    a los componentes seleccionados.

    El Engine no consulta la base de datos ni consolida el
    diagnóstico global. Únicamente coordina las reglas y
    devuelve sus resultados individuales.
    """
    results: list[RuleResult] = []

    # Obtener los componentes individuales.
    cpu_components = _normalize_entries(components.get("cpu"))
    motherboard_components = _normalize_entries(
        components.get("motherboard")
    )
    psu_components = _normalize_entries(components.get("psu"))
    cooling_components = _normalize_entries(components.get("cooling"))

    # Obtener las listas de componentes múltiples.
    ram_components = _normalize_entries(components.get("ram"))
    gpu_components = _normalize_entries(components.get("gpu"))
    storage_components = _normalize_entries(components.get("storage"))

    # En esta primera versión se trabaja con una CPU y una motherboard.
    cpu = cpu_components[0] if cpu_components else None
    motherboard = (
        motherboard_components[0]
        if motherboard_components
        else None
    )
    psu = psu_components[0] if psu_components else None
    cooling = cooling_components[0] if cooling_components else None

    cpu_specs = _get_specs(cpu) if cpu else None
    motherboard_specs = (
        _get_specs(motherboard) if motherboard else None
    )
    psu_specs = _get_specs(psu) if psu else None
    cooling_specs = _get_specs(cooling) if cooling else None

    # ========================================================
    # 1. CPU + MOTHERBOARD
    # ========================================================

    if cpu and motherboard:
        cpu_model = _get_component_name(cpu)

        results.append(
            check_cpu_motherboard_socket(
                cpu_specs,
                motherboard_specs,
            )
        )

        results.append(
            check_cpu_motherboard_model(
                cpu_model,
                motherboard_specs,
            )
        )

        results.append(
            check_cpu_motherboard_memory_type(
                cpu_specs,
                motherboard_specs,
            )
        )

    # ========================================================
    # 2. RAM + MOTHERBOARD + CPU
    # ========================================================

    if ram_components:
        # Cada kit se compara individualmente por tipo de memoria.
        if motherboard:
            for ram in ram_components:
                results.append(
                    check_ram_motherboard_memory_type(
                        _get_specs(ram),
                        motherboard_specs,
                    )
                )

        # Capacidad y cantidad de módulos se acumulan entre kits.
        ram_aggregate = _build_ram_aggregate(ram_components)

        if ram_aggregate is not None:
            if motherboard:
                results.append(
                    check_ram_motherboard_capacity(
                        ram_aggregate,
                        motherboard_specs,
                    )
                )

                results.append(
                    check_ram_motherboard_slots(
                        ram_aggregate,
                        motherboard_specs,
                    )
                )

            if cpu:
                results.append(
                    check_ram_cpu_capacity(
                        ram_aggregate,
                        cpu_specs,
                    )
                )

    # ========================================================
    # 3. GPU + MOTHERBOARD + PSU
    # ========================================================

    for gpu in gpu_components:
        gpu_specs = _get_specs(gpu)

        if motherboard:
            results.append(
                check_gpu_motherboard_pcie_interface(
                    gpu_specs,
                    motherboard_specs,
                )
            )

            results.append(
                check_gpu_motherboard_pcie_generation(
                    gpu_specs,
                    motherboard_specs,
                )
            )

        if psu:
            results.append(
                check_gpu_psu_wattage(
                    gpu_specs,
                    psu_specs,
                )
            )

            results.append(
                check_gpu_psu_connectors(
                    gpu_specs,
                    psu_specs,
                )
            )

    # ========================================================
    # 4. CPU + REFRIGERACIÓN
    # ========================================================

    if cpu and cooling:
        results.append(
            check_cpu_cooling_socket(
                cpu_specs,
                cooling_specs,
            )
        )

        results.append(
            check_cpu_cooling_thermal_capacity(
                cpu_specs,
                cooling_specs,
            )
        )

    # ========================================================
    # 5. STORAGE + MOTHERBOARD
    # ========================================================

    if motherboard:
        occupied_m2_indexes: list[int] = []

        for storage in storage_components:
            storage_specs = _get_specs(storage)
            storage_quantity = _get_quantity(storage)

            results.append(
                check_storage_motherboard_interface(
                    storage_specs,
                    motherboard_specs,
                )
            )

            results.append(
                check_storage_motherboard_form_factor(
                    storage_specs,
                    motherboard_specs,
                )
            )

            availability_result = (
                check_storage_motherboard_connection_availability(
                    storage_specs,
                    motherboard_specs,
                    storage_quantity=storage_quantity,
                    occupied_m2_slot_indexes=occupied_m2_indexes,
                )
            )

            results.append(availability_result)

            # Reservar la ranura M.2 cuando la disponibilidad
            # se haya confirmado.
            if availability_result.status == "compatible":
                slot_index = _find_storage_slot_index(
                    storage_specs,
                    motherboard_specs,
                    occupied_m2_indexes,
                )

                if (
                    slot_index is not None
                    and slot_index not in occupied_m2_indexes
                ):
                    occupied_m2_indexes.append(slot_index)

    return results
