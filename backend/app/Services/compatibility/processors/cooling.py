from typing import Any

from app.Services.compatibility.rule_result import RuleResult
# Reglas de CPU y refrigeración.
from app.Services.compatibility.rules.cpu.cpu_cooling import (
    check_cpu_cooling_socket,
    check_cpu_cooling_thermal_capacity,
)
from app.Services.compatibility.processors.aggregates import _get_specs
from app.Services.compatibility.processors.normalization import _normalize_entries

def run_cooling_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    results: list[RuleResult] = []

    cpu_components = _normalize_entries(components.get("cpu"))
    cooling_components = _normalize_entries(components.get("cooling"))

    cpu = cpu_components[0] if cpu_components else None
    cooling = cooling_components[0] if cooling_components else None

    if cpu and cooling:
        cpu_specs = _get_specs(cpu)
        cooling_specs = _get_specs(cooling)

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

    return results