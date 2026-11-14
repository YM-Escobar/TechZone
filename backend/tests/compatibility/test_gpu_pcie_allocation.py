from app.Services.compatibility.rules.gpu.gpu_pcie_allocation import (
    check_gpu_motherboard_pcie_allocation,
)


def make_gpu(
    name: str,
    generation: str = "4.0",
    physical_size: str = "x16",
    electrical_lanes: int = 16,
    quantity: int = 1,
) -> dict:
    return {
        "name": name,
        "quantity": quantity,
        "specs": {
            "interface": {
                "generation": generation,
                "physical_size": physical_size,
                "electrical_lanes": electrical_lanes,
            }
        },
    }


def make_slot(
    generation: str = "4.0",
    physical_size: str = "x16",
    electrical_lanes: int = 16,
    quantity: int = 1,
) -> dict:
    return {
        "generation": generation,
        "physical_size": physical_size,
        "electrical_lanes": electrical_lanes,
        "quantity": quantity,
    }


def test_multiple_gpus_are_assigned_to_distinct_slots():
    gpus = [
        make_gpu("GPU x16", "4.0", "x16", 16),
        make_gpu("GPU x8", "3.0", "x8", 8),
    ]
    motherboard = {
        "pcie_slots_details": [
            make_slot("4.0", "x16", 16),
            make_slot("3.0", "x8", 8),
        ]
    }

    results = check_gpu_motherboard_pcie_allocation(gpus, motherboard)

    assert [result.status for result in results] == [
        "compatible",
        "compatible",
        "compatible",
    ]


def test_assignment_reserves_the_only_slot_for_the_gpu_that_needs_it():
    gpus = [
        make_gpu("GPU x8", "4.0", "x8", 8),
        make_gpu("GPU x16", "4.0", "x16", 16),
    ]
    motherboard = {
        "pcie_slots_details": [
            make_slot("4.0", "x16", 16),
            make_slot("3.0", "x8", 8),
        ]
    }

    results = check_gpu_motherboard_pcie_allocation(gpus, motherboard)

    assert [result.status for result in results] == [
        "compatible",
        "compatible",
        "warning",
    ]


def test_assignment_prefers_matching_generation_when_available():
    gpu = make_gpu("GPU x8", "4.0", "x8", 8)
    motherboard = {
        "pcie_slots_details": [
            make_slot("3.0", "x16", 8),
            make_slot("4.0", "x8", 8),
        ]
    }

    results = check_gpu_motherboard_pcie_allocation([gpu], motherboard)

    assert [result.status for result in results] == [
        "compatible",
        "compatible",
        "compatible",
    ]


def test_reduced_electrical_lanes_generate_warning():
    gpu = make_gpu("GPU x16", "4.0", "x16", 16)
    motherboard = {
        "pcie_slots_details": [make_slot("4.0", "x16", 8)]
    }

    results = check_gpu_motherboard_pcie_allocation([gpu], motherboard)

    assert [result.status for result in results] == [
        "compatible",
        "warning",
        "compatible",
    ]


def test_generation_difference_generates_warning():
    gpu = make_gpu("GPU x16", "4.0", "x16", 16)
    motherboard = {
        "pcie_slots_details": [make_slot("3.0", "x16", 16)]
    }

    results = check_gpu_motherboard_pcie_allocation([gpu], motherboard)

    assert [result.status for result in results] == [
        "compatible",
        "compatible",
        "warning",
    ]


def test_insufficient_physical_slots_are_incompatible():
    gpus = [
        make_gpu("GPU A"),
        make_gpu("GPU B"),
    ]
    motherboard = {
        "pcie_slots_details": [make_slot()]
    }

    results = check_gpu_motherboard_pcie_allocation(gpus, motherboard)

    assert [result.status for result in results] == [
        "incompatible",
        "indeterminate",
        "indeterminate",
    ]


def test_empty_pcie_slots_are_known_to_be_incompatible_with_gpu():
    gpu = make_gpu("GPU x16")

    results = check_gpu_motherboard_pcie_allocation(
        [gpu],
        {"pcie_slots_details": []},
    )

    assert results[0].status == "incompatible"


def test_missing_pcie_slot_data_is_indeterminate():
    gpu = make_gpu("GPU x16")

    results = check_gpu_motherboard_pcie_allocation([gpu], {})

    assert all(result.status == "indeterminate" for result in results)


def test_gpu_quantity_reserves_one_slot_per_unit():
    gpu = make_gpu("GPU x8", "4.0", "x8", 8, quantity=2)
    motherboard = {
        "pcie_slots_details": [make_slot("4.0", "x8", 8, quantity=2)]
    }

    results = check_gpu_motherboard_pcie_allocation([gpu], motherboard)

    assert all(result.status == "compatible" for result in results)
