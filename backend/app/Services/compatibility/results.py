
from dataclasses import dataclass
from typing import Literal

from app.Services.compatibility.rule_result import RuleResult


# Estados posibles del diagnóstico global.
# review_required evita exponer el estado interno indeterminate.
CompatibilityStatus = Literal[
    "compatible",
    "incompatible",
    "warning",
    "review_required"
]


# Estructura estandarizada del diagnóstico de compatibilidad.
@dataclass
class CompatibilityResult:

    # Estado general de la configuración.
    status: CompatibilityStatus

    # Indica si se encontraron incompatibilidades.
    is_compatible: bool

    # Explicación general del diagnóstico.
    summary: str

    # Cantidad total de reglas ejecutadas.
    total_rules: int

    # Cantidad de reglas compatibles.
    compatible_count: int

    # Cantidad de reglas incompatibles.
    incompatible_count: int

    # Cantidad de reglas que generan advertencias.
    warning_count: int

    # Cantidad de reglas que no pudieron verificarse.
    # Este dato es interno y no debe exponerse directamente al usuario.
    indeterminate_count: int

    # Resultados individuales que sí pueden mostrarse.
    results: list[RuleResult]


# Consolida los resultados individuales del Engine
# en un diagnóstico general de compatibilidad.
def consolidate_compatibility_results(
    rule_results: list[RuleResult]
) -> CompatibilityResult:

    # Inicializa los contadores de cada estado.
    compatible_count = 0
    incompatible_count = 0
    warning_count = 0
    indeterminate_count = 0

    # Almacena los resultados que pueden mostrarse al usuario.
    visible_results: list[RuleResult] = []

    # Recorre los resultados de todas las reglas ejecutadas.
    for result in rule_results:

        if result.status == "compatible":
            compatible_count += 1
            visible_results.append(result)

        elif result.status == "incompatible":
            incompatible_count += 1
            visible_results.append(result)

        elif result.status == "warning":
            warning_count += 1
            visible_results.append(result)

        elif result.status == "indeterminate":
            # Se contabiliza internamente, pero no se muestra
            # como resultado individual al usuario.
            indeterminate_count += 1

    # Calcula la cantidad total de reglas ejecutadas.
    total_rules = len(rule_results)


    # Determina el estado global de la configuración.
    if total_rules == 0:
        status: CompatibilityStatus = "review_required"

        summary = (
            "No se ejecutaron reglas de compatibilidad. "
            "No es posible determinar si la configuración es compatible."
        )

    elif incompatible_count > 0:
        status = "incompatible"

        summary = (
            f"Se encontraron {incompatible_count} incompatibilidades "
            "en la configuración."
        )

    elif indeterminate_count > 0:
        status = "review_required"

        summary = (
            "No fue posible verificar completamente la configuración "
            "con la información técnica disponible."
        )

    elif warning_count > 0:
        status = "warning"

        summary = (
            f"La configuración no presenta incompatibilidades, "
            f"pero tiene {warning_count} advertencias que deben revisarse."
        )

    else:
        status = "compatible"

        summary = (
            "La configuración es compatible según las reglas evaluadas."
        )

    # Una configuración es compatible si se ejecutaron reglas
    # y no existen incompatibilidades ni validaciones pendientes.
    is_compatible = (
        total_rules > 0
        and incompatible_count == 0
        and indeterminate_count == 0
    )

    # Devuelve el diagnóstico consolidado.
    return CompatibilityResult(
        status=status,
        is_compatible=is_compatible,
        summary=summary,
        total_rules=total_rules,
        compatible_count=compatible_count,
        incompatible_count=incompatible_count,
        warning_count=warning_count,
        indeterminate_count=indeterminate_count,
        results=visible_results
    )
