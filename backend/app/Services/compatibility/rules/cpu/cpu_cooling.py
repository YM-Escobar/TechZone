
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


def check_cpu_cooling_socket(
    cpu_specs: dict[str, Any],
    cooling_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba si la refrigeración admite el socket del procesador.

    La comparación ignora diferencias entre mayúsculas y minúsculas
    y espacios al inicio o al final.
    """
    cpu_socket = cpu_specs.get("socket")
    supported_sockets = cooling_specs.get("supported_sockets")

    # Verificar que exista información válida del socket de la CPU.
    if not isinstance(cpu_socket, str) or not cpu_socket.strip():
        return RuleResult(
            rule_id="cpu_cooling_socket",
            status="indeterminate",
            message="No se conoce el socket del procesador.",
            components=["cpu", "cooling"],
        )

    # Verificar que la refrigeración tenga una lista de sockets soportados.
    if not isinstance(supported_sockets, list) or not supported_sockets:
        return RuleResult(
            rule_id="cpu_cooling_socket",
            status="indeterminate",
            message="No hay información sobre los sockets compatibles con la refrigeración.",
            components=["cpu", "cooling"],
        )

    # Normalizar los sockets registrados para facilitar la comparación.
    normalized_sockets = []

    for socket in supported_sockets:
        if not isinstance(socket, str) or not socket.strip():
            continue

        normalized_sockets.append(socket.strip().casefold())

    if not normalized_sockets:
        return RuleResult(
            rule_id="cpu_cooling_socket",
            status="indeterminate",
            message="La lista de sockets soportados por la refrigeración no contiene datos válidos.",
            components=["cpu", "cooling"],
        )

    # Comprobar si el socket de la CPU está soportado.
    if cpu_socket.strip().casefold() not in normalized_sockets:
        return RuleResult(
            rule_id="cpu_cooling_socket",
            status="incompatible",
            message=(
                f"La refrigeración no declara soporte para el socket "
                f"{cpu_socket.strip()} del procesador."
            ),
            components=["cpu", "cooling"],
        )

    return RuleResult(
        rule_id="cpu_cooling_socket",
        status="compatible",
        message=(
            f"La refrigeración declara soporte para el socket "
            f"{cpu_socket.strip()} del procesador."
        ),
        components=["cpu", "cooling"],
    )


def check_cpu_cooling_thermal_capacity(
    cpu_specs: dict[str, Any],
    cooling_specs: dict[str, Any],
) -> RuleResult:
    """
    Compara el TDP del procesador con la capacidad térmica
    declarada por el fabricante de la refrigeración.

    Esta comparación es orientativa y no garantiza por sí sola
    que la refrigeración mantenga temperaturas adecuadas.
    """
    cpu_tdp = cpu_specs.get("tdp_w")
    cooling_tdp_rating = cooling_specs.get("tdp_rating_w")

    # Validar que ambos valores sean enteros positivos.
    if (
        not isinstance(cpu_tdp, int)
        or isinstance(cpu_tdp, bool)
        or cpu_tdp <= 0
        or not isinstance(cooling_tdp_rating, int)
        or isinstance(cooling_tdp_rating, bool)
        or cooling_tdp_rating <= 0
    ):
        return RuleResult(
            rule_id="cpu_cooling_thermal_capacity",
            status="indeterminate",
            message=(
                "No hay información térmica suficiente para comparar "
                "el procesador con la refrigeración."
            ),
            components=["cpu", "cooling"],
        )

    # Una capacidad térmica inferior genera una advertencia.
    if cooling_tdp_rating < cpu_tdp:
        return RuleResult(
            rule_id="cpu_cooling_thermal_capacity",
            status="warning",
            message=(
                f"El procesador tiene un TDP de {cpu_tdp} W, "
                f"mientras que la refrigeración declara "
                f"{cooling_tdp_rating} W de capacidad térmica. "
                "La capacidad declarada es inferior al TDP del procesador."
            ),
            components=["cpu", "cooling"],
        )

    return RuleResult(
        rule_id="cpu_cooling_thermal_capacity",
        status="compatible",
        message=(
            f"La refrigeración declara {cooling_tdp_rating} W de capacidad "
            f"térmica frente a los {cpu_tdp} W de TDP del procesador. "
            "Esta comparación es orientativa y no garantiza "
            "por sí sola el rendimiento térmico."
        ),
        components=["cpu", "cooling"],
    )
