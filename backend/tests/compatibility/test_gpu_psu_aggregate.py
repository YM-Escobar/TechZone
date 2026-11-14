
import pytest

from app.Services.compatibility.rules.gpu.gpu_psu_aggregate import (
    check_multiple_gpu_psu_wattage,
    check_multiple_gpu_psu_connectors,
)


@pytest.fixture
def gpu_components():
    return [
        {
            "name": "GPU A",
            "specs": {
                "board_power_w": 300,
                "power_connectors_required": [
                    {"type": "12VHPWR", "quantity": 1},
                ],
            },
            "quantity": 1,
        },
        {
            "name": "GPU B",
            "specs": {
                "board_power_w": 250,
                "power_connectors_required": [
                    {"type": "12VHPWR", "quantity": 1},
                ],
            },
            "quantity": 1,
        },
    ]


@pytest.fixture
def psu_specs():
    return {
        "wattage_w": 850,
        "power_connectors": [
            {
                "type": "12VHPWR",
                "quantity": 2,
                "native": True,
            },
        ],
    }


def test_multiple_gpu_psu_wattage_compatible(
    gpu_components,
    psu_specs,
):
    result = check_multiple_gpu_psu_wattage(
        gpu_components,
        psu_specs,
    )

    assert result.status == "compatible"


def test_multiple_gpu_psu_wattage_warning(
    gpu_components,
    psu_specs,
):
    psu_specs["wattage_w"] = 500

    result = check_multiple_gpu_psu_wattage(
        gpu_components,
        psu_specs,
    )

    assert result.status == "warning"


def test_multiple_gpu_psu_wattage_quantity(
    gpu_components,
    psu_specs,
):
    gpu_components[0]["quantity"] = 2
    psu_specs["wattage_w"] = 800

    result = check_multiple_gpu_psu_wattage(
        gpu_components,
        psu_specs,
    )

    assert result.status == "warning"


def test_multiple_gpu_psu_wattage_missing_data(
    gpu_components,
):
    gpu_components[0]["specs"]["board_power_w"] = None

    result = check_multiple_gpu_psu_wattage(
        gpu_components,
        {"wattage_w": 850},
    )

    assert result.status == "indeterminate"


def test_multiple_gpu_psu_connectors_compatible(
    gpu_components,
    psu_specs,
):
    result = check_multiple_gpu_psu_connectors(
        gpu_components,
        psu_specs,
    )

    assert result.status == "compatible"


def test_multiple_gpu_psu_connectors_insufficient_quantity(
    gpu_components,
    psu_specs,
):
    psu_specs["power_connectors"][0]["quantity"] = 1

    result = check_multiple_gpu_psu_connectors(
        gpu_components,
        psu_specs,
    )

    assert result.status == "incompatible"


def test_multiple_gpu_psu_connectors_quantity(
    gpu_components,
    psu_specs,
):
    gpu_components[0]["quantity"] = 2

    result = check_multiple_gpu_psu_connectors(
        gpu_components,
        psu_specs,
    )

    assert result.status == "incompatible"


def test_multiple_gpu_psu_connectors_non_native_not_counted(
    gpu_components,
    psu_specs,
):
    psu_specs["power_connectors"][0]["native"] = False

    result = check_multiple_gpu_psu_connectors(
        gpu_components,
        psu_specs,
    )

    assert result.status == "incompatible"


def test_multiple_gpu_psu_connectors_without_requirements(
    gpu_components,
    psu_specs,
):
    for gpu in gpu_components:
        gpu["specs"]["power_connectors_required"] = []

    result = check_multiple_gpu_psu_connectors(
        gpu_components,
        psu_specs,
    )

    assert result.status == "compatible"


def test_multiple_gpu_psu_connectors_missing_data(
    gpu_components,
    psu_specs,
):
    gpu_components[0]["specs"]["power_connectors_required"] = None

    result = check_multiple_gpu_psu_connectors(
        gpu_components,
        psu_specs,
    )

    assert result.status == "indeterminate"
