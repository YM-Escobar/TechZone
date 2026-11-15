
import pytest

from app.Services.compatibility.rules.gpu.gpu_motherboard import (
    check_gpu_motherboard_pcie_interface,
    check_gpu_motherboard_pcie_generation,
)
from app.Services.compatibility.rules.gpu.gpu_psu import (
    check_gpu_psu_wattage,
    check_gpu_psu_connectors,
)


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def gpu_specs():
    """Especificaciones de una GPU de ejemplo."""
    return {
        "interface": {
            "generation": "4.0",
            "physical_size": "x16",
            "electrical_lanes": 16,
        },
        "recommended_psu_w": 750,
        "power_connectors_required": [
            {"type": "12VHPWR", "quantity": 1}
        ],
    }


@pytest.fixture
def motherboard_specs():
    """Especificaciones de una motherboard de ejemplo."""
    return {
        "pcie_slots_details": [
            {
                "generation": "4.0",
                "physical_size": "x16",
                "electrical_lanes": 16,
                "quantity": 1,
            },
            {
                "generation": "3.0",
                "physical_size": "x16",
                "electrical_lanes": 4,
                "quantity": 1,
            },
        ]
    }


@pytest.fixture
def psu_specs():
    """Especificaciones de una fuente de ejemplo."""
    return {
        "wattage_w": 850,
        "power_connectors": [
            {
                "type": "12VHPWR",
                "quantity": 1,
                "native": True,
            }
        ],
    }


# ============================================================
# GPU + MOTHERBOARD: INTERFAZ PCIe
# ============================================================

def test_gpu_motherboard_pcie_interface_compatible(
    gpu_specs,
    motherboard_specs,
):
    """Una ranura x16 física y eléctrica admite una GPU x16."""
    result = check_gpu_motherboard_pcie_interface(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_gpu_motherboard_pcie_interface_smaller_connector(
    gpu_specs,
    motherboard_specs,
):
    """Una GPU x8 puede utilizar una ranura física x16 con 8 líneas."""
    gpu_specs["interface"]["physical_size"] = "x8"
    gpu_specs["interface"]["electrical_lanes"] = 8

    motherboard_specs["pcie_slots_details"] = [
        {
            "generation": "4.0",
            "physical_size": "x16",
            "electrical_lanes": 8,
            "quantity": 1,
        }
    ]

    result = check_gpu_motherboard_pcie_interface(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_gpu_motherboard_pcie_interface_incompatible_electrical_lanes(
    gpu_specs,
    motherboard_specs,
):
    """Una ranura x16 física con 8 líneas genera una advertencia."""
    motherboard_specs["pcie_slots_details"] = [
        {
            "generation": "4.0",
            "physical_size": "x16",
            "electrical_lanes": 8,
            "quantity": 1,
        }
    ]

    result = check_gpu_motherboard_pcie_interface(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "warning"

def test_gpu_motherboard_pcie_interface_incompatible_electrical_lanes(
    gpu_specs,
    motherboard_specs,
):
    """Una ranura x16 física con 8 líneas no satisface una GPU x16."""
    motherboard_specs["pcie_slots_details"] = [
        {
            "generation": "4.0",
            "physical_size": "x16",
            "electrical_lanes": 8,
            "quantity": 1,
        }
    ]

    result = check_gpu_motherboard_pcie_interface(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "warning"


def test_gpu_motherboard_pcie_interface_missing_data(
    gpu_specs,
):
    """La ausencia de información sobre ranuras genera indeterminate."""
    result = check_gpu_motherboard_pcie_interface(
        gpu_specs,
        {},
    )

    assert result.status == "indeterminate"


def test_gpu_motherboard_pcie_interface_invalid_gpu_data(
    gpu_specs,
    motherboard_specs,
):
    """Una interfaz PCIe inválida no debe producir incompatibilidad."""
    gpu_specs["interface"]["electrical_lanes"] = 0

    result = check_gpu_motherboard_pcie_interface(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "indeterminate"


# ============================================================
# GPU + MOTHERBOARD: GENERACIÓN PCIe
# ============================================================

def test_gpu_motherboard_pcie_generation_compatible(
    gpu_specs,
    motherboard_specs,
):
    """La misma generación PCIe es compatible."""
    result = check_gpu_motherboard_pcie_generation(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_gpu_motherboard_pcie_generation_backward_compatible(
    gpu_specs,
    motherboard_specs,
):
    """Una generación diferente genera warning, no incompatibilidad."""
    motherboard_specs["pcie_slots_details"] = [
        {
            "generation": "3.0",
            "physical_size": "x16",
            "electrical_lanes": 16,
            "quantity": 1,
        }
    ]

    result = check_gpu_motherboard_pcie_generation(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "warning"


def test_gpu_motherboard_pcie_generation_missing_gpu_data(
    gpu_specs,
    motherboard_specs,
):
    """Sin generación de GPU no se puede determinar el resultado."""
    gpu_specs["interface"]["generation"] = None

    result = check_gpu_motherboard_pcie_generation(
        gpu_specs,
        motherboard_specs,
    )

    assert result.status == "indeterminate"


def test_gpu_motherboard_pcie_generation_missing_motherboard_data(
    gpu_specs,
):
    """Sin generaciones de motherboard no se puede determinar."""
    result = check_gpu_motherboard_pcie_generation(
        gpu_specs,
        {"pcie_slots_details": []},
    )

    assert result.status == "indeterminate"


# ============================================================
# GPU + PSU: POTENCIA
# ============================================================

def test_gpu_psu_wattage_compatible(
    gpu_specs,
    psu_specs,
):
    """Una fuente que cumple la potencia recomendada es compatible."""
    result = check_gpu_psu_wattage(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "compatible"


def test_gpu_psu_wattage_warning(
    gpu_specs,
    psu_specs,
):
    """Una potencia inferior a la recomendada genera warning."""
    psu_specs["wattage_w"] = 650

    result = check_gpu_psu_wattage(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "warning"
    assert "650 W" in result.message
    assert "750 W" in result.message


def test_gpu_psu_wattage_missing_data(
    gpu_specs,
):
    """La falta de potencia genera indeterminate."""
    result = check_gpu_psu_wattage(
        gpu_specs,
        {},
    )

    assert result.status == "indeterminate"


def test_gpu_psu_wattage_invalid_data(
    gpu_specs,
    psu_specs,
):
    """Una potencia inválida no debe generar una conclusión."""
    psu_specs["wattage_w"] = True

    result = check_gpu_psu_wattage(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "indeterminate"


# ============================================================
# GPU + PSU: CONECTORES
# ============================================================

def test_gpu_psu_connectors_compatible(
    gpu_specs,
    psu_specs,
):
    """La fuente dispone del conector nativo requerido."""
    result = check_gpu_psu_connectors(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "compatible"


def test_gpu_psu_connectors_incompatible_missing_connector(
    gpu_specs,
    psu_specs,
):
    """La ausencia del conector requerido genera incompatibilidad."""
    psu_specs["power_connectors"] = [
        {
            "type": "PCIe 8-pin",
            "quantity": 2,
            "native": True,
        }
    ]

    result = check_gpu_psu_connectors(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "incompatible"


def test_gpu_psu_connectors_insufficient_quantity(
    gpu_specs,
    psu_specs,
):
    """Un conector no es suficiente cuando la GPU requiere dos."""
    gpu_specs["power_connectors_required"] = [
        {"type": "12VHPWR", "quantity": 2}
    ]

    result = check_gpu_psu_connectors(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "incompatible"


def test_gpu_psu_connectors_non_native_not_counted(
    gpu_specs,
    psu_specs,
):
    """Los conectores no nativos no cuentan como conectores disponibles."""
    psu_specs["power_connectors"][0]["native"] = False

    result = check_gpu_psu_connectors(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "incompatible"


def test_gpu_psu_connectors_no_additional_power_required(
    gpu_specs,
    psu_specs,
):
    """Una GPU sin conectores adicionales es compatible."""
    gpu_specs["power_connectors_required"] = []

    result = check_gpu_psu_connectors(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "compatible"


def test_gpu_psu_connectors_missing_data(
    gpu_specs,
):
    """La falta de información sobre conectores genera indeterminate."""
    result = check_gpu_psu_connectors(
        gpu_specs,
        {},
    )

    assert result.status == "indeterminate"


def test_gpu_psu_connectors_invalid_data(
    gpu_specs,
    psu_specs,
):
    """Una cantidad de conectores inválida genera indeterminate."""
    psu_specs["power_connectors"][0]["quantity"] = 0

    result = check_gpu_psu_connectors(
        gpu_specs,
        psu_specs,
    )

    assert result.status == "indeterminate"
