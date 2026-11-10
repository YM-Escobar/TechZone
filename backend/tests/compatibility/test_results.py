
import pytest

from app.Services.compatibility.rule_result import RuleResult
from app.Services.compatibility.results import (
    consolidate_compatibility_results,
)


# Crea resultados individuales para reutilizarlos en las pruebas.
def create_rule_result(
    rule_id: str,
    status: str,
    message: str = "Resultado de prueba."
) -> RuleResult:

    return RuleResult(
        rule_id=rule_id,
        status=status,
        message=message,
        components=["cpu", "motherboard"]
    )


# Comprueba que todas las reglas compatibles generen
# un diagnóstico global compatible.
def test_all_rules_compatible():

    results = [
        create_rule_result("cpu_socket", "compatible"),
        create_rule_result("ram_type", "compatible"),
        create_rule_result("gpu_interface", "compatible"),
    ]

    diagnostic = consolidate_compatibility_results(results)

    assert diagnostic.status == "compatible"
    assert diagnostic.is_compatible is True
    assert diagnostic.total_rules == 3
    assert diagnostic.compatible_count == 3
    assert diagnostic.incompatible_count == 0
    assert diagnostic.warning_count == 0
    assert diagnostic.indeterminate_count == 0
    assert len(diagnostic.results) == 3


# Comprueba que una incompatibilidad tenga prioridad
# sobre advertencias y resultados indeterminados.
def test_incompatible_rules_have_priority():

    results = [
        create_rule_result("cpu_socket", "compatible"),
        create_rule_result("ram_type", "incompatible"),
        create_rule_result("gpu_power", "warning"),
        create_rule_result("storage_interface", "indeterminate"),
    ]

    diagnostic = consolidate_compatibility_results(results)

    assert diagnostic.status == "incompatible"
    assert diagnostic.is_compatible is False
    assert diagnostic.total_rules == 4
    assert diagnostic.compatible_count == 1
    assert diagnostic.incompatible_count == 1
    assert diagnostic.warning_count == 1
    assert diagnostic.indeterminate_count == 1


# Comprueba que las advertencias no se consideren
# incompatibilidades definitivas.
def test_warning_rules():

    results = [
        create_rule_result("cpu_socket", "compatible"),
        create_rule_result("gpu_power", "warning"),
        create_rule_result("cooling_capacity", "warning"),
    ]

    diagnostic = consolidate_compatibility_results(results)

    assert diagnostic.status == "warning"
    assert diagnostic.is_compatible is True
    assert diagnostic.total_rules == 3
    assert diagnostic.compatible_count == 1
    assert diagnostic.incompatible_count == 0
    assert diagnostic.warning_count == 2


# Comprueba que los resultados indeterminados requieran revisión
# y no se incluyan entre los resultados visibles.
def test_indeterminate_rules_require_review():

    results = [
        create_rule_result("cpu_socket", "compatible"),
        create_rule_result("gpu_power", "indeterminate"),
    ]

    diagnostic = consolidate_compatibility_results(results)

    assert diagnostic.status == "review_required"
    assert diagnostic.is_compatible is False
    assert diagnostic.total_rules == 2
    assert diagnostic.compatible_count == 1
    assert diagnostic.indeterminate_count == 1

    assert len(diagnostic.results) == 1
    assert all(
        result.status != "indeterminate"
        for result in diagnostic.results
    )


# Comprueba que una lista vacía no se considere
# una configuración compatible.
def test_empty_results_require_review():

    diagnostic = consolidate_compatibility_results([])

    assert diagnostic.status == "review_required"
    assert diagnostic.is_compatible is False
    assert diagnostic.total_rules == 0
    assert diagnostic.compatible_count == 0
    assert diagnostic.incompatible_count == 0
    assert diagnostic.warning_count == 0
    assert diagnostic.indeterminate_count == 0
    assert diagnostic.results == []


# Comprueba el comportamiento cuando existen advertencias
# y resultados indeterminados simultáneamente.
def test_warning_and_indeterminate_rules():

    results = [
        create_rule_result("cpu_socket", "compatible"),
        create_rule_result("gpu_power", "warning"),
        create_rule_result("storage_interface", "indeterminate"),
    ]

    diagnostic = consolidate_compatibility_results(results)

    assert diagnostic.status == "review_required"
    assert diagnostic.is_compatible is False
    assert diagnostic.compatible_count == 1
    assert diagnostic.warning_count == 1
    assert diagnostic.indeterminate_count == 1

    assert len(diagnostic.results) == 2
