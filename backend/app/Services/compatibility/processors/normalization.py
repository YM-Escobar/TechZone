from typing import Any

def _normalize_entries(value: Any) -> list[dict[str, Any]]:
    """
    Normaliza un componente individual o una lista de componentes.

    Permite recibir:
    - Un diccionario para componentes individuales.
    - Una lista de diccionarios para componentes múltiples.
    """
    if isinstance(value, dict):
        return [value]

    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]

    return []
