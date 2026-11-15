
from typing import Any

from app.Services.compatibility.rule_result import RuleResult


def _is_positive_int(value: Any) -> bool:
    """Comprueba que un valor sea un entero positivo, sin aceptar booleanos."""
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_empty_string(value: Any) -> bool:
    """Comprueba que un valor sea una cadena no vacía."""
    return isinstance(value, str) and bool(value.strip())


def _get_storage_connection_type(storage_specs: dict[str, Any]) -> str | None:
    """
    Determina el tipo de conexión que necesita el almacenamiento.

    NVMe + PCIe: unidad M.2 NVMe.
    SATA + M.2: unidad M.2 SATA.
    SATA + SATA: unidad SATA convencional.
    """
    interface = storage_specs.get("interface")

    if not isinstance(interface, dict):
        return None

    protocol = interface.get("protocol")
    connection = interface.get("connection")

    if not _is_non_empty_string(protocol):
        return None

    if not _is_non_empty_string(connection):
        return None

    protocol = protocol.strip().casefold()
    connection = connection.strip().casefold()

    if protocol == "nvme" and connection == "pcie":
        return "pcie"

    if protocol == "sata" and connection == "m.2":
        return "sata_m2"

    if protocol == "sata" and connection == "sata":
        return "sata"

    return None


def _get_m2_interface(connection_type: str) -> str | None:
    """Relaciona el tipo de unidad M.2 con la interfaz de la ranura."""
    if connection_type == "pcie":
        return "pcie"

    if connection_type == "sata_m2":
        return "sata"

    return None


def check_storage_motherboard_interface(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba que la motherboard disponga de una interfaz
    adecuada para el tipo de almacenamiento.
    """
    connection_type = _get_storage_connection_type(storage_specs)

    if connection_type is None:
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="indeterminate",
            message=(
                "No se puede determinar una interfaz válida "
                "para el almacenamiento."
            ),
            components=["storage", "motherboard"],
        )

    # Las unidades SATA convencionales utilizan puertos SATA.
    if connection_type == "sata":
        sata_ports = motherboard_specs.get("sata_ports")

        if not _is_positive_int(sata_ports):
            return RuleResult(
                rule_id="storage_motherboard_interface",
                status="indeterminate",
                message="No hay información válida sobre los puertos SATA de la motherboard.",
                components=["storage", "motherboard"],
            )

        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="compatible",
            message="El almacenamiento utiliza una conexión SATA soportada por la motherboard.",
            components=["storage", "motherboard"],
        )

    # Las unidades M.2 necesitan una ranura con la interfaz adecuada.
    m2_slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(m2_slots, list):
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="indeterminate",
            message="No hay información sobre las ranuras M.2 de la motherboard.",
            components=["storage", "motherboard"],
        )

    required_interface = _get_m2_interface(connection_type)

    valid_interfaces = []

    for slot in m2_slots:
        if not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")

        if not _is_non_empty_string(slot_interface):
            continue

        valid_interfaces.append(slot_interface.strip().casefold())

    if not valid_interfaces:
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="indeterminate",
            message="No hay información válida sobre las interfaces de las ranuras M.2.",
            components=["storage", "motherboard"],
        )

    if required_interface not in valid_interfaces:
        return RuleResult(
            rule_id="storage_motherboard_interface",
            status="incompatible",
            message=(
                "La motherboard no declara ranuras M.2 con la interfaz "
                "necesaria para este almacenamiento."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_interface",
        status="compatible",
        message="La interfaz del almacenamiento es compatible con una interfaz M.2 declarada por la motherboard.",
        components=["storage", "motherboard"],
    )


def check_storage_motherboard_form_factor(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
) -> RuleResult:
    """
    Comprueba el factor de forma del almacenamiento M.2.

    Las unidades SATA convencionales de 2.5 o 3.5 pulgadas
    no necesitan coincidir con los factores de forma de las
    ranuras M.2.
    """
    connection_type = _get_storage_connection_type(storage_specs)

    if connection_type is None:
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No se puede determinar el tipo de conexión del almacenamiento.",
            components=["storage", "motherboard"],
        )

    # El factor de forma M.2 solo se compara con ranuras M.2.
    if connection_type == "sata":
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="compatible",
            message="El almacenamiento SATA convencional no requiere una ranura M.2.",
            components=["storage", "motherboard"],
        )

    storage_form_factor = storage_specs.get("form_factor")

    if not _is_non_empty_string(storage_form_factor):
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No se conoce el factor de forma del almacenamiento M.2.",
            components=["storage", "motherboard"],
        )

    m2_slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(m2_slots, list):
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No hay información sobre las ranuras M.2 de la motherboard.",
            components=["storage", "motherboard"],
        )

    required_interface = _get_m2_interface(connection_type)
    valid_form_factors = []

    for slot in m2_slots:
        if not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")
        supported_form_factors = slot.get("supported_form_factors")

        if not _is_non_empty_string(slot_interface):
            continue

        if slot_interface.strip().casefold() != required_interface:
            continue

        if not isinstance(supported_form_factors, list):
            continue

        for form_factor in supported_form_factors:
            if _is_non_empty_string(form_factor):
                valid_form_factors.append(form_factor.strip().casefold())

    if not valid_form_factors:
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="indeterminate",
            message="No hay información válida sobre los factores de forma soportados por las ranuras M.2 adecuadas.",
            components=["storage", "motherboard"],
        )

    if storage_form_factor.strip().casefold() not in valid_form_factors:
        return RuleResult(
            rule_id="storage_motherboard_form_factor",
            status="incompatible",
            message=(
                f"La motherboard no declara soporte para el factor de forma "
                f"{storage_form_factor.strip()}."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_form_factor",
        status="compatible",
        message=(
            f"La motherboard declara soporte para el factor de forma "
            f"{storage_form_factor.strip()}."
        ),
        components=["storage", "motherboard"],
    )


def check_storage_motherboard_connection_availability(
    storage_specs: dict[str, Any],
    motherboard_specs: dict[str, Any],
    storage_quantity: int = 1,
    occupied_m2_slot_indexes: list[int] | None = None,
) -> RuleResult:
    """
    Comprueba la disponibilidad de conexiones para el almacenamiento.

    occupied_m2_slot_indexes contiene los índices de las ranuras
    M.2 que ya están ocupadas, según el orden de m2_slots_details.

    Esto permite considerar los puertos SATA que se deshabilitan
    cuando se utilizan determinadas ranuras M.2.
    """
    if not _is_positive_int(storage_quantity):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="La cantidad de unidades de almacenamiento no es válida.",
            components=["storage", "motherboard"],
        )

    if occupied_m2_slot_indexes is None:
        occupied_m2_slot_indexes = []

    # Validar los índices de las ranuras M.2 ocupadas.
    if not isinstance(occupied_m2_slot_indexes, list):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="La información sobre las ranuras M.2 ocupadas no es válida.",
            components=["storage", "motherboard"],
        )

    if any(
        not isinstance(index, int) or isinstance(index, bool) or index < 0
        for index in occupied_m2_slot_indexes
    ):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="Los índices de las ranuras M.2 ocupadas contienen datos inválidos.",
            components=["storage", "motherboard"],
        )

    connection_type = _get_storage_connection_type(storage_specs)

    if connection_type is None:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No se puede determinar qué conexión necesita el almacenamiento.",
            components=["storage", "motherboard"],
        )

    # Caso 1: almacenamiento SATA convencional.
    if connection_type == "sata":
        sata_ports = motherboard_specs.get("sata_ports")

        if not _is_positive_int(sata_ports):
            return RuleResult(
                rule_id="storage_motherboard_connection_availability",
                status="indeterminate",
                message="No hay información válida sobre la cantidad de puertos SATA.",
                components=["storage", "motherboard"],
            )

        m2_slots = motherboard_specs.get("m2_slots_details", [])

        if not isinstance(m2_slots, list):
            return RuleResult(
                rule_id="storage_motherboard_connection_availability",
                status="indeterminate",
                message="No se puede comprobar si las ranuras M.2 deshabilitan puertos SATA.",
                components=["storage", "motherboard"],
            )

        disabled_sata_ports = set()

        # Recopilar los puertos SATA deshabilitados por las ranuras ocupadas.
        for index in occupied_m2_slot_indexes:
            if index >= len(m2_slots):
                return RuleResult(
                    rule_id="storage_motherboard_connection_availability",
                    status="indeterminate",
                    message="Se indicó una ranura M.2 ocupada que no existe en la motherboard.",
                    components=["storage", "motherboard"],
                )

            slot = m2_slots[index]

            if not isinstance(slot, dict):
                return RuleResult(
                    rule_id="storage_motherboard_connection_availability",
                    status="indeterminate",
                    message="La información de una ranura M.2 ocupada no es válida.",
                    components=["storage", "motherboard"],
                )

            shared_resources = slot.get("shared_resources", {})

            if shared_resources is None:
                continue

            if not isinstance(shared_resources, dict):
                return RuleResult(
                    rule_id="storage_motherboard_connection_availability",
                    status="indeterminate",
                    message="La información de recursos compartidos de una ranura M.2 no es válida.",
                    components=["storage", "motherboard"],
                )

            disabled_ports = shared_resources.get("disabled_sata_ports", [])

            if not isinstance(disabled_ports, list):
                return RuleResult(
                    rule_id="storage_motherboard_connection_availability",
                    status="indeterminate",
                    message="La lista de puertos SATA deshabilitados no es válida.",
                    components=["storage", "motherboard"],
                )

            for port in disabled_ports:
                if (
                    not isinstance(port, int)
                    or isinstance(port, bool)
                    or port <= 0
                    or port > sata_ports
                ):
                    return RuleResult(
                        rule_id="storage_motherboard_connection_availability",
                        status="indeterminate",
                        message="La motherboard contiene números de puertos SATA deshabilitados inválidos.",
                        components=["storage", "motherboard"],
                    )

                disabled_sata_ports.add(port)

        available_ports = sata_ports - len(disabled_sata_ports)

        if available_ports < storage_quantity:
            return RuleResult(
                rule_id="storage_motherboard_connection_availability",
                status="incompatible",
                message=(
                    f"No hay suficientes puertos SATA disponibles. "
                    f"Disponibles: {available_ports}; "
                    f"necesarios: {storage_quantity}."
                ),
                components=["storage", "motherboard"],
            )

        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="compatible",
            message=f"Hay {available_ports} puertos SATA disponibles.",
            components=["storage", "motherboard"],
        )

    # Caso 2: almacenamiento M.2 NVMe o M.2 SATA.
    m2_slots = motherboard_specs.get("m2_slots_details")

    if not isinstance(m2_slots, list):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No hay información sobre las ranuras M.2 de la motherboard.",
            components=["storage", "motherboard"],
        )

    required_interface = _get_m2_interface(connection_type)
    storage_form_factor = storage_specs.get("form_factor")

    if not _is_non_empty_string(storage_form_factor):
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="indeterminate",
            message="No se conoce el factor de forma del almacenamiento M.2.",
            components=["storage", "motherboard"],
        )

    # Buscar ranuras adecuadas que no estén ocupadas.
    available_slots = 0

    for index, slot in enumerate(m2_slots):
        if index in occupied_m2_slot_indexes:
            continue

        if not isinstance(slot, dict):
            continue

        slot_interface = slot.get("interface")
        supported_form_factors = slot.get("supported_form_factors")
        quantity = slot.get("quantity")

        if not _is_non_empty_string(slot_interface):
            continue

        if slot_interface.strip().casefold() != required_interface:
            continue

        if not isinstance(supported_form_factors, list):
            continue

        if not any(
            _is_non_empty_string(form_factor)
            and form_factor.strip().casefold() == storage_form_factor.strip().casefold()
            for form_factor in supported_form_factors
        ):
            continue

        if not _is_positive_int(quantity):
            continue

        available_slots += quantity

    if available_slots < storage_quantity:
        return RuleResult(
            rule_id="storage_motherboard_connection_availability",
            status="incompatible",
            message=(
                f"No hay suficientes ranuras M.2 disponibles para este "
                f"almacenamiento. Disponibles: {available_slots}; "
                f"necesarias: {storage_quantity}."
            ),
            components=["storage", "motherboard"],
        )

    return RuleResult(
        rule_id="storage_motherboard_connection_availability",
        status="compatible",
        message=f"Hay {available_slots} ranuras M.2 adecuadas disponibles.",
        components=["storage", "motherboard"],
    )
