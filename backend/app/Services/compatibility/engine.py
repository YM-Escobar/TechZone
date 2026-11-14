from typing import Any

from app.Services.compatibility.rule_result import RuleResult
from app.Services.compatibility.processors.cpu_motherboard import run_cpu_motherboard_rules
from app.Services.compatibility.processors.ram import run_ram_rules
from app.Services.compatibility.processors.gpu import run_gpu_rules
from app.Services.compatibility.processors.cooling import run_cooling_rules
from app.Services.compatibility.processors.storage import run_storage_rules


def run_compatibility_rules(
    components: dict[str, Any],
) -> list[RuleResult]:
    results: list[RuleResult] = []

    results.extend(run_cpu_motherboard_rules(components))
    results.extend(run_ram_rules(components))
    results.extend(run_gpu_rules(components))
    results.extend(run_cooling_rules(components))
    results.extend(run_storage_rules(components))

    return results