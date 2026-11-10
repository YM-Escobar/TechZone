
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


# Comprueba que un valor sea un entero positivo.
def _is_positive_int(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


# Comprueba que la capacidad total de RAM no supere
# el límite máximo admitido por el procesador.
def check_ram_cpu_capacity(
    ram_specs: dict[str, Any],
    cpu_specs: dict[str, Any],
    ram_quantity: int = 1
) -> RuleResult:

    # Obtiene la capacidad del kit y el límite del procesador.
    ram_capacity = ram_specs.get("total_capacity_gb")
    cpu_max = cpu_specs.get("max_memory_gb")

    # Comprueba que los datos sean válidos.
    if (
        not _is_positive_int(ram_capacity)
        or not _is_positive_int(cpu_max)
        or not _is_positive_int(ram_quantity)
    ):
        return RuleResult(
            rule_id="ram_cpu_capacity",
            status="indeterminate",
            message="No hay información suficiente para verificar la capacidad máxima de memoria del procesador.",
            components=["ram", "cpu"]
        )

    # Calcula la capacidad instalada considerando todos los kits.
    installed_capacity = ram_capacity * ram_quantity

    # Comprueba que no se supere el límite del procesador.
    if installed_capacity > cpu_max:
        return RuleResult(
            rule_id="ram_cpu_capacity",
            status="incompatible",
            message=(
                f"La configuración tendría {installed_capacity} GB de RAM, "
                f"pero el procesador admite un máximo de {cpu_max} GB."
            ),
            components=["ram", "cpu"]
        )

    return RuleResult(
        rule_id="ram_cpu_capacity",
        status="compatible",
        message=(
            f"La capacidad instalada de {installed_capacity} GB "
            f"no supera el máximo de {cpu_max} GB del procesador."
        ),
        components=["ram", "cpu"]
    )
