
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


def _is_positive_int(value: Any) -> bool:
    """Comprueba que un valor sea un entero positivo, sin aceptar booleanos."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_gpu_psu_wattage(
    gpu_specs: dict[str, Any],
    psu_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba si la potencia de la fuente alcanza la recomendación
    indicada por el fabricante de la GPU.

    Una potencia inferior genera una advertencia, no una incompatibilidad.
    """
    gpu_recommended_psu = gpu_specs.get("recommended_psu_w")
    psu_wattage = psu_specs.get("wattage_w")

    # Verificar que ambas potencias sean valores válidos.
    if (
        not _is_positive_int(gpu_recommended_psu)
        or not _is_positive_int(psu_wattage)
    ):
        return RuleResult(
            rule_id="gpu_psu_wattage",
            status="indeterminate",
            message="No hay información suficiente para comprobar la potencia de la fuente.",
            components=["gpu", "psu"],
        )

    # La potencia inferior a la recomendada es una advertencia.
    if psu_wattage < gpu_recommended_psu:
        return RuleResult(
            rule_id="gpu_psu_wattage",
            status="warning",
            message=(
                f"La fuente proporciona {psu_wattage} W, "
                f"pero el fabricante recomienda al menos "
                f"{gpu_recommended_psu} W para la GPU."
            ),
            components=["gpu", "psu"],
        )

    return RuleResult(
        rule_id="gpu_psu_wattage",
        status="compatible",
        message=(
            f"La fuente proporciona {psu_wattage} W y cumple "
            f"la recomendación de {gpu_recommended_psu} W de la GPU."
        ),
        components=["gpu", "psu"],
    )


def check_gpu_psu_connectors(
    gpu_specs: dict[str, Any],
    psu_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba que la fuente tenga los conectores nativos
    necesarios para alimentar la GPU.

    No se consideran adaptadores ni equivalencias entre conectores.
    """
    required_connectors = gpu_specs.get("power_connectors_required")
    available_connectors = psu_specs.get("power_connectors")

    # Comprobar que los datos sean listas.
    if (
        not isinstance(required_connectors, list)
        or not isinstance(available_connectors, list)
    ):
        return RuleResult(
            rule_id="gpu_psu_connectors",
            status="indeterminate",
            message="No hay información suficiente sobre los conectores de alimentación.",
            components=["gpu", "psu"],
        )

    # Una GPU sin conectores adicionales no necesita comprobaciones.
    if not required_connectors:
        return RuleResult(
            rule_id="gpu_psu_connectors",
            status="compatible",
            message="La GPU no requiere conectores adicionales de alimentación.",
            components=["gpu", "psu"],
        )

    # Validar los conectores requeridos por la GPU.
    required = {}

    for connector in required_connectors:
        if not isinstance(connector, dict):
            return RuleResult(
                rule_id="gpu_psu_connectors",
                status="indeterminate",
                message="Los conectores requeridos por la GPU contienen datos inválidos.",
                components=["gpu", "psu"],
            )

        connector_type = connector.get("type")
        quantity = connector.get("quantity")

        if (
            not isinstance(connector_type, str)
            or not connector_type.strip()
            or not _is_positive_int(quantity)
        ):
            return RuleResult(
                rule_id="gpu_psu_connectors",
                status="indeterminate",
                message="Los conectores requeridos por la GPU están incompletos.",
                components=["gpu", "psu"],
            )

        normalized_type = connector_type.strip().casefold()
        required[normalized_type] = (
            required.get(normalized_type, 0) + quantity
        )

    # Validar y contabilizar únicamente conectores nativos de la fuente.
    available = {}

    if not available_connectors:
        return RuleResult(
            rule_id="gpu_psu_connectors",
            status="incompatible",
            message="La fuente no tiene registrados los conectores requeridos por la GPU.",
            components=["gpu", "psu"],
        )

    for connector in available_connectors:
        if not isinstance(connector, dict):
            return RuleResult(
                rule_id="gpu_psu_connectors",
                status="indeterminate",
                message="Los conectores registrados en la fuente contienen datos inválidos.",
                components=["gpu", "psu"],
            )

        connector_type = connector.get("type")
        quantity = connector.get("quantity")
        native = connector.get("native")

        if (
            not isinstance(connector_type, str)
            or not connector_type.strip()
            or not _is_positive_int(quantity)
            or not isinstance(native, bool)
        ):
            return RuleResult(
                rule_id="gpu_psu_connectors",
                status="indeterminate",
                message="La información de los conectores de la fuente está incompleta.",
                components=["gpu", "psu"],
            )

        # Solo se cuentan los conectores nativos.
        if native:
            normalized_type = connector_type.strip().casefold()
            available[normalized_type] = (
                available.get(normalized_type, 0) + quantity
            )

    # Comparar cantidades disponibles con las requeridas.
    missing = []

    for connector_type, required_quantity in required.items():
        available_quantity = available.get(connector_type, 0)

        if available_quantity < required_quantity:
            missing.append(
                f"{connector_type}: necesita {required_quantity}, "
                f"dispone de {available_quantity}"
            )

    if missing:
        return RuleResult(
            rule_id="gpu_psu_connectors",
            status="incompatible",
            message=(
                "La fuente no dispone de suficientes conectores "
                "nativos requeridos por la GPU. "
                + "; ".join(missing)
            ),
            components=["gpu", "psu"],
        )

    return RuleResult(
        rule_id="gpu_psu_connectors",
        status="compatible",
        message="La fuente dispone de los conectores nativos requeridos por la GPU.",
        components=["gpu", "psu"],
    )
