
# Importa el motor que ejecuta las reglas individuales.
from app.Services.compatibility.engine import run_compatibility_rules

# Importa la estructura del diagnóstico y su función de consolidación.
from app.Services.compatibility.results import (
    CompatibilityResult,
    consolidate_compatibility_results,
)


class CompatibilityService:
    """Coordina la ejecución de reglas y la generación del diagnóstico."""

    def evaluate(self, components: dict) -> CompatibilityResult:
        """
        Evalúa la compatibilidad de los componentes de una configuración.

        Args:
            components: Diccionario con los componentes seleccionados.

        Returns:
            CompatibilityResult: Diagnóstico general de compatibilidad.
        """

        # Ejecuta todas las reglas aplicables a los componentes recibidos.
        rule_results = run_compatibility_rules(components)

        # Consolida los resultados individuales en un diagnóstico general.
        diagnostic = consolidate_compatibility_results(rule_results)

        # Devuelve el diagnóstico final.
        return diagnostic
