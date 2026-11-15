from typing import Any


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

    Cada registro representa un grupo de ranuras equivalentes.
    El índice puede aparecer varias veces en occupied_indexes,
    una por cada ranura ocupada dentro del grupo.
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
        if not isinstance(slot, dict):
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

        if occupied_indexes.count(index) >= quantity:
            continue

        return index

    return None

