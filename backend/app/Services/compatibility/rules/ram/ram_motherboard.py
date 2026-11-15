
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


# Comprueba que un valor sea un entero positivo.
def _is_positive_int(value: Any) -> bool:
    return (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value > 0
    )


# Comprueba que la RAM utilice el mismo tipo de memoria
# que admite la motherboard.
def check_ram_motherboard_memory_type(
    ram_specs: dict[str, Any],
    motherboard_specs: dict[str, Any]
) -> RuleResult:

    # Obtiene los tipos de memoria de ambos componentes.
    ram_type = ram_specs.get("memory_type")
    motherboard_type = motherboard_specs.get("memory_type")

    # Comprueba que exista información suficiente.
    if (
        not isinstance(ram_type, str)
        or not ram_type.strip()
        or not isinstance(motherboard_type, str)
        or not motherboard_type.strip()
    ):
        return RuleResult(
            rule_id="ram_motherboard_memory_type",
            status="indeterminate",
            message="No hay información suficiente para verificar el tipo de memoria.",
            components=["ram", "motherboard"]
        )

    # Compara los tipos ignorando mayúsculas y espacios externos.
    if ram_type.strip().casefold() != motherboard_type.strip().casefold():
        return RuleResult(
            rule_id="ram_motherboard_memory_type",
            status="incompatible",
            message=(
                f"La memoria RAM utiliza {ram_type}, pero la motherboard "
                f"admite {motherboard_type}."
            ),
            components=["ram", "motherboard"]
        )

    return RuleResult(
        rule_id="ram_motherboard_memory_type",
        status="compatible",
        message=f"La RAM y la motherboard utilizan memoria {ram_type}.",
        components=["ram", "motherboard"]
    )


# Comprueba que la capacidad total de RAM no supere
# el límite máximo admitido por la motherboard.
def check_ram_motherboard_capacity(
    ram_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    ram_quantity: int = 1
) -> RuleResult:

    # Obtiene la capacidad del kit y el límite de la motherboard.
    ram_capacity = ram_specs.get("total_capacity_gb")
    motherboard_max = motherboard_specs.get("max_memory_gb")

    # Comprueba que los datos sean válidos.
    if (
        not _is_positive_int(ram_capacity)
        or not _is_positive_int(motherboard_max)
        or not _is_positive_int(ram_quantity)
    ):
        return RuleResult(
            rule_id="ram_motherboard_capacity",
            status="indeterminate",
            message="No hay información suficiente para verificar la capacidad máxima de RAM.",
            components=["ram", "motherboard"]
        )

    # Calcula la capacidad instalada considerando todos los kits.
    installed_capacity = ram_capacity * ram_quantity

    # Comprueba que no se supere el límite de la motherboard.
    if installed_capacity > motherboard_max:
        return RuleResult(
            rule_id="ram_motherboard_capacity",
            status="incompatible",
            message=(
                f"La configuración tendría {installed_capacity} GB de RAM, "
                f"pero la motherboard admite un máximo de {motherboard_max} GB."
            ),
            components=["ram", "motherboard"]
        )

    return RuleResult(
        rule_id="ram_motherboard_capacity",
        status="compatible",
        message=(
            f"La capacidad instalada de {installed_capacity} GB "
            f"no supera el máximo de {motherboard_max} GB de la motherboard."
        ),
        components=["ram", "motherboard"]
    )


# Comprueba que la cantidad total de módulos no supere
# los slots disponibles en la motherboard.
def check_ram_motherboard_slots(
    ram_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    ram_quantity: int = 1
) -> RuleResult:

    # Obtiene los módulos del kit y los slots disponibles.
    module_count = ram_specs.get("module_count")
    memory_slots = motherboard_specs.get("memory_slots")

    # Comprueba que los datos sean válidos.
    if (
        not _is_positive_int(module_count)
        or not _is_positive_int(memory_slots)
        or not _is_positive_int(ram_quantity)
    ):
        return RuleResult(
            rule_id="ram_motherboard_slots",
            status="indeterminate",
            message="No hay información suficiente para verificar los módulos y slots.",
            components=["ram", "motherboard"]
        )

    # Calcula la cantidad total de módulos instalados.
    installed_modules = module_count * ram_quantity

    # Comprueba que no se supere la cantidad de slots.
    if installed_modules > memory_slots:
        return RuleResult(
            rule_id="ram_motherboard_slots",
            status="incompatible",
            message=(
                f"La configuración requiere {installed_modules} slots, "
                f"pero la motherboard dispone de {memory_slots}."
            ),
            components=["ram", "motherboard"]
        )

    return RuleResult(
        rule_id="ram_motherboard_slots",
        status="compatible",
        message=(
            f"La configuración utiliza {installed_modules} módulos "
            f"y la motherboard dispone de {memory_slots} slots."
        ),
        components=["ram", "motherboard"]
    )
