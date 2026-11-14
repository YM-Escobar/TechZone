
import pytest

from app.Services.compatibility.rules.gpu.gpu_pcie_slots import (
    check_gpu_motherboard_pcie_slot_availability,
)


@pytest.fixture
def gpu_x16():
    return {
        "name": "GPU x16",
        "specs": {
            "interface": {
                "physical_size": "x16",
            }
        },
        "quantity": 1,
    }


@pytest.fixture
def gpu_x8():
    return {
        "name": "GPU x8",
        "specs": {
            "interface": {
                "physical_size": "x8",
            }
        },
        "quantity": 1,
    }


@pytest.fixture
def motherboard_specs():
    return {
        "pcie_slots_details": [
            {
                "physical_size": "x16",
                "electrical_lanes": 16,
                "generation": "4.0",
                "quantity": 1,
            },
            {
                "physical_size": "x8",
                "electrical_lanes": 8,
                "generation": "3.0",
                "quantity": 1,
            },
        ]
    }


def test_gpu_pcie_slot_availability_single_gpu(
    gpu_x16,
    motherboard_specs,
):
    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu_x16],
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_gpu_pcie_slot_availability_multiple_gpus(
    gpu_x16,
    gpu_x8,
    motherboard_specs,
):
    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu_x16, gpu_x8],
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_gpu_pcie_slot_availability_insufficient_slots(
    gpu_x16,
    motherboard_specs,
):
    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu_x16, gpu_x16],
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_gpu_pcie_slot_availability_physical_size_mismatch(
    gpu_x16,
):
    motherboard = {
        "pcie_slots_details": [
            {
                "physical_size": "x8",
                "electrical_lanes": 8,
                "generation": "4.0",
                "quantity": 2,
            }
        ]
    }

    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu_x16],
        motherboard,
    )

    assert result.status == "incompatible"


def test_gpu_pcie_slot_availability_gpu_quantity(
    gpu_x8,
):
    motherboard = {
        "pcie_slots_details": [
            {
                "physical_size": "x8",
                "electrical_lanes": 8,
                "generation": "4.0",
                "quantity": 2,
            }
        ]
    }

    gpu = {
        **gpu_x8,
        "quantity": 2,
    }

    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu],
        motherboard,
    )

    assert result.status == "compatible"


def test_gpu_pcie_slot_availability_missing_motherboard_data(
    gpu_x16,
):
    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu_x16],
        {},
    )

    assert result.status == "indeterminate"


def test_gpu_pcie_slot_availability_missing_gpu_data(
    motherboard_specs,
):
    gpu = {
        "name": "GPU sin interfaz",
        "specs": {},
        "quantity": 1,
    }

    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu],
        motherboard_specs,
    )

    assert result.status == "indeterminate"


def test_gpu_pcie_slot_availability_invalid_quantity(
    gpu_x16,
    motherboard_specs,
):
    gpu = {
        **gpu_x16,
        "quantity": 0,
    }

    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu],
        motherboard_specs,
    )

    assert result.status == "indeterminate"


def test_gpu_pcie_slot_availability_empty_slots_is_incompatible(gpu_x16):
    result = check_gpu_motherboard_pcie_slot_availability(
        [gpu_x16],
        {"pcie_slots_details": []},
    )

    assert result.status == "incompatible"
