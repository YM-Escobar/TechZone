
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


def _is_positive_int(value: Any) -> bool:
    """Comprueba que un valor sea un entero positivo, sin aceptar booleanos."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _parse_pcie_size(value: Any) -> int | None:
    """Extrae el número de líneas físicas de valores como x16 o x8."""
    if not isinstance(value, str):
        return None

    normalized = value.strip().casefold()

    if not normalized.startswith("x"):
        return None

    try:
        lanes = int(normalized[1:])
    except ValueError:
        return None

    return lanes if lanes > 0 else None


def check_gpu_motherboard_pcie_interface(
    gpu_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba si la interfaz física y eléctrica de la GPU
    puede utilizar alguna ranura PCIe de la motherboard.

    Una ranura físicamente más larga puede alojar una tarjeta
    con un conector más corto.

    Si tiene menos líneas eléctricas que las requeridas por la GPU,
    puede funcionar con un ancho de banda reducido.
    """
    gpu_interface = gpu_specs.get("interface")
    slots = motherboard_specs.get("pcie_slots_details")

    # Verificar que existan las estructuras necesarias.
    if not isinstance(gpu_interface, dict) or not isinstance(slots, list):
        return RuleResult(
            rule_id="gpu_motherboard_pcie_interface",
            status="indeterminate",
            message="No hay información suficiente para comprobar la interfaz PCIe.",
            components=["gpu", "motherboard"],
        )

    gpu_physical_size = _parse_pcie_size(
        gpu_interface.get("physical_size")
    )
    gpu_electrical_lanes = gpu_interface.get("electrical_lanes")

    # Validar las especificaciones de la GPU.
    if (
        gpu_physical_size is None
        or not _is_positive_int(gpu_electrical_lanes)
    ):
        return RuleResult(
            rule_id="gpu_motherboard_pcie_interface",
            status="indeterminate",
            message="Las especificaciones PCIe de la GPU están incompletas o son inválidas.",
            components=["gpu", "motherboard"],
        )

    valid_slots = []

    # Revisar las ranuras PCIe registradas en la motherboard.
    for slot in slots:
        if not isinstance(slot, dict):
            continue

        slot_physical_size = _parse_pcie_size(
            slot.get("physical_size")
        )
        slot_electrical_lanes = slot.get("electrical_lanes")
        quantity = slot.get("quantity")

        if (
            slot_physical_size is None
            or not _is_positive_int(slot_electrical_lanes)
            or not _is_positive_int(quantity)
        ):
            continue

        valid_slots.append({
            "physical_size": slot_physical_size,
            "electrical_lanes": slot_electrical_lanes,
            "quantity": quantity,
        })

    # Si no hay ranuras válidas, no se puede determinar el resultado.
    if not valid_slots:
        return RuleResult(
            rule_id="gpu_motherboard_pcie_interface",
            status="indeterminate",
            message="No hay información válida sobre las ranuras PCIe de la motherboard.",
            components=["gpu", "motherboard"],
        )

    # Buscar al menos una ranura que pueda alojar físicamente la GPU.
    compatible_slots = []

    for slot in valid_slots:
        physical_fit = slot["physical_size"] >= gpu_physical_size

        if physical_fit:
            compatible_slots.append(slot)

    # Si ninguna ranura tiene el tamaño físico necesario, es incompatible.
    if not compatible_slots:
        return RuleResult(
            rule_id="gpu_motherboard_pcie_interface",
            status="incompatible",
            message=(
                "La motherboard no dispone de una ranura PCIe "
                "con el tamaño físico necesario para la GPU."
            ),
            components=["gpu", "motherboard"],
        )

    # Buscar una ranura que también tenga suficientes líneas eléctricas.
    for slot in compatible_slots:
        if slot["electrical_lanes"] >= gpu_electrical_lanes:
            return RuleResult(
                rule_id="gpu_motherboard_pcie_interface",
                status="compatible",
                message=(
                    "La motherboard dispone de una ranura PCIe "
                    "física y eléctricamente adecuada para la GPU."
                ),
                components=["gpu", "motherboard"],
            )

    # La GPU puede funcionar, pero con menos líneas PCIe.
    return RuleResult(
        rule_id="gpu_motherboard_pcie_interface",
        status="warning",
        message=(
            "La GPU puede funcionar en la ranura PCIe disponible, "
            "pero tendrá menos líneas eléctricas de las que admite. "
            "Esto puede reducir el rendimiento."
        ),
        components=["gpu", "motherboard"],
    )



def check_gpu_motherboard_pcie_generation(
    gpu_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba la generación PCIe de la GPU frente a las ranuras
    físicamente adecuadas de la motherboard.

    Las generaciones PCIe son retrocompatibles.
    Una diferencia de generación genera una advertencia,
    no una incompatibilidad.
    """
    gpu_interface = gpu_specs.get("interface")
    slots = motherboard_specs.get("pcie_slots_details")

    # Verificar que existan las estructuras necesarias.
    if not isinstance(gpu_interface, dict) or not isinstance(slots, list):
        return RuleResult(
            rule_id="gpu_motherboard_pcie_generation",
            status="indeterminate",
            message="No hay información suficiente para comprobar la generación PCIe.",
            components=["gpu", "motherboard"],
        )

    gpu_generation = gpu_interface.get("generation")
    gpu_physical_size = _parse_pcie_size(
        gpu_interface.get("physical_size")
    )

    # Validar la información de la GPU.
    if (
        not isinstance(gpu_generation, str)
        or not gpu_generation.strip()
        or gpu_physical_size is None
    ):
        return RuleResult(
            rule_id="gpu_motherboard_pcie_generation",
            status="indeterminate",
            message="La información PCIe de la GPU está incompleta o es inválida.",
            components=["gpu", "motherboard"],
        )

    valid_generations = []

    # Revisar únicamente ranuras donde físicamente pueda instalarse la GPU.
    for slot in slots:
        if not isinstance(slot, dict):
            continue

        slot_physical_size = _parse_pcie_size(
            slot.get("physical_size")
        )
        generation = slot.get("generation")

        if (
            slot_physical_size is None
            or slot_physical_size < gpu_physical_size
            or not isinstance(generation, str)
            or not generation.strip()
        ):
            continue

        valid_generations.append(generation.strip().casefold())

    # No hay información suficiente sobre las ranuras adecuadas.
    if not valid_generations:
        return RuleResult(
            rule_id="gpu_motherboard_pcie_generation",
            status="indeterminate",
            message="No se conoce la generación PCIe de las ranuras físicamente adecuadas.",
            components=["gpu", "motherboard"],
        )

    # Si existe al menos una ranura con la misma generación, es compatible.
    if gpu_generation.strip().casefold() in valid_generations:
        return RuleResult(
            rule_id="gpu_motherboard_pcie_generation",
            status="compatible",
            message=(
                "La motherboard dispone de al menos una ranura "
                "físicamente adecuada con la misma generación PCIe de la GPU."
            ),
            components=["gpu", "motherboard"],
        )

    # Una generación diferente no impide el funcionamiento.
    return RuleResult(
        rule_id="gpu_motherboard_pcie_generation",
        status="warning",
        message=(
            "La generación PCIe de la GPU difiere de las ranuras "
            "físicamente adecuadas de la motherboard. PCIe es "
            "retrocompatible, pero el rendimiento puede verse afectado."
        ),
        components=["gpu", "motherboard"],
    )
