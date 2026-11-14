
from typing import Any

from app.Services.compatibility.rule_result import RuleResult
from app.Services.compatibility.rules.storage.storage_helpers import (
    _get_m2_interface,
    _get_storage_connection_type,
    _is_non_empty_string,
)


def check_storage_motherboard_form_factor(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    connection_type = _get_storage_connection_type(storage_specs)

    if connection_type is None:
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No se puede determinar el tipo de conexión del almacenamiento.",
            components=["storage", "motherboard"],
        )

    if connection_type == "sata":
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="compatible",
            message="El almacenamiento SATA convencional no requiere una ranura M.2.",
            components=["storage", "motherboard"],
        )

    storage_form_factor = storage_specs.get("form_factor")

    if not _is_non_empty_string(storage_form_factor):
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No se conoce el factor de forma del almacenamiento M.2.",
            components=["storage", "motherboard"],
        )

    m2_slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(m2_slots, list):
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No hay información sobre las ranuras M.2 de la motherboard.",
            components=["storage", "motherboard"],
        )

    required_interface = _get_m2_interface(connection_type)
    valid_form_factors = []

    for slot in m2_slots:
        if not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")
        supported_form_factors = slot.get("supported_form_factors")

        if not _is_non_empty_string(slot_interface):
            continue

        if slot_interface.strip().casefold() != required_interface:
            continue

        if not isinstance(supported_form_factors, list):
            continue

        for form_factor in supported_form_factors:
            if _is_non_empty_string(form_factor):
                valid_form_factors.append(form_factor.strip().casefold())

    if not valid_form_factors:
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No hay información válida sobre los factores de forma soportados por las ranuras M.2 adecuadas.",
            components=["storage", "motherboard"],
        )

    if storage_form_factor.strip().casefold() not in valid_form_factors:
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="incompatible",
            message=(
                f"La motherboard no declara soporte para el factor de forma "
                f"{storage_form_factor.strip()}."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_form_factor",
        status="compatible",
        message=(
            f"La motherboard declara soporte para el factor de forma "
            f"{storage_form_factor.strip()}."
        ),
        components=["storage", "motherboard"],
    )
