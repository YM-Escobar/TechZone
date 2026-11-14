
from typing import Any

from app.Services.compatibility.rule_result import RuleResult

# Reglas de almacenamiento.
from app.Services.compatibility.rules.storage.storage_motherboard import (
    _get_storage_connection_type,
    check_storage_motherboard_interface,
    check_storage_motherboard_form_factor,
    check_storage_motherboard_connection_availability,
)
from app.Services.compatibility.processors.aggregates import _find_storage_slot_index, _get_quantity, _get_specs
from app.Services.compatibility.processors.normalization import _normalize_entries

def run_storage_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    results: list[RuleResult] = []

    motherboard_components = _normalize_entries(
        components.get("motherboard")
    )
    storage_components = _normalize_entries(components.get("storage"))

    motherboard = motherboard_components[0] if motherboard_components else None

    if motherboard:
        motherboard_specs = _get_specs(motherboard)
        occupied_m2_indexes: list[int] = []
        sata_storage_specs = None
        total_sata_quantity = 0
        m2_storage_components = []

        for storage in storage_components:
            storage_specs = _get_specs(storage)
            storage_quantity = _get_quantity(storage)

            interface_result = check_storage_motherboard_interface(
                storage_specs,
                motherboard_specs,
            )
            form_factor_result = check_storage_motherboard_form_factor(
                storage_specs,
                motherboard_specs,
            )

            results.append(interface_result)
            results.append(form_factor_result)

            connection_type = _get_storage_connection_type(storage_specs)

            if connection_type == "sata":
                sata_storage_specs = storage_specs
                total_sata_quantity += storage_quantity
            elif connection_type in {"pcie", "sata_m2"}:
                m2_storage_components.append(
                    (storage_specs, storage_quantity, interface_result, form_factor_result)
                )

        for storage_specs, storage_quantity, interface_result, form_factor_result in m2_storage_components:
            availability_result = check_storage_motherboard_connection_availability(
                storage_specs,
                motherboard_specs,
                storage_quantity=storage_quantity,
                occupied_m2_slot_indexes=occupied_m2_indexes,
            )

            results.append(availability_result)

            if (
                interface_result.status == "compatible"
                and form_factor_result.status == "compatible"
            ):
                for _ in range(storage_quantity):
                    slot_index = _find_storage_slot_index(
                        storage_specs,
                        motherboard_specs,
                        occupied_m2_indexes,
                    )

                    if slot_index is None:
                        break

                    occupied_m2_indexes.append(slot_index)

        if sata_storage_specs is not None and total_sata_quantity > 0:
            results.append(
                check_storage_motherboard_connection_availability(
                    sata_storage_specs,
                    motherboard_specs,
                    storage_quantity=total_sata_quantity,
                    occupied_m2_slot_indexes=occupied_m2_indexes,
                )
            )

    return results
