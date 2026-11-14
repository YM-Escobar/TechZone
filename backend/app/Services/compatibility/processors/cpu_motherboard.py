from typing import Any

from app.Services.compatibility.rule_result import RuleResult

# Reglas de CPU y motherboard.
from app.Services.compatibility.rules.motherboard.cpu_motherboard import (
    check_cpu_motherboard_socket,
    check_cpu_motherboard_model,
    check_cpu_motherboard_memory_type,
)
from app.Services.compatibility.processors.aggregates import _get_component_name, _get_specs
from app.Services.compatibility.processors.normalization import _normalize_entries

def run_cpu_motherboard_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    results: list[RuleResult] = []

    cpu_components = _normalize_entries(components.get("cpu"))
    motherboard_components = _normalize_entries(
        components.get("motherboard")
    )

    cpu = cpu_components[0] if cpu_components else None
    motherboard = motherboard_components[0] if motherboard_components else None

    if cpu and motherboard:
        cpu_specs = _get_specs(cpu)
        motherboard_specs = _get_specs(motherboard)
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

    return results