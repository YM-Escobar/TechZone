
import pytest

from app.Services.compatibility.rules.ram.ram_motherboard import (
    check_ram_motherboard_memory_type,
    check_ram_motherboard_capacity,
    check_ram_motherboard_slots,
)
from app.Services.compatibility.rules.ram.ram_cpu import (
    check_ram_cpu_capacity,
)


# ==========================================================
# DATOS DE PRUEBA
# ==========================================================

# RAM DDR5 de 32 GB, distribuida en dos módulos.
@pytest.fixture
def ram_specs():
    return {
        "memory_type": "DDR5",
        "capacity_per_module_gb": 16,
        "total_capacity_gb": 32,
        "module_count": 2,
        "frequency_mhz": 6000,
        "form_factor": "DIMM",
    }


# Motherboard con soporte para DDR5, 128 GB y cuatro slots.
@pytest.fixture
def motherboard_specs():
    return {
        "memory_type": "DDR5",
        "max_memory_gb": 128,
        "memory_slots": 4,
    }


# Procesador con capacidad máxima de memoria de 128 GB.
@pytest.fixture
def cpu_specs():
    return {
        "max_memory_gb": 128,
    }


# ==========================================================
# PRUEBAS: TIPO DE MEMORIA
# ==========================================================

def test_ram_motherboard_memory_type_compatible(
    ram_specs,
    motherboard_specs
):
    result = check_ram_motherboard_memory_type(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "compatible"


def test_ram_motherboard_memory_type_incompatible(
    ram_specs,
    motherboard_specs
):
    motherboard_specs["memory_type"] = "DDR4"

    result = check_ram_motherboard_memory_type(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "incompatible"


def test_ram_motherboard_memory_type_missing_data(
    ram_specs,
    motherboard_specs
):
    motherboard_specs.pop("memory_type")

    result = check_ram_motherboard_memory_type(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "indeterminate"


def test_ram_motherboard_memory_type_case_insensitive(
    ram_specs,
    motherboard_specs
):
    ram_specs["memory_type"] = "ddr5"

    result = check_ram_motherboard_memory_type(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "compatible"


# ==========================================================
# PRUEBAS: CAPACIDAD MÁXIMA DE MOTHERBOARD
# ==========================================================

def test_ram_motherboard_capacity_compatible(
    ram_specs,
    motherboard_specs
):
    result = check_ram_motherboard_capacity(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "compatible"


def test_ram_motherboard_capacity_incompatible(
    ram_specs,
    motherboard_specs
):
    motherboard_specs["max_memory_gb"] = 16

    result = check_ram_motherboard_capacity(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "incompatible"


def test_ram_motherboard_capacity_multiple_kits(
    ram_specs,
    motherboard_specs
):
    result = check_ram_motherboard_capacity(
        ram_specs,
        motherboard_specs,
        ram_quantity=2
    )

    assert result.status == "compatible"
    assert "64 GB" in result.message


def test_ram_motherboard_capacity_invalid_quantity(
    ram_specs,
    motherboard_specs
):
    result = check_ram_motherboard_capacity(
        ram_specs,
        motherboard_specs,
        ram_quantity=0
    )

    assert result.status == "indeterminate"


# ==========================================================
# PRUEBAS: SLOTS DE MOTHERBOARD
# ==========================================================

def test_ram_motherboard_slots_compatible(
    ram_specs,
    motherboard_specs
):
    result = check_ram_motherboard_slots(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "compatible"


def test_ram_motherboard_slots_incompatible(
    ram_specs,
    motherboard_specs
):
    motherboard_specs["memory_slots"] = 2

    result = check_ram_motherboard_slots(
        ram_specs,
        motherboard_specs,
        ram_quantity=2
    )

    assert result.status == "incompatible"


def test_ram_motherboard_slots_multiple_kits(
    ram_specs,
    motherboard_specs
):
    result = check_ram_motherboard_slots(
        ram_specs,
        motherboard_specs,
        ram_quantity=2
    )

    assert result.status == "compatible"
    assert "4 módulos" in result.message


def test_ram_motherboard_slots_missing_data(
    ram_specs,
    motherboard_specs
):
    motherboard_specs.pop("memory_slots")

    result = check_ram_motherboard_slots(
        ram_specs,
        motherboard_specs
    )

    assert result.status == "indeterminate"


# ==========================================================
# PRUEBAS: CAPACIDAD MÁXIMA DE CPU
# ==========================================================

def test_ram_cpu_capacity_compatible(
    ram_specs,
    cpu_specs
):
    result = check_ram_cpu_capacity(
        ram_specs,
        cpu_specs
    )

    assert result.status == "compatible"


def test_ram_cpu_capacity_incompatible(
    ram_specs,
    cpu_specs
):
    cpu_specs["max_memory_gb"] = 16

    result = check_ram_cpu_capacity(
        ram_specs,
        cpu_specs
    )

    assert result.status == "incompatible"


def test_ram_cpu_capacity_multiple_kits(
    ram_specs,
    cpu_specs
):
    result = check_ram_cpu_capacity(
        ram_specs,
        cpu_specs,
        ram_quantity=2
    )

    assert result.status == "compatible"
    assert "64 GB" in result.message


def test_ram_cpu_capacity_missing_data(
    ram_specs,
    cpu_specs
):
    cpu_specs.pop("max_memory_gb")

    result = check_ram_cpu_capacity(
        ram_specs,
        cpu_specs
    )

    assert result.status == "indeterminate"


def test_ram_cpu_capacity_invalid_quantity(
    ram_specs,
    cpu_specs
):
    result = check_ram_cpu_capacity(
        ram_specs,
        cpu_specs,
        ram_quantity=-1
    )

    assert result.status == "indeterminate"
