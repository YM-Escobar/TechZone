
from typing import Any


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value > 0


def _is_non_negative_int(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _is_non_empty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _get_storage_connection_type(storage_specs: dict[str, Any]) -> str | None:
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
    if connection_type == "pcie":
        return "pcie"

    if connection_type == "sata_m2":
        return "sata"

    return None
