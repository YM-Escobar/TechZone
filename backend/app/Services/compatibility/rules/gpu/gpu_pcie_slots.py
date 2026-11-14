
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _parse_pcie_size(value: Any) -> int | None:
    if not isinstance(value, str):
        return None

    normalized = value.strip().casefold()

    if not normalized.startswith("x"):
        return None

    try:
        size = int(normalized[1:])
    except ValueError:
        return None

    return size if size > 0 else None


def check_gpu_motherboard_pcie_slot_availability(
    gpu_components: list[dict[str, Any]],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    slots = motherboard_specs.get("pcie_slots_details")

    if not isinstance(slots, list) or not slots:
        return RuleResult(
            rule_id="gpu_motherboard_pcie_slot_availability",
            status="indeterminate",
            message="No hay información suficiente sobre las ranuras PCIe de la motherboard.",
            components=["gpu", "motherboard"],
        )

    gpu_sizes = []

    for gpu in gpu_components:
        if not isinstance(gpu, dict):
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message="La información de las GPU es inválida.",
                components=["gpu", "motherboard"],
            )

        specs = gpu.get("specs")
        quantity = gpu.get("quantity", 1)

        if (
            not isinstance(specs, dict)
            or not _is_positive_int(quantity)
        ):
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message="Las especificaciones o cantidades de las GPU están incompletas.",
                components=["gpu", "motherboard"],
            )

        interface = specs.get("interface")

        if not isinstance(interface, dict):
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message="No se conoce el tamaño físico de una de las GPU.",
                components=["gpu", "motherboard"],
            )

        physical_size = _parse_pcie_size(
            interface.get("physical_size")
        )

        if physical_size is None:
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message="El tamaño físico de una de las GPU es inválido.",
                components=["gpu", "motherboard"],
            )

        gpu_sizes.extend([physical_size] * quantity)

    available_slots = []

    for slot in slots:
        if not isinstance(slot, dict):
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message="La información de las ranuras PCIe contiene datos inválidos.",
                components=["gpu", "motherboard"],
            )

        physical_size = _parse_pcie_size(
            slot.get("physical_size")
        )
        quantity = slot.get("quantity")

        if (
            physical_size is None
            or not _is_positive_int(quantity)
        ):
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message="La información de las ranuras PCIe está incompleta o es inválida.",
                components=["gpu", "motherboard"],
            )

        available_slots.extend([physical_size] * quantity)

    gpu_sizes.sort(reverse=True)
    available_slots.sort()

    for gpu_size in gpu_sizes:
        suitable_slot = next(
            (
                index
                for index, slot_size in enumerate(available_slots)
                if slot_size >= gpu_size
            ),
            None,
        )

        if suitable_slot is None:
            return RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="incompatible",
                message="La motherboard no dispone de suficientes ranuras PCIe físicas para todas las GPU seleccionadas.",
                components=["gpu", "motherboard"],
            )

        available_slots.pop(suitable_slot)

    return RuleResult(
        rule_id="gpu_motherboard_pcie_slot_availability",
        status="compatible",
        message="La motherboard dispone de suficientes ranuras PCIe físicas para todas las GPU seleccionadas.",
        components=["gpu", "motherboard"],
    )
