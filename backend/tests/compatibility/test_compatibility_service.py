
# Importa la clase que coordina el proceso de compatibilidad.
from app.Services.compatibility.compatibility_service import CompatibilityService

# Importa la estructura de los resultados individuales.
from app.Services.compatibility.rule_result import RuleResult


# Crea una instancia del servicio para reutilizarla en las pruebas.
service = CompatibilityService()


def test_service_consolidates_compatible_results(monkeypatch):
    """Comprueba que el servicio consolide correctamente los resultados."""

    # Simula los resultados que devolvería el motor de reglas.
    rule_results = [
        RuleResult(
            rule_id="cpu_motherboard_socket",
            status="compatible",
            message="Los sockets coinciden.",
            components=["CPU", "Motherboard"],
        ),
        RuleResult(
            rule_id="ram_motherboard_type",
            status="compatible",
            message="El tipo de memoria es compatible.",
            components=["RAM", "Motherboard"],
        ),
    ]

    # Sustituye temporalmente el motor real por uno controlado.
    monkeypatch.setattr(
        "app.Services.compatibility.compatibility_service.run_compatibility_rules",
        lambda components: rule_results,
    )

    # Ejecuta el servicio.
    diagnostic = service.evaluate({"cpu": {"name": "CPU de prueba"}})

    # Comprueba que el diagnóstico sea compatible.
    assert diagnostic.status == "compatible"
    assert diagnostic.is_compatible is True
    assert diagnostic.compatible_count == 2
    assert diagnostic.total_rules == 2


def test_service_detects_incompatible_components(monkeypatch):
    """Comprueba que el servicio detecte incompatibilidades."""

    # Simula una regla que encuentra una incompatibilidad.
    rule_results = [
        RuleResult(
            rule_id="cpu_motherboard_socket",
            status="incompatible",
            message="Los sockets no coinciden.",
            components=["CPU", "Motherboard"],
        ),
    ]

    # Simula la respuesta del motor.
    monkeypatch.setattr(
        "app.Services.compatibility.compatibility_service.run_compatibility_rules",
        lambda components: rule_results,
    )

    # Ejecuta el servicio.
    diagnostic = service.evaluate({})

    # Comprueba que la incompatibilidad se refleje en el diagnóstico.
    assert diagnostic.status == "incompatible"
    assert diagnostic.is_compatible is False
    assert diagnostic.incompatible_count == 1


def test_service_requires_review_when_results_are_indeterminate(monkeypatch):
    """Comprueba que los resultados indeterminados requieran revisión."""

    # Simula una regla que no pudo determinar la compatibilidad.
    rule_results = [
        RuleResult(
            rule_id="cpu_motherboard_model",
            status="indeterminate",
            message="Falta información técnica.",
            components=["CPU", "Motherboard"],
        ),
    ]

    # Simula la respuesta del motor.
    monkeypatch.setattr(
        "app.Services.compatibility.compatibility_service.run_compatibility_rules",
        lambda components: rule_results,
    )

    # Ejecuta el servicio.
    diagnostic = service.evaluate({})

    # Comprueba que se solicite revisión.
    assert diagnostic.status == "review_required"
    assert diagnostic.is_compatible is False
    assert diagnostic.indeterminate_count == 1


def test_service_requires_review_when_no_rules_are_executed(monkeypatch):
    """Comprueba el comportamiento cuando el motor no devuelve resultados."""

    # Simula un motor que no encuentra reglas para ejecutar.
    monkeypatch.setattr(
        "app.Services.compatibility.compatibility_service.run_compatibility_rules",
        lambda components: [],
    )

    # Ejecuta el servicio con una configuración vacía.
    diagnostic = service.evaluate({})

    # Sin reglas ejecutadas no se debe afirmar que todo es compatible.
    assert diagnostic.status == "review_required"
    assert diagnostic.is_compatible is False
    assert diagnostic.total_rules == 0


def test_service_passes_components_to_engine(monkeypatch):
    """Comprueba que el servicio envíe los componentes al motor."""

    # Define una configuración de prueba.
    components = {
        "cpu": {"name": "CPU de prueba"},
        "ram": [],
    }

    # Almacena los componentes recibidos por el motor simulado.
    received_components = {}

    def fake_engine(received):
        received_components["components"] = received
        return []

    # Sustituye el motor real por la función de prueba.
    monkeypatch.setattr(
        "app.Services.compatibility.compatibility_service.run_compatibility_rules",
        fake_engine,
    )

    # Ejecuta el servicio.
    service.evaluate(components)

    # Comprueba que el servicio haya enviado la misma configuración.
    assert received_components["components"] is components
