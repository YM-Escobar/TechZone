
import pytest

from app.Services.compatibility.rules.storage.storage_motherboard import (
    check_storage_motherboard_interface,
    check_storage_motherboard_form_factor,
    check_storage_motherboard_connection_availability,
)


@pytest.fixture
def motherboard_specs():
    """Motherboard con ranuras M.2 PCIe, M.2 SATA y puertos SATA."""
    return {
        "sata_ports": 6,
        "m2_slots_details": [
            {
                "interface": "PCIe",
                "supported_form_factors": ["M.2 2280", "M.2 2260"],
                "quantity": 1,
                "shared_resources": {
                    "disabled_sata_ports": [1, 2],
                },
            },
            {
                "interface": "SATA",
                "supported_form_factors": ["M.2 2280"],
                "quantity": 1,
                "shared_resources": {
                    "disabled_sata_ports": [3],
                },
            },
        ],
    }


@pytest.fixture
def nvme_specs():
    """Unidad M.2 NVMe de ejemplo."""
    return {
        "storage_type": "SSD",
        "capacity_gb": 1000,
        "interface": {
            "protocol": "NVMe",
            "connection": "PCIe",
            "generation": "4.0",
        },
        "form_factor": "M.2 2280",
    }


@pytest.fixture
def m2_sata_specs():
    """Unidad M.2 SATA de ejemplo."""
    return {
        "storage_type": "SSD",
        "capacity_gb": 500,
        "interface": {
            "protocol": "SATA",
            "connection": "M.2",
        },
        "form_factor": "M.2 2280",
    }


@pytest.fixture
def sata_specs():
    """Unidad SATA convencional de ejemplo."""
    return {
        "storage_type": "SSD",
        "capacity_gb": 500,
        "interface": {
            "protocol": "SATA",
            "connection": "SATA",
        },
        "form_factor": "2.5",
    }


# ============================================================
# Pruebas: interfaz
# ============================================================

def test_storage_interface_nvme_compatible(motherboard_specs, nvme_specs):
    result = check_storage_motherboard_interface(
        nvme_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_interface_m2_sata_compatible(
    motherboard_specs,
    m2_sata_specs,
):
    result = check_storage_motherboard_interface(
        m2_sata_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_interface_conventional_sata_compatible(
    motherboard_specs,
    sata_specs,
):
    result = check_storage_motherboard_interface(
        sata_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_interface_nvme_without_pcie_slot(
    motherboard_specs,
    nvme_specs,
):
    motherboard_specs["m2_slots_details"] = [
        {
            "interface": "SATA",
            "supported_form_factors": ["M.2 2280"],
            "quantity": 1,
        }
    ]

    result = check_storage_motherboard_interface(
        nvme_specs,
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_storage_interface_m2_sata_without_sata_slot(
    motherboard_specs,
    m2_sata_specs,
):
    motherboard_specs["m2_slots_details"] = [
        {
            "interface": "PCIe",
            "supported_form_factors": ["M.2 2280"],
            "quantity": 1,
        }
    ]

    result = check_storage_motherboard_interface(
        m2_sata_specs,
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_storage_interface_invalid_specs(motherboard_specs):
    storage_specs = {
        "interface": {
            "protocol": "NVMe",
            "connection": "SATA",
        }
    }

    result = check_storage_motherboard_interface(
        storage_specs,
        motherboard_specs,
    )

    assert result.status == "indeterminate"


def test_storage_interface_missing_m2_information(nvme_specs):
    result = check_storage_motherboard_interface(
        nvme_specs,
        {},
    )

    assert result.status == "indeterminate"


# ============================================================
# Pruebas: factor de forma
# ============================================================

def test_storage_form_factor_nvme_compatible(
    motherboard_specs,
    nvme_specs,
):
    result = check_storage_motherboard_form_factor(
        nvme_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_form_factor_m2_sata_compatible(
    motherboard_specs,
    m2_sata_specs,
):
    result = check_storage_motherboard_form_factor(
        m2_sata_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_form_factor_incompatible(
    motherboard_specs,
    nvme_specs,
):
    nvme_specs["form_factor"] = "M.2 22110"

    result = check_storage_motherboard_form_factor(
        nvme_specs,
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_storage_form_factor_conventional_sata(
    motherboard_specs,
    sata_specs,
):
    result = check_storage_motherboard_form_factor(
        sata_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_form_factor_missing(nvme_specs, motherboard_specs):
    nvme_specs.pop("form_factor")

    result = check_storage_motherboard_form_factor(
        nvme_specs,
        motherboard_specs,
    )

    assert result.status == "indeterminate"


# ============================================================
# Pruebas: disponibilidad de conexiones
# ============================================================

def test_storage_availability_nvme_compatible(
    motherboard_specs,
    nvme_specs,
):
    result = check_storage_motherboard_connection_availability(
        nvme_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_availability_m2_sata_compatible(
    motherboard_specs,
    m2_sata_specs,
):
    result = check_storage_motherboard_connection_availability(
        m2_sata_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_availability_sata_compatible(
    motherboard_specs,
    sata_specs,
):
    result = check_storage_motherboard_connection_availability(
        sata_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_storage_availability_nvme_slot_already_occupied(
    motherboard_specs,
    nvme_specs,
):
    result = check_storage_motherboard_connection_availability(
        nvme_specs,
        motherboard_specs,
        occupied_m2_slot_indexes=[0],
    )

    assert result.status == "incompatible"


def test_storage_availability_sata_ports_disabled(
    motherboard_specs,
    sata_specs,
):
    # La ranura M.2 PCIe ocupada deshabilita los puertos SATA 1 y 2.
    result = check_storage_motherboard_connection_availability(
        sata_specs,
        motherboard_specs,
        occupied_m2_slot_indexes=[0, 1],
        storage_quantity=5,
    )

    assert result.status == "incompatible"


def test_storage_availability_multiple_sata_units(
    motherboard_specs,
    sata_specs,
):
    result = check_storage_motherboard_connection_availability(
        sata_specs,
        motherboard_specs,
        storage_quantity=4,
    )

    assert result.status == "compatible"


def test_storage_availability_invalid_quantity(
    motherboard_specs,
    nvme_specs,
):
    result = check_storage_motherboard_connection_availability(
        nvme_specs,
        motherboard_specs,
        storage_quantity=0,
    )

    assert result.status == "indeterminate"


def test_storage_availability_invalid_occupied_index(
    motherboard_specs,
    sata_specs,
):
    result = check_storage_motherboard_connection_availability(
        sata_specs,
        motherboard_specs,
        occupied_m2_slot_indexes=[10],
    )

    assert result.status == "indeterminate"
