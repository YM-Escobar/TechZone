
import pytest

from app.Services.compatibility.rules.cpu.cpu_cooling import (
    check_cpu_cooling_socket,
    check_cpu_cooling_thermal_capacity,
)


# ============================================================
# Datos de prueba
# ============================================================

@pytest.fixture
def cpu_specs():
    """Especificaciones de ejemplo de un procesador."""
    return {
        "socket": "AM5",
        "tdp_w": 120,
    }


@pytest.fixture
def cooling_specs():
    """Especificaciones de ejemplo de una refrigeración."""
    return {
        "cooling_type": "liquid",
        "supported_sockets": ["AM4", "AM5", "LGA1700"],
        "tdp_rating_w": 150,
    }


# ============================================================
# Pruebas: CPU + refrigeración (socket)
# ============================================================

def test_cpu_cooling_socket_compatible(cpu_specs, cooling_specs):
    """El socket del procesador está soportado por la refrigeración."""
    result = check_cpu_cooling_socket(cpu_specs, cooling_specs)

    assert result.status == "compatible"
    assert result.rule_id == "cpu_cooling_socket"


def test_cpu_cooling_socket_case_insensitive(cpu_specs, cooling_specs):
    """La comparación de sockets no debe depender de mayúsculas."""
    cpu_specs["socket"] = "am5"
    cooling_specs["supported_sockets"] = ["AM4", "Am5"]

    result = check_cpu_cooling_socket(cpu_specs, cooling_specs)

    assert result.status == "compatible"


def test_cpu_cooling_socket_incompatible(cpu_specs, cooling_specs):
    """El socket del procesador no está soportado."""
    cpu_specs["socket"] = "LGA1700"
    cooling_specs["supported_sockets"] = ["AM4", "AM5"]

    result = check_cpu_cooling_socket(cpu_specs, cooling_specs)

    assert result.status == "incompatible"


@pytest.mark.parametrize(
    "cpu_socket",
    [None, "", 123],
)
def test_cpu_cooling_socket_missing_cpu_data(
    cpu_specs,
    cooling_specs,
    cpu_socket,
):
    """Un socket de CPU ausente o inválido produce indeterminate."""
    cpu_specs["socket"] = cpu_socket

    result = check_cpu_cooling_socket(cpu_specs, cooling_specs)

    assert result.status == "indeterminate"


@pytest.mark.parametrize(
    "supported_sockets",
    [None, [], ["", None, 123]],
)
def test_cpu_cooling_socket_missing_cooling_data(
    cpu_specs,
    cooling_specs,
    supported_sockets,
):
    """Una lista de sockets ausente o inválida produce indeterminate."""
    cooling_specs["supported_sockets"] = supported_sockets

    result = check_cpu_cooling_socket(cpu_specs, cooling_specs)

    assert result.status == "indeterminate"


# ============================================================
# Pruebas: CPU + refrigeración (capacidad térmica)
# ============================================================

def test_cpu_cooling_thermal_capacity_compatible(
    cpu_specs,
    cooling_specs,
):
    """La capacidad declarada supera el TDP del procesador."""
    result = check_cpu_cooling_thermal_capacity(
        cpu_specs,
        cooling_specs,
    )

    assert result.status == "compatible"
    assert result.rule_id == "cpu_cooling_thermal_capacity"


def test_cpu_cooling_thermal_capacity_warning(
    cpu_specs,
    cooling_specs,
):
    """La capacidad declarada es inferior al TDP del procesador."""
    cooling_specs["tdp_rating_w"] = 95

    result = check_cpu_cooling_thermal_capacity(
        cpu_specs,
        cooling_specs,
    )

    assert result.status == "warning"


def test_cpu_cooling_thermal_capacity_equal(
    cpu_specs,
    cooling_specs,
):
    """Una capacidad igual al TDP no genera advertencia."""
    cooling_specs["tdp_rating_w"] = 120

    result = check_cpu_cooling_thermal_capacity(
        cpu_specs,
        cooling_specs,
    )

    assert result.status == "compatible"


@pytest.mark.parametrize(
    ("cpu_tdp", "cooling_tdp"),
    [
        (None, 150),
        (120, None),
        (0, 150),
        (120, 0),
        (-1, 150),
        (120, -1),
        (120.5, 150),
        (120, 150.5),
        (True, 150),
        (120, True),
    ],
)
def test_cpu_cooling_thermal_capacity_invalid_data(
    cpu_specs,
    cooling_specs,
    cpu_tdp,
    cooling_tdp,
):
    """Los valores térmicos ausentes o inválidos producen indeterminate."""
    cpu_specs["tdp_w"] = cpu_tdp
    cooling_specs["tdp_rating_w"] = cooling_tdp

    result = check_cpu_cooling_thermal_capacity(
        cpu_specs,
        cooling_specs,
    )

    assert result.status == "indeterminate"
