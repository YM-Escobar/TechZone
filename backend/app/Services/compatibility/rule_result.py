from dataclasses import dataclass
from typing import Literal


# Estados posibles de una regla de compatibilidad.
RuleStatus = Literal[
    "compatible",
    "incompatible",
    "warning",
    "indeterminate"
]


# Resultado estandarizado de una regla.
@dataclass
class RuleResult:

    # Identificador único de la regla.
    rule_id: str

    # Estado obtenido después de evaluar la regla.
    status: RuleStatus

    # Explicación del resultado.
    message: str

    # Componentes involucrados en la validación.
    components: list[str]