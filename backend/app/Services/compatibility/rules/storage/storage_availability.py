
from typing import Any

from app.Services.compatibility.rule_result import RuleResult
from app.Services.compatibility.rules.storage.storage_helpers import (
    _get_m2_interface,
    _get_storage_connection_type,
    _is_positive_int,
    _is_non_empty_string,
    _is_non_negative_int,
)


def _validate_occupied_m2_indexes(
    occupied_indexes: list[int],
) -> bool:
    return (
        isinstance(occupied_indexes, list)
        and all(
            isinstance(index, int)
            and not isinstance(index, bool)
            and index >= 0
            for index in occupied_indexes
        )
    )


def _get_disabled_sata_ports(
    motherboard_specs: dict[str, Any],
    occupied_indexes: list[int],
    sata_ports: int,
) -> tuple[set[int] | None, str | None]:
    m2_slots = motherboard_specs.get("m2_slots_details", [])

    if not isinstance(m2_slots, list):
        return None, "No se puede comprobar si las ranuras M.2 deshabilitan puertos SATA."

    disabled_ports = set()

    for index in set(occupied_indexes):
        if index >= len(m2_slots):
            return None, "Se indicó una ranura M.2 ocupada que no existe en la motherboard."

        slot = m2_slots[index]

        if not isinstance(slot, dict):
            return None, "La información de una ranura M.2 ocupada no es válida."

        shared_resources = slot.get("shared_resources", {})

        if shared_resources is None:
            continue

        if not isinstance(shared_resources, dict):
            return None, "La información de recursos compartidos de una ranura M.2 no es válida."

        ports = shared_resources.get("disabled_sata_ports", [])

        if not isinstance(ports, list):
            return None, "La lista de puertos SATA deshabilitados no es válida."

        for port in ports:
            if not _is_positive_int(port) or port > sata_ports:
                return None, "La motherboard contiene números de puertos SATA deshabilitados inválidos."

            disabled_ports.add(port)

    return disabled_ports, None


def _check_sata_availability(
    motherboard_specs: dict[str, Any],
    storage_quantity: int,
    occupied_indexes: list[int],
) -> RuleResult:
    sata_ports = motherboard_specs.get("sata_ports")

    if not _is_non_negative_int(sata_ports):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No hay información válida sobre la cantidad de puertos SATA.",
            components=["storage", "motherboard"],
        )

    disabled_ports, error = _get_disabled_sata_ports(
        motherboard_specs,
        occupied_indexes,
        sata_ports,
    )

    if error is not None:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message=error,
            components=["storage", "motherboard"],
        )

    available_ports = sata_ports - len(disabled_ports)

    if available_ports < storage_quantity:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="incompatible",
            message=(
                f"No hay suficientes puertos SATA disponibles. "
                f"Disponibles: {available_ports}; "
                f"necesarios: {storage_quantity}."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_connection_availability",
        status="compatible",
        message=f"Hay {available_ports} puertos SATA disponibles.",
        components=["storage", "motherboard"],
    )


def _get_available_m2_slots(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    occupied_indexes: list[int],
) -> int | None:
    m2_slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(m2_slots, list):
        return None

    connection_type = _get_storage_connection_type(storage_specs)
    required_interface = _get_m2_interface(connection_type)
    storage_form_factor = storage_specs.get("form_factor")

    if not _is_non_empty_string(storage_form_factor):
        return None

    available_slots = 0

    for index, slot in enumerate(m2_slots):
        if not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")
        supported_form_factors = slot.get("supported_form_factors")
        quantity = slot.get("quantity")

        if not _is_non_empty_string(slot_interface):
            continue

        if slot_interface.strip().casefold() != required_interface:
            continue

        if not isinstance(supported_form_factors, list):
            continue

        if not any(
            _is_non_empty_string(form_factor)
            and form_factor.strip().casefold() == storage_form_factor.strip().casefold()
            for form_factor in supported_form_factors
        ):
            continue

        if not _is_positive_int(quantity):
            continue

        occupied_quantity = occupied_indexes.count(index)
        available_slots += max(quantity - occupied_quantity, 0)

    return available_slots


def _check_m2_availability(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    storage_quantity: int,
    occupied_indexes: list[int],
) -> RuleResult:
    if not isinstance(motherboard_specs.get("m2_slots_details"), list):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No hay información sobre las ranuras M.2 de la motherboard.",
            components=["storage", "motherboard"],
        )

    if not _is_non_empty_string(storage_specs.get("form_factor")):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No se conoce el factor de forma del almacenamiento M.2.",
            components=["storage", "motherboard"],
        )

    available_slots = _get_available_m2_slots(
        storage_specs,
        motherboard_specs,
        occupied_indexes,
    )

    if available_slots is None:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No se pudo determinar la disponibilidad de las ranuras M.2.",
            components=["storage", "motherboard"],
        )

    if available_slots < storage_quantity:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="incompatible",
            message=(
                f"No hay suficientes ranuras M.2 disponibles para este "
                f"almacenamiento. Disponibles: {available_slots}; "
                f"necesarias: {storage_quantity}."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_connection_availability",
        status="compatible",
        message=f"Hay {available_slots} ranuras M.2 adecuadas disponibles.",
        components=["storage", "motherboard"],
    )


def check_storage_motherboard_connection_availability(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    storage_quantity: int = 1,
    occupied_m2_slot_indexes: list[int] | None = None,
) -> RuleResult:
    if not _is_positive_int(storage_quantity):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="La cantidad de unidades de almacenamiento no es válida.",
            components=["storage", "motherboard"],
        )

    if occupied_m2_slot_indexes is None:
        occupied_m2_slot_indexes = []

    if not _validate_occupied_m2_indexes(occupied_m2_slot_indexes):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="La información sobre las ranuras M.2 ocupadas no es válida.",
            components=["storage", "motherboard"],
        )

    connection_type = _get_storage_connection_type(storage_specs)

    if connection_type is None:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No se puede determinar qué conexión necesita el almacenamiento.",
            components=["storage", "motherboard"],
        )

    if connection_type == "sata":
        return _check_sata_availability(
            motherboard_specs,
            storage_quantity,
            occupied_m2_slot_indexes,
        )

    return _check_m2_availability(
        storage_specs,
        motherboard_specs,
        storage_quantity,
        occupied_m2_slot_indexes,
    )
