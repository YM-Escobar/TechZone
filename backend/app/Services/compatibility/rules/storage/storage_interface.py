
from typing import Any

from app.Services.compatibility.rule_result import RuleResult
from app.Services.compatibility.rules.storage.storage_helpers import (
    _get_m2_interface,
    _get_storage_connection_type,
    _is_non_empty_string,
    _is_non_negative_int,
)


def check_storage_motherboard_interface(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    connection_type = _get_storage_connection_type(storage_specs)

    if connection_type is None:
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="indeterminate",
            message=(
                "No se puede determinar una interfaz válida "
                "para el almacenamiento."
            ),
            components=["storage", "motherboard"],
        )

    if connection_type == "sata":
        sata_ports = motherboard_specs.get("sata_ports")

        if not _is_non_negative_int(sata_ports):
            return RuleResult(
                rule_id="storage_motherboard_interface",
                status="indeterminate",
                message="No hay información válida sobre los puertos SATA de la motherboard.",
                components=["storage", "motherboard"],
            )

        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="compatible",
            message="El almacenamiento utiliza una conexión SATA soportada por la motherboard.",
            components=["storage", "motherboard"],
        )

    m2_slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(m2_slots, list):
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="indeterminate",
            message="No hay información sobre las ranuras M.2 de la motherboard.",
            components=["storage", "motherboard"],
        )

    required_interface = _get_m2_interface(connection_type)
    valid_interfaces = []

    for slot in m2_slots:
        if not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")

        if _is_non_empty_string(slot_interface):
            valid_interfaces.append(slot_interface.strip().casefold())

    if not valid_interfaces:
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="indeterminate",
            message="No hay información válida sobre las interfaces de las ranuras M.2.",
            components=["storage", "motherboard"],
        )

    if required_interface not in valid_interfaces:
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="incompatible",
            message=(
                "La motherboard no declara ranuras M.2 con la interfaz "
                "necesaria para este almacenamiento."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_interface",
        status="compatible",
        message="La interfaz del almacenamiento es compatible con una interfaz M.2 declarada por la motherboard.",
        components=["storage", "motherboard"],
    )
