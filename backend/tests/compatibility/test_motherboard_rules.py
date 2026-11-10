
import pytest

from app.Services.compatibility.rules.motherboard.cpu_motherboard import (
    check_cpu_motherboard_socket,
    check_cpu_motherboard_model,
    check_cpu_motherboard_memory_type,
)



# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def cpu_specs():
    """Especificaciones de ejemplo de un procesador."""
    return {
        "socket": "AM5",
        "supported_memory_types": ["DDR5"],
    }


@pytest.fixture
def motherboard_specs():
    """Especificaciones de ejemplo de una motherboard."""
    return {
        "socket": "AM5",
        "memory_type": "DDR5",
        "supported_cpu_models": [
            {
                "model": "AMD Ryzen 7 7800X3D",
            },
            {
                "model": "AMD Ryzen 9 7950X",
                "min_bios_version": "1.20",
            },
        ],
    }


# ============================================================
# Pruebas: CPU + motherboard (socket)
# ============================================================

def test_cpu_motherboard_socket_compatible(
    cpu_specs,
    motherboard_specs,
):
    """Ambos componentes utilizan el mismo socket."""
    result = check_cpu_motherboard_socket(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_cpu_motherboard_socket_incompatible(
    cpu_specs,
    motherboard_specs,
):
    """Los sockets de ambos componentes son diferentes."""
    cpu_specs["socket"] = "AM4"

    result = check_cpu_motherboard_socket(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_cpu_motherboard_socket_case_insensitive(
    cpu_specs,
    motherboard_specs,
):
    """La comparación de sockets ignora mayúsculas y minúsculas."""
    cpu_specs["socket"] = "am5"

    result = check_cpu_motherboard_socket(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


@pytest.mark.parametrize(
    "socket",
    [None, "", 123],
)
def test_cpu_motherboard_socket_missing_cpu_data(
    cpu_specs,
    motherboard_specs,
    socket,
):
    """Un socket ausente o inválido produce indeterminate."""
    cpu_specs["socket"] = socket

    result = check_cpu_motherboard_socket(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "indeterminate"


@pytest.mark.parametrize(
    "socket",
    [None, "", 123],
)
def test_cpu_motherboard_socket_missing_motherboard_data(
    cpu_specs,
    motherboard_specs,
    socket,
):
    """Un socket de motherboard ausente o inválido produce indeterminate."""
    motherboard_specs["socket"] = socket

    result = check_cpu_motherboard_socket(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "indeterminate"


# ============================================================
# Pruebas: CPU + motherboard (modelo y BIOS)
# ============================================================

def test_cpu_motherboard_model_compatible(motherboard_specs):
    """El modelo de CPU aparece en la lista de modelos soportados."""
    result = check_cpu_motherboard_model(
        "AMD Ryzen 7 7800X3D",
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_cpu_motherboard_model_requires_bios(motherboard_specs):
    """El modelo requiere verificar una versión mínima de BIOS."""
    result = check_cpu_motherboard_model(
        "AMD Ryzen 9 7950X",
        motherboard_specs,
    )

    assert result.status == "warning"


def test_cpu_motherboard_model_incompatible(motherboard_specs):
    """El modelo de CPU no aparece entre los modelos soportados."""
    result = check_cpu_motherboard_model(
        "Intel Core i9-14900K",
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_cpu_motherboard_model_without_supported_list():
    """Una lista de modelos ausente produce indeterminate."""
    result = check_cpu_motherboard_model(
        "AMD Ryzen 7 7800X3D",
        {},
    )

    assert result.status == "indeterminate"


def test_cpu_motherboard_model_case_insensitive(motherboard_specs):
    """La comparación del modelo ignora diferencias de mayúsculas."""
    result = check_cpu_motherboard_model(
        "amd ryzen 7 7800x3d",
        motherboard_specs,
    )

    assert result.status == "compatible"


# ============================================================
# Pruebas: CPU + motherboard (tipo de memoria)
# ============================================================

def test_cpu_motherboard_memory_type_compatible(
    cpu_specs,
    motherboard_specs,
):
    """CPU y motherboard soportan DDR5."""
    result = check_cpu_motherboard_memory_type(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_cpu_motherboard_memory_type_incompatible(
    cpu_specs,
    motherboard_specs,
):
    """La motherboard utiliza un tipo de memoria no soportado por la CPU."""
    motherboard_specs["memory_type"] = "DDR4"

    result = check_cpu_motherboard_memory_type(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "incompatible"


def test_cpu_motherboard_memory_type_case_insensitive(
    cpu_specs,
    motherboard_specs,
):
    """La comparación del tipo de memoria ignora mayúsculas."""
    motherboard_specs["memory_type"] = "ddr5"

    result = check_cpu_motherboard_memory_type(
        cpu_specs,
        motherboard_specs,
    )

    assert result.status == "compatible"


def test_cpu_motherboard_memory_type_missing_cpu_data(
    motherboard_specs,
):
    """La ausencia de tipos de memoria soportados produce indeterminate."""
    result = check_cpu_motherboard_memory_type(
        {},
        motherboard_specs,
    )

    assert result.status == "indeterminate"


def test_cpu_motherboard_memory_type_missing_motherboard_data(
    cpu_specs,
):
    """La ausencia del tipo de memoria de la motherboard produce indeterminate."""
    result = check_cpu_motherboard_memory_type(
        cpu_specs,
        {},
    )

    assert result.status == "indeterminate"
