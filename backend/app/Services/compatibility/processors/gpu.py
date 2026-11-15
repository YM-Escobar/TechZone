from typing import Any

from app.Services.compatibility.rule_result import RuleResult

# Reglas de GPU.
from app.Services.compatibility.rules.gpu.gpu_pcie_allocation import (
    check_gpu_motherboard_pcie_allocation,
)
from app.Services.compatibility.rules.gpu.gpu_psu import (
    check_gpu_psu_wattage,
)
from app.Services.compatibility.rules.gpu.gpu_psu_aggregate import (
    check_multiple_gpu_psu_wattage,
    check_multiple_gpu_psu_connectors,
)
from app.Services.compatibility.processors.aggregates import _get_specs
from app.Services.compatibility.processors.normalization import _normalize_entries

def run_gpu_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    results: list[RuleResult] = []

    motherboard_components = _normalize_entries(
        components.get("motherboard")
    )
    psu_components = _normalize_entries(
        components.get("psu")
    )
    gpu_components = _normalize_entries(
        components.get("gpu")
    )

    motherboard = motherboard_components[0] if motherboard_components else None
    psu = psu_components[0] if psu_components else None

    motherboard_specs = _get_specs(motherboard) if motherboard else None
    psu_specs = _get_specs(psu) if psu else None

    if motherboard and gpu_components:
        results.extend(
            check_gpu_motherboard_pcie_allocation(
                gpu_components,
                motherboard_specs,
            )
        )

    for gpu in gpu_components:
        gpu_specs = _get_specs(gpu)

        if psu:
            results.append(
                check_gpu_psu_wattage(
                    gpu_specs,
                    psu_specs,
                )
            )

    if psu and gpu_components:
        results.append(
            check_multiple_gpu_psu_wattage(
                gpu_components,
                psu_specs,
            )
        )

        results.append(
            check_multiple_gpu_psu_connectors(
                gpu_components,
                psu_specs,
            )
        )

    return results
