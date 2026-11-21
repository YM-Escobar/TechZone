import { tokens } from '../api';
import { evaluateBuilder } from './compatibility';
import type { BuildItemInput, SelectedProduct } from './types';
import {
  renderCompatibility,
  setCompatibilityState,
  type BuilderViewElements,
} from './ui-view';

export function createCompatibilityUpdater(
  selected: Map<number, SelectedProduct>,
  view: BuilderViewElements,
): () => void {
  let sequence = 0;
  let timer = 0;

  async function refresh(): Promise<void> {
    const request = ++sequence;
    const items: BuildItemInput[] = [...selected.values()].map(({ product, quantity }) => ({
      product_id: product.id,
      quantity,
    }));

    if (!items.length) {
      view.compatibilityResults.innerHTML = `
        <p class="my-3 text-xs leading-relaxed text-ink-400">
          Agrega componentes para ejecutar el diagnóstico.
        </p>`;
      setCompatibilityState(
        view,
        'Agrega componentes para evaluar la compatibilidad.',
      );
      return;
    }

    if (!tokens.access) {
      view.compatibilityResults.innerHTML = `
        <p class="my-3 text-xs leading-relaxed text-ink-400">
          Inicia sesión para consultar advertencias e incompatibilidades.
        </p>`;
      setCompatibilityState(
        view,
        'Inicia sesión para evaluar la compatibilidad del ensamble.',
      );
      return;
    }

    view.compatibilityResults.innerHTML = `
      <p class="my-3 text-xs leading-relaxed text-ink-400">
        Analizando compatibilidad…
      </p>`;
    setCompatibilityState(
      view,
      'Evaluando las piezas seleccionadas.',
    );

    try {
      const result = await evaluateBuilder(items);
      if (request === sequence) renderCompatibility(view, result);
    } catch (error) {
      if (request !== sequence) return;
      view.compatibilityResults.replaceChildren();
      setCompatibilityState(
        view,
        error instanceof Error
          ? error.message
          : 'No fue posible evaluar la compatibilidad.',
      );
    }
  }

  return () => {
    window.clearTimeout(timer);
    sequence += 1;
    timer = window.setTimeout(() => {
      void refresh();
    }, 350);
  };
}
