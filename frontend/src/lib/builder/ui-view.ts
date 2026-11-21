import { category, escapeHtml, price } from '../format';
import {
  calculateComponentCount,
  calculateTotal,
} from './calculations';
import { BUILDER_CATEGORIES } from './constants';
import type {
  BuilderCategory,
  CompatibilityResult,
  SelectedProduct,
} from './types';

export interface BuilderViewElements {
  categoryList: HTMLElement;
  selectedList: HTMLElement;
  totalElement: HTMLElement;
  componentCountElement: HTMLElement;
  viewerCountElement: HTMLElement;
  saveFeedback: HTMLElement;
  compatibilityPercent: HTMLElement;
  compatibilityMeter: HTMLElement;
  compatibilityMeterFill: HTMLElement;
  compatibilitySummary: HTMLElement;
  compatibilityCounts: HTMLElement;
  compatibilityPurchaseWarning: HTMLElement;
  compatibilityResults: HTMLElement;
  panelTitle: HTMLElement;
  specificationsView: HTMLElement;
  diagnosticsView: HTMLElement;
  panelToggle: HTMLButtonElement;
}

export function renderSidebar(
  view: BuilderViewElements,
  activeCategory: BuilderCategory,
  selected: Map<number, SelectedProduct>,
): void {
  view.categoryList.querySelectorAll<HTMLButtonElement>('[data-category]').forEach((button) => {
    const categoryValue = button.dataset.category as BuilderCategory;
    const active = categoryValue === activeCategory;
    const hasSelected = [...selected.values()].some(
      ({ product }) => product.category === categoryValue,
    );
    const state = button.querySelector<HTMLElement>('[data-category-state]');

    button.classList.toggle('is-active', active);
    button.classList.toggle('is-complete', hasSelected);
    button.setAttribute('aria-pressed', String(active));
    state?.classList.toggle('text-rose-400', hasSelected);

    if (state) state.textContent = hasSelected ? 'SELECCIONADO' : 'PENDIENTE';
  });
}

export function renderSelected(
  view: BuilderViewElements,
  selected: Map<number, SelectedProduct>,
  activeCategory: BuilderCategory,
): void {
  const items = [...selected.values()];

  if (!items.length) {
    view.selectedList.innerHTML = `
      <p class="my-3 text-xs leading-relaxed text-ink-400">
        Selecciona componentes para ver aquí sus especificaciones.
      </p>`;
  } else {
    view.selectedList.innerHTML = items.map(({ product, quantity }) => {
      return `
        <article class="grid grid-cols-[minmax(0,1fr)_auto] gap-x-3 gap-y-1
          border-b border-ink-800 py-3">
          <div class="col-span-2 flex min-w-0 items-center justify-between">
            <span class="font-mono text-[9px] tracking-wider text-violet-300">
              ${escapeHtml(category(product.category).code)}
            </span>
            <button type="button" class="grid size-6 place-items-center
              rounded-sm text-lg text-ink-400 hover:bg-ink-800 hover:text-rose-400"
              data-remove-product="${product.id}"
              aria-label="Retirar ${escapeHtml(product.name)}">×</button>
          </div>
          <strong class="col-span-2 text-xs font-semibold leading-snug text-ink-100">
            ${escapeHtml(product.name)}
          </strong>
          <small class="truncate text-[10px] text-ink-400">
            ${escapeHtml(product.brand)} · ${quantity}
            ${quantity === 1 ? 'unidad' : 'unidades'}
          </small>
          <span class="col-start-2 row-start-3 text-right font-mono text-[10px]
            font-semibold text-rose-400">
            ${price(Number(product.price) * quantity)}
          </span>
        </article>`;
    }).join('');
  }

  const total = calculateTotal(items);
  const count = calculateComponentCount(items);
  view.totalElement.textContent = price(total);
  view.componentCountElement.textContent =
    `${count} ${count === 1 ? 'COMPONENTE' : 'COMPONENTES'}`;
  view.viewerCountElement.textContent =
    `${count} ${count === 1 ? 'COMPONENTE' : 'COMPONENTES'}`;
  renderSidebar(view, activeCategory, selected);
}

export function setFeedback(
  view: BuilderViewElements,
  message: string,
  isError = false,
): void {
  view.saveFeedback.textContent = message;
  view.saveFeedback.classList.toggle('text-danger', isError);
  view.saveFeedback.classList.toggle('text-ok', !isError);
}

export function setCompatibilityState(
  view: BuilderViewElements,
  summary: string,
  percent: number | null = null,
): void {
  view.compatibilityPercent.textContent =
    percent === null ? '--%' : `${percent}% compatible`;
  view.compatibilityPercent.className =
    `whitespace-nowrap font-mono text-xs font-bold ${percent === null ? 'text-ink-400' : 'text-ok'}`;
  view.compatibilityMeterFill.className =
    'block h-full rounded-full bg-ok transition-[width]';
  view.compatibilityMeterFill.style.width = `${percent ?? 0}%`;
  view.compatibilityMeter.setAttribute('aria-valuenow', String(percent ?? 0));
  view.compatibilityMeter.setAttribute(
    'aria-valuetext',
    percent === null ? 'Compatibilidad pendiente' : `${percent}% de compatibilidad`,
  );
  view.compatibilitySummary.textContent = summary;
  view.compatibilityCounts.replaceChildren();
  view.compatibilityPurchaseWarning.hidden = true;
}

export function renderCompatibility(
  view: BuilderViewElements,
  result: CompatibilityResult,
): void {
  const percent = result.total_rules > 0
    ? Math.max(0, Math.round(
      ((result.total_rules - result.incompatible_count) / result.total_rules) * 100,
    ))
    : null;
  setCompatibilityState(view, result.summary, percent);
  const incompatibleCount = Math.max(0, Math.trunc(result.incompatible_count));
  const warningCount = Math.max(0, Math.trunc(result.warning_count));
  const counts = [
    incompatibleCount > 0
      ? `<span class="font-semibold text-danger">${incompatibleCount} ${
        incompatibleCount === 1 ? 'incompatibilidad' : 'incompatibilidades'
      }</span>`
      : '',
    warningCount > 0
      ? `<span class="font-semibold text-warn">${warningCount} ${
        warningCount === 1 ? 'advertencia' : 'advertencias'
      }</span>`
      : '',
  ].filter(Boolean);

  view.compatibilityCounts.innerHTML = counts.length
    ? counts.join('')
    : '<span class="text-ok">Sin incidencias</span>';
  view.compatibilityPurchaseWarning.hidden = incompatibleCount === 0;

  const visibleResults = result.results.filter(
    ({ status: ruleStatus }) => ruleStatus === 'warning' || ruleStatus === 'incompatible',
  );
  view.compatibilityResults.innerHTML = visibleResults.length
    ? visibleResults.map((rule) => {
      const incompatible = rule.status === 'incompatible';
      const border = incompatible ? 'border-danger' : 'border-warn';
      const text = incompatible ? 'text-danger' : 'text-warn';

      return `
        <article class="rounded-sm border-l-2 ${border} bg-ink-850 p-3">
          <h3 class="mb-1 font-mono text-[9px] font-semibold tracking-wider ${text}">
            ${incompatible ? 'INCOMPATIBILIDAD' : 'ADVERTENCIA'}
          </h3>
          <p class="text-xs leading-relaxed text-ink-200">${escapeHtml(rule.message)}</p>
        </article>`;
    }).join('')
    : `<p class="my-3 text-xs leading-relaxed text-ink-400">
        No se detectaron advertencias ni incompatibilidades.
      </p>`;
}

export function showDiagnostics(
  view: BuilderViewElements,
  show: boolean,
): void {
  view.specificationsView.hidden = show;
  view.specificationsView.classList.toggle('hidden', show);
  view.diagnosticsView.hidden = !show;
  view.diagnosticsView.classList.toggle('hidden', !show);
  view.panelTitle.textContent = show ? 'DIAGNÓSTICO' : 'ESPECIFICACIONES';
  view.panelToggle.textContent = show ? 'VER ESPECIFICACIONES' : 'VER DIAGNÓSTICO';
  view.panelToggle.setAttribute('aria-controls', show
    ? 'builder-specifications-view'
    : 'builder-diagnostics-view');
  view.panelToggle.setAttribute('aria-pressed', String(show));
}
