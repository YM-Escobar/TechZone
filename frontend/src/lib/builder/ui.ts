import { tokens, type Product } from '../api';
import { escapeHtml } from '../format';
import { BUILDER_CATEGORIES, DEFAULT_BUILD_NAME, SINGLE_UNIT_CATEGORIES } from './constants';
import { saveBuilder } from './builds';
import { getBuilderProducts, renderProductCard } from './products';
import { createCompatibilityUpdater } from './ui-compatibility';
import { renderSelected, setFeedback, showDiagnostics, type BuilderViewElements } from './ui-view';
import type { BuildItemInput, BuilderCategory, SelectedProduct } from './types';

export function initializeBuilder(root: HTMLElement): void {
  if (root.dataset.initialized === 'true') return;

  const $ = <T extends HTMLElement>(selector: string): T => {
    const element = root.querySelector<T>(selector);
    if (!element) throw new Error(`Builder: no se encontró ${selector}`);
    return element;
  };
  const view: BuilderViewElements = {
    categoryList: $('#builder-category-list'),
    selectedList: $('#builder-selected-list'),
    totalElement: $('#builder-total'),
    componentCountElement: $('#builder-component-count'),
    viewerCountElement: $('#builder-viewer-count'),
    saveFeedback: $('#builder-save-feedback'),
    compatibilityPercent: $('#compatibility-percent'),
    compatibilityMeter: $('#compatibility-meter'),
    compatibilityMeterFill: $('#compatibility-meter-fill'),
    compatibilitySummary: $('#compatibility-summary'),
    compatibilityCounts: $('#compatibility-counts'),
    compatibilityPurchaseWarning: $('#compatibility-purchase-warning'),
    compatibilityResults: $('#compatibility-results'),
    panelTitle: $('#builder-panel-title'),
    specificationsView: $('#builder-specifications-view'),
    diagnosticsView: $('#builder-diagnostics-view'),
    panelToggle: $<HTMLButtonElement>('#builder-panel-toggle'),
  };
  const productsResults = $('#builder-products-results');
  const productsCount = $('#builder-products-count');
  const productsTitle = $('#builder-products-title');
  const productsDescription = $('#builder-products-description');
  const productsSearch = $<HTMLInputElement>('#builder-products-search');
  const saveButton = $<HTMLButtonElement>('#builder-save');
  const buildName = $<HTMLInputElement>('#builder-name');
  const selected = new Map<number, SelectedProduct>();
  const scheduleCompatibility = createCompatibilityUpdater(selected, view);

  let activeCategory: BuilderCategory = 'cpu';
  let searchTerm = '';
  let products: Product[] = [];
  let requestSequence = 0;

  root.dataset.initialized = 'true';
  buildName.value = buildName.value || DEFAULT_BUILD_NAME;

  async function loadProducts(): Promise<void> {
    const sequence = ++requestSequence;
    products = [];
    productsResults.setAttribute('aria-busy', 'true');
    productsResults.innerHTML = `
      <div class="w-full min-w-62.5 border border-dashed border-ink-700
        p-7 text-center font-mono text-[9px] text-ink-400">
        CARGANDO CATÁLOGO…
      </div>`;
    const config = BUILDER_CATEGORIES.find((item) => item.value === activeCategory);
    productsTitle.textContent = config?.shortLabel ?? 'COMPONENTES';
    productsDescription.textContent =
      config?.description ?? 'Elige los componentes para tu ensamble.';

    try {
      const response = await getBuilderProducts(activeCategory, searchTerm);
      if (sequence !== requestSequence) return;

      products = response.items;
      productsResults.setAttribute('aria-busy', 'false');
      productsCount.textContent =
        `${response.total} ${response.total === 1 ? 'PRODUCTO ELEGIBLE' : 'PRODUCTOS ELEGIBLES'}`;

      if (!response.items.length) {
        productsResults.innerHTML = `
          <div class="w-full min-w-62.5 border border-dashed border-ink-700
            p-7 text-center text-xs text-ink-400">
            No hay productos elegibles para esta búsqueda.
          </div>`;
        return;
      }

      productsResults.innerHTML = response.items
        .map((product) => renderProductCard(product, selected.has(product.id)))
        .join('');
    } catch (error) {
      if (sequence !== requestSequence) return;
      productsResults.setAttribute('aria-busy', 'false');
      productsCount.textContent = 'NO SE PUDO CARGAR EL CATÁLOGO';
      productsResults.innerHTML = `
        <div class="w-full min-w-[250px] border border-danger/40
          bg-danger/10 p-7 text-center text-xs text-danger">
          ${escapeHtml(error instanceof Error ? error.message : 'Intenta de nuevo.')}
        </div>`;
    }
  }

  function addProduct(product: Product): void {
    const existing = selected.get(product.id);
    const singleUnit = SINGLE_UNIT_CATEGORIES.has(product.category);
    if (existing && (singleUnit || existing.quantity >= 20)) {
      productsCount.textContent = singleUnit ? 'Solo se permite una unidad de este componente.' : 'Máximo 20 unidades por componente.';
      return;
    }
    if (existing) {
      existing.quantity += 1;
    } else {
      if (SINGLE_UNIT_CATEGORIES.has(product.category)) {
        for (const [id, item] of selected) {
          if (item.product.category === product.category) selected.delete(id);
        }
      }
      selected.set(product.id, { product, quantity: 1 });
    }

    renderSelected(view, selected, activeCategory);
    void loadProducts();
    scheduleCompatibility();
  }

  view.categoryList.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const button = target.closest<HTMLButtonElement>('[data-category]');
    if (!button) return;

    const config = BUILDER_CATEGORIES.find(
      (item) => item.value === button.dataset.category,
    );
    if (!config) return;

    activeCategory = config.value;
    searchTerm = '';
    productsSearch.value = '';
    renderSelected(view, selected, activeCategory);
    void loadProducts();
  });

  productsSearch.addEventListener('input', () => {
    searchTerm = productsSearch.value.trim();
    void loadProducts();
  });

  productsResults.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const button = target.closest<HTMLButtonElement>('[data-add-product]');
    if (!button || button.disabled) return;

    const product = products.find((item) => item.id === Number(button.dataset.addProduct));
    if (product) addProduct(product);
  });

  view.selectedList.addEventListener('click', (event) => {
    const target = event.target;
    if (!(target instanceof Element)) return;
    const button = target.closest<HTMLButtonElement>('[data-remove-product]');
    if (!button) return;

    selected.delete(Number(button.dataset.removeProduct));
    renderSelected(view, selected, activeCategory);
    void loadProducts();
    scheduleCompatibility();
  });

  view.panelToggle.addEventListener('click', () => {
    showDiagnostics(view, Boolean(view.diagnosticsView.hidden));
  });

  saveButton.addEventListener('click', async () => {
    if (!tokens.access) {
      setFeedback(view, 'Inicia sesión para guardar tu ensamble.', true);
      return;
    }

    const name = buildName.value.trim();
    if (name.length < 2) {
      setFeedback(view, 'El nombre debe tener al menos 2 caracteres.', true);
      buildName.focus();
      return;
    }
    if (!selected.size) {
      setFeedback(view, 'Agrega al menos un componente antes de guardar.', true);
      return;
    }

    const items: BuildItemInput[] = [...selected.values()].map(({ product, quantity }) => ({
      product_id: product.id,
      quantity,
    }));
    saveButton.disabled = true;
    setFeedback(view, 'GUARDANDO…');

    try {
      const saved = await saveBuilder({
        name,
        description: null,
        is_public: false,
        items,
      });
      setFeedback(view, `ENSAMBLE #${saved.id} GUARDADO`);
    } catch (error) {
      setFeedback(
        view,
        error instanceof Error ? error.message : 'No se pudo guardar el ensamble.',
        true,
      );
    } finally {
      saveButton.disabled = false;
    }
  });

  renderSelected(view, selected, activeCategory);
  void loadProducts();
}
