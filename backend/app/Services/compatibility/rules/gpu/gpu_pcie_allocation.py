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

    return size if size in {1, 4, 8, 16} else None


def _get_gpu_units(
    gpu_components: list[dict[str, Any]],
) -> list[dict[str, Any]] | None:
    gpu_units = []

    for gpu in gpu_components:
        if not isinstance(gpu, dict):
            return None

        specs = gpu.get("specs")
        quantity = gpu.get("quantity", 1)

        if not isinstance(specs, dict) or not _is_positive_int(quantity):
            return None

        interface = specs.get("interface")

        if not isinstance(interface, dict):
            return None

        physical_size = _parse_pcie_size(interface.get("physical_size"))
        electrical_lanes = interface.get("electrical_lanes")
        generation = interface.get("generation")

        if (
            physical_size is None
            or not _is_positive_int(electrical_lanes)
            or electrical_lanes not in {1, 2, 4, 8, 16}
            or electrical_lanes > physical_size
            or not isinstance(generation, str)
            or not generation.strip()
        ):
            return None

        gpu_units.extend(
            {
                "physical_size": physical_size,
                "electrical_lanes": electrical_lanes,
                "generation": generation.strip().casefold(),
            }
            for _ in range(quantity)
        )

    return gpu_units


def _get_motherboard_slots(
    motherboard_specs: dict[str, Any],
) -> list[dict[str, Any]] | None:
    slots = motherboard_specs.get("pcie_slots_details")

    if not isinstance(slots, list):
        return None

    available_slots = []

    for slot in slots:
        if not isinstance(slot, dict):
            return None

        physical_size = _parse_pcie_size(slot.get("physical_size"))
        electrical_lanes = slot.get("electrical_lanes")
        generation = slot.get("generation")
        quantity = slot.get("quantity")

        if (
            physical_size is None
            or not _is_positive_int(electrical_lanes)
            or electrical_lanes not in {1, 2, 4, 8, 16}
            or electrical_lanes > physical_size
            or not isinstance(generation, str)
            or not generation.strip()
            or not _is_positive_int(quantity)
        ):
            return None

        available_slots.extend(
            {
                "physical_size": physical_size,
                "electrical_lanes": electrical_lanes,
                "generation": generation.strip().casefold(),
            }
            for _ in range(quantity)
        )

    return available_slots


def _get_assignment(
    gpu_units: list[dict[str, Any]],
    available_slots: list[dict[str, Any]],
) -> list[tuple[dict[str, Any], dict[str, Any]]] | None:
    if len(gpu_units) > len(available_slots):
        return None

    candidates = {
        index: [
            slot_index
            for slot_index, slot in enumerate(available_slots)
            if slot["physical_size"] >= gpu["physical_size"]
        ]
        for index, gpu in enumerate(gpu_units)
    }

    if any(not slot_indexes for slot_indexes in candidates.values()):
        return None

    ordered_gpu_indexes = sorted(
        range(len(gpu_units)),
        key=lambda index: (
            len(candidates[index]),
            -gpu_units[index]["physical_size"],
            -gpu_units[index]["electrical_lanes"],
        ),
    )

    best_score = None
    best_assignment = None

    def assign(
        position: int,
        occupied_slots: set[int],
        current_assignment: dict[int, int],
        current_score: tuple[int, int, int, int],
    ) -> None:
        nonlocal best_score, best_assignment

        if best_score is not None and current_score >= best_score:
            return

        if position == len(ordered_gpu_indexes):
            best_score = current_score
            best_assignment = current_assignment.copy()
            return

        gpu_index = ordered_gpu_indexes[position]
        gpu = gpu_units[gpu_index]

        slot_options = []

        for slot_index in candidates[gpu_index]:
            if slot_index in occupied_slots:
                continue

            slot = available_slots[slot_index]
            lane_deficit = max(
                gpu["electrical_lanes"] - slot["electrical_lanes"],
                0,
            )
            lane_warning = int(lane_deficit > 0)
            generation_warning = int(
                gpu["generation"] != slot["generation"]
            )

            slot_score = (
                lane_warning + generation_warning,
                lane_warning,
                generation_warning,
                lane_deficit,
            )
            slot_options.append((slot_score, slot_index))

        for slot_score, slot_index in sorted(slot_options):
            next_score = tuple(
                current_score[index] + slot_score[index]
                for index in range(4)
            )

            occupied_slots.add(slot_index)
            current_assignment[gpu_index] = slot_index

            assign(
                position + 1,
                occupied_slots,
                current_assignment,
                next_score,
            )

            del current_assignment[gpu_index]
            occupied_slots.remove(slot_index)

    assign(0, set(), {}, (0, 0, 0, 0))

    if best_assignment is None:
        return None

    return [
        (gpu_units[gpu_index], available_slots[slot_index])
        for gpu_index, slot_index in best_assignment.items()
    ]


def check_gpu_motherboard_pcie_allocation(
    gpu_components: list[dict[str, Any]],
    motherboard_specs: dict[str, Any],
) -> tuple[RuleResult, RuleResult, RuleResult]:
    components = ["gpu", "motherboard"]
    gpu_units = _get_gpu_units(gpu_components)
    available_slots = _get_motherboard_slots(motherboard_specs)

    if gpu_units is None or available_slots is None:
        message = "No hay información PCIe suficiente o válida para asignar las GPU a las ranuras de la motherboard."

        return (
            RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="indeterminate",
                message=message,
                components=components,
            ),
            RuleResult(
                rule_id="gpu_motherboard_pcie_interface",
                status="indeterminate",
                message=message,
                components=components,
            ),
            RuleResult(
                rule_id="gpu_motherboard_pcie_generation",
                status="indeterminate",
                message=message,
                components=components,
            ),
        )

    assignment = _get_assignment(gpu_units, available_slots)

    if assignment is None:
        return (
            RuleResult(
                rule_id="gpu_motherboard_pcie_slot_availability",
                status="incompatible",
                message="La motherboard no dispone de suficientes ranuras PCIe físicas para todas las GPU seleccionadas.",
                components=components,
            ),
            RuleResult(
                rule_id="gpu_motherboard_pcie_interface",
                status="indeterminate",
                message="No se pudo asignar cada GPU a una ranura PCIe física distinta para comprobar sus líneas eléctricas.",
                components=components,
            ),
            RuleResult(
                rule_id="gpu_motherboard_pcie_generation",
                status="indeterminate",
                message="No se pudo asignar cada GPU a una ranura PCIe física distinta para comprobar su generación.",
                components=components,
            ),
        )

    reduced_lane_assignments = [
        (gpu, slot)
        for gpu, slot in assignment
        if slot["electrical_lanes"] < gpu["electrical_lanes"]
    ]
    generation_mismatches = [
        (gpu, slot)
        for gpu, slot in assignment
        if slot["generation"] != gpu["generation"]
    ]

    availability_result = RuleResult(
        rule_id="gpu_motherboard_pcie_slot_availability",
        status="compatible",
        message="Cada GPU dispone de una ranura PCIe física independiente en la motherboard.",
        components=components,
    )

    if reduced_lane_assignments:
        interface_result = RuleResult(
            rule_id="gpu_motherboard_pcie_interface",
            status="warning",
            message="Una o más GPU utilizarán menos líneas eléctricas de las que admiten. Esto puede reducir el rendimiento.",
            components=components,
        )
    else:
        interface_result = RuleResult(
            rule_id="gpu_motherboard_pcie_interface",
            status="compatible",
            message="Todas las GPU disponen de ranuras PCIe asignadas con suficientes líneas eléctricas.",
            components=components,
        )

    if generation_mismatches:
        generation_result = RuleResult(
            rule_id="gpu_motherboard_pcie_generation",
            status="warning",
            message="Una o más GPU utilizan una generación PCIe diferente a la de su ranura asignada. PCIe es retrocompatible, pero el rendimiento puede verse afectado.",
            components=components,
        )
    else:
        generation_result = RuleResult(
            rule_id="gpu_motherboard_pcie_generation",
            status="compatible",
            message="Todas las GPU tienen asignada una ranura PCIe de la misma generación.",
            components=components,
        )

    return availability_result, interface_result, generation_result
