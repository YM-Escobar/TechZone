
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def check_multiple_gpu_psu_wattage(
    gpu_components: list[dict[str, Any]],
    psu_specs: dict[str, Any],
) -> RuleResult:
    if not isinstance(gpu_components, list) or not gpu_components:
        return RuleResult(
            rule_id="multiple_gpu_psu_wattage",
            status="indeterminate",
            message="No hay información suficiente para comprobar la potencia conjunta de las GPU.",
            components=["gpu", "psu"],
        )

    if not isinstance(psu_specs, dict):
        return RuleResult(
            rule_id="multiple_gpu_psu_wattage",
            status="indeterminate",
            message="No hay información suficiente sobre la potencia de la fuente.",
            components=["gpu", "psu"],
        )

    psu_wattage = psu_specs.get("wattage_w")

    if not _is_positive_int(psu_wattage):
        return RuleResult(
            rule_id="multiple_gpu_psu_wattage",
            status="indeterminate",
            message="La potencia de la fuente está incompleta o es inválida.",
            components=["gpu", "psu"],
        )

    total_gpu_power = 0

    for gpu in gpu_components:
        if not isinstance(gpu, dict):
            return RuleResult(
                rule_id="multiple_gpu_psu_wattage",
                status="indeterminate",
                message="La información de las GPU contiene datos inválidos.",
                components=["gpu", "psu"],
            )

        specs = gpu.get("specs")
        quantity = gpu.get("quantity", 1)

        if (
            not isinstance(specs, dict)
            or not _is_positive_int(quantity)
        ):
            return RuleResult(
                rule_id="multiple_gpu_psu_wattage",
                status="indeterminate",
                message="Las especificaciones o cantidades de las GPU están incompletas.",
                components=["gpu", "psu"],
            )

        board_power = specs.get("board_power_w")

        if not _is_positive_int(board_power):
            return RuleResult(
                rule_id="multiple_gpu_psu_wattage",
                status="indeterminate",
                message="No hay información suficiente sobre el consumo de todas las GPU.",
                components=["gpu", "psu"],
            )

        total_gpu_power += board_power * quantity

    if total_gpu_power > psu_wattage:
        return RuleResult(
            rule_id="multiple_gpu_psu_wattage",
            status="warning",
            message=(
                f"Las GPU requieren conjuntamente {total_gpu_power} W, "
                f"superando los {psu_wattage} W de la fuente."
            ),
            components=["gpu", "psu"],
        )

    return RuleResult(
        rule_id="multiple_gpu_psu_wattage",
        status="compatible",
        message=(
            f"Las GPU requieren conjuntamente {total_gpu_power} W "
            f"y no superan los {psu_wattage} W de la fuente. "
            "Esta comprobación no garantiza la suficiencia para el equipo completo."
        ),
        components=["gpu", "psu"],
    )


def check_multiple_gpu_psu_connectors(
    gpu_components: list[dict[str, Any]],
    psu_specs: dict[str, Any],
) -> RuleResult:
    if not isinstance(gpu_components, list) or not gpu_components:
        return RuleResult(
            rule_id="multiple_gpu_psu_connectors",
            status="indeterminate",
            message="No hay información suficiente para comprobar los conectores de las GPU.",
            components=["gpu", "psu"],
        )

    if not isinstance(psu_specs, dict):
        return RuleResult(
            rule_id="multiple_gpu_psu_connectors",
            status="indeterminate",
            message="No hay información suficiente sobre los conectores de la fuente.",
            components=["gpu", "psu"],
        )

    available_connectors = psu_specs.get("power_connectors")

    if not isinstance(available_connectors, list):
        return RuleResult(
            rule_id="multiple_gpu_psu_connectors",
            status="indeterminate",
            message="No hay información suficiente sobre los conectores de la fuente.",
            components=["gpu", "psu"],
        )

    required = {}

    for gpu in gpu_components:
        if not isinstance(gpu, dict):
            return RuleResult(
                rule_id="multiple_gpu_psu_connectors",
                status="indeterminate",
                message="La información de las GPU contiene datos inválidos.",
                components=["gpu", "psu"],
            )

        specs = gpu.get("specs")
        quantity = gpu.get("quantity", 1)

        if (
            not isinstance(specs, dict)
            or not _is_positive_int(quantity)
        ):
            return RuleResult(
                rule_id="multiple_gpu_psu_connectors",
                status="indeterminate",
                message="Las especificaciones o cantidades de las GPU están incompletas.",
                components=["gpu", "psu"],
            )

        required_connectors = specs.get("power_connectors_required")

        if not isinstance(required_connectors, list):
            return RuleResult(
                rule_id="multiple_gpu_psu_connectors",
                status="indeterminate",
                message="No hay información suficiente sobre los conectores requeridos por las GPU.",
                components=["gpu", "psu"],
            )

        for connector in required_connectors:
            if not isinstance(connector, dict):
                return RuleResult(
                    rule_id="multiple_gpu_psu_connectors",
                    status="indeterminate",
                    message="Los conectores requeridos por las GPU contienen datos inválidos.",
                    components=["gpu", "psu"],
                )

            connector_type = connector.get("type")
            connector_quantity = connector.get("quantity")

            if (
                not isinstance(connector_type, str)
                or not connector_type.strip()
                or not _is_positive_int(connector_quantity)
            ):
                return RuleResult(
                    rule_id="multiple_gpu_psu_connectors",
                    status="indeterminate",
                    message="Los conectores requeridos por las GPU están incompletos.",
                    components=["gpu", "psu"],
                )

            normalized_type = connector_type.strip().casefold()
            required[normalized_type] = (
                required.get(normalized_type, 0)
                + connector_quantity * quantity
            )

    available = {}

    for connector in available_connectors:
        if not isinstance(connector, dict):
            return RuleResult(
                rule_id="multiple_gpu_psu_connectors",
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
                rule_id="multiple_gpu_psu_connectors",
                status="indeterminate",
                message="La información de los conectores de la fuente está incompleta.",
                components=["gpu", "psu"],
            )

        if native:
            normalized_type = connector_type.strip().casefold()
            available[normalized_type] = (
                available.get(normalized_type, 0) + quantity
            )

    if not required:
        return RuleResult(
            rule_id="multiple_gpu_psu_connectors",
            status="compatible",
            message="Las GPU no requieren conectores adicionales de alimentación.",
            components=["gpu", "psu"],
        )

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
            rule_id="multiple_gpu_psu_connectors",
            status="incompatible",
            message=(
                "La fuente no dispone de suficientes conectores "
                "nativos para alimentar todas las GPU. "
                + "; ".join(missing)
            ),
            components=["gpu", "psu"],
        )

    return RuleResult(
        rule_id="multiple_gpu_psu_connectors",
        status="compatible",
        message="La fuente dispone de suficientes conectores nativos para todas las GPU.",
        components=["gpu", "psu"],
    )
