from typing import Any

from app.Services.compatibility.rule_result import RuleResult


# Comprueba la compatibilidad del socket entre CPU y motherboard.

def check_cpu_motherboard_socket(
    cpu_specs: dict[str, Any],
    motherboard_specs: dict[str, Any]
) -> RuleResult:

    # Obtiene los sockets de ambos componentes.
    cpu_socket = cpu_specs.get("socket")
    motherboard_socket = motherboard_specs.get("socket")

    # Verifica que ambos valores sean cadenas de texto no vacías.
    # Si algún dato falta o tiene un tipo incorrecto, no se puede determinar.
    if (
        not isinstance(cpu_socket, str)
        or not cpu_socket.strip()
        or not isinstance(motherboard_socket, str)
        or not motherboard_socket.strip()
    ):
        return RuleResult(
            rule_id="cpu_motherboard_socket",
            status="indeterminate",
            message="No hay información suficiente para verificar los sockets.",
            components=["cpu", "motherboard"]
        )

    # Compara los sockets ignorando mayúsculas y espacios externos.
    if cpu_socket.strip().casefold() == motherboard_socket.strip().casefold():
        return RuleResult(
            rule_id="cpu_motherboard_socket",
            status="compatible",
            message="El procesador y la motherboard utilizan el mismo socket.",
            components=["cpu", "motherboard"]
        )

    # Si los sockets son diferentes, existe incompatibilidad.
    return RuleResult(
        rule_id="cpu_motherboard_socket",
        status="incompatible",
        message="El socket del procesador no coincide con el de la motherboard.",
        components=["cpu", "motherboard"]
    )

# Comprueba si la motherboard declara soporte para el modelo de CPU.
def check_cpu_motherboard_model(
    cpu_model: str,
    motherboard_specs: dict[str, Any]
) -> RuleResult:

    # Obtiene los modelos de CPU soportados por la motherboard.
    supported_models = motherboard_specs.get("supported_cpu_models")

    # Sin información no podemos determinar la compatibilidad.
    if not isinstance(supported_models, list) or not supported_models:
        return RuleResult(
            rule_id="cpu_motherboard_model",
            status="indeterminate",
            message="No hay información suficiente sobre los procesadores soportados.",
            components=["cpu", "motherboard"]
        )

    # Busca el modelo exacto ignorando mayúsculas y espacios externos.
    matching_model = next(
        (
            item for item in supported_models
            if isinstance(item, dict)
            and isinstance(item.get("model"), str)
            and item["model"].strip().casefold() == cpu_model.strip().casefold()
        ),
        None
    )

    # Si el fabricante no declara soporte para el procesador,
    # se considera incompatible según los datos del catálogo.
    if matching_model is None:
        return RuleResult(
            rule_id="cpu_motherboard_model",
            status="incompatible",
            message=f"La motherboard no declara soporte para el procesador {cpu_model}.",
            components=["cpu", "motherboard"]
        )

    # Comprueba si existe un requisito mínimo de BIOS.
    min_bios = matching_model.get("min_bios_version")

    if min_bios:
        return RuleResult(
            rule_id="cpu_motherboard_model",
            status="warning",
            message=(
                f"El procesador {cpu_model} está soportado, pero requiere "
                f"como mínimo la versión de BIOS {min_bios}. "
                "Se debe verificar la versión instalada."
            ),
            components=["cpu", "motherboard"]
        )

    return RuleResult(
        rule_id="cpu_motherboard_model",
        status="compatible",
        message=f"La motherboard declara soporte para el procesador {cpu_model}.",
        components=["cpu", "motherboard"]
    )

# Comprueba que CPU y motherboard admitan el mismo tipo de memoria.
def check_cpu_motherboard_memory_type(
    cpu_specs: dict[str, Any],
    motherboard_specs: dict[str, Any]
) -> RuleResult:

    # Obtiene los tipos de memoria soportados por cada componente.
    cpu_memory_types = cpu_specs.get("supported_memory_types")
    motherboard_memory_type = motherboard_specs.get("memory_type")

    # Comprueba que exista información suficiente.
    if (
        not isinstance(cpu_memory_types, list)
        or not cpu_memory_types
        or not isinstance(motherboard_memory_type, str)
        or not motherboard_memory_type.strip()
    ):
        return RuleResult(
            rule_id="cpu_motherboard_memory_type",
            status="indeterminate",
            message="No hay información suficiente para verificar los tipos de memoria.",
            components=["cpu", "motherboard"]
        )

    # Compara los tipos de memoria ignorando mayúsculas y espacios externos.
    supported_types = [
        memory_type.strip().casefold()
        for memory_type in cpu_memory_types
        if isinstance(memory_type, str)
    ]

    motherboard_type = motherboard_memory_type.strip().casefold()

    # Si el procesador no admite el tipo de memoria de la motherboard,
    # existe incompatibilidad.
    if motherboard_type not in supported_types:
        return RuleResult(
            rule_id="cpu_motherboard_memory_type",
            status="incompatible",
            message=(
                f"La motherboard utiliza {motherboard_memory_type}, "
                "pero el procesador no declara soporte para ese tipo de memoria."
            ),
            components=["cpu", "motherboard"]
        )

    return RuleResult(
        rule_id="cpu_motherboard_memory_type",
        status="compatible",
        message=(
            f"El procesador y la motherboard admiten "
            f"{motherboard_memory_type}."
        ),
        components=["cpu", "motherboard"]
    )