from typing import Any

from app.Services.compatibility.rule_result import RuleResult

# Reglas de RAM.
from app.Services.compatibility.rules.ram.ram_motherboard import (
    check_ram_motherboard_memory_type,
    check_ram_motherboard_capacity,
    check_ram_motherboard_slots,
)
from app.Services.compatibility.rules.ram.ram_cpu import (
    check_ram_cpu_capacity,
)
from app.Services.compatibility.processors.aggregates import _build_ram_aggregate, _get_specs
from app.Services.compatibility.processors.normalization import _normalize_entries


def run_ram_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    results: list[RuleResult] = []

    cpu_components = _normalize_entries(components.get("cpu"))
    motherboard_components = _normalize_entries(
        components.get("motherboard")
    )
    ram_components = _normalize_entries(components.get("ram"))

    cpu = cpu_components[0] if cpu_components else None
    motherboard = motherboard_components[0] if motherboard_components else None

    if ram_components:
        if motherboard:
            motherboard_specs = _get_specs(motherboard)

            for ram in ram_components:
                results.append(
                    check_ram_motherboard_memory_type(
                        _get_specs(ram),
                        motherboard_specs,
                    )
                )

        ram_aggregate = _build_ram_aggregate(ram_components)

        if ram_aggregate is not None:
            if motherboard:
                motherboard_specs = _get_specs(motherboard)

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
                        _get_specs(cpu),
                    )
                )

    return results