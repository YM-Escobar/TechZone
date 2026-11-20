import { api, mediaUrl, type Page, type Product } from '../api';
import { category, escapeHtml, price } from '../format';
import { SINGLE_UNIT_CATEGORIES } from './constants';
import type { BuilderCategory } from './types';

export async function getBuilderProducts(
  selectedCategory: BuilderCategory,
  search = '',
): Promise<Page<Product>> {
  return api<Page<Product>>('/products', {
    query: {
      category: selectedCategory,
      search: search.trim() || undefined,
      is_builder_eligible: true,
      skip: 0,
      limit: 40,
    },
  });
}

export function renderProductCard(product: Product, selected: boolean): string {
  const image = mediaUrl(product.image_url);
  const imageMarkup = image
    ? `<img class="h-full max-h-31.5 w-full object-contain p-2" src="${escapeHtml(image)}" alt="" loading="lazy">`
    : `<span class="font-mono text-sm font-bold text-ink-400">${escapeHtml(category(product.category).code)}</span>`;

  const unavailable = product.stock <= 0;
  const selectedStyles = selected
    ? 'is-selected border-rose-400 ring-1 ring-rose-400/60 shadow-[0_0_18px_rgba(255,45,149,0.35)]'
    : 'border-ink-800';
  const hoverStyle = selected ? 'hover:border-rose-300' : 'hover:border-violet-400';
  const actionLabel = unavailable
    ? `${product.name}: sin stock`
    : selected && SINGLE_UNIT_CATEGORIES.has(product.category)
      ? `${product.name}: ya seleccionado; solo se permite una unidad`
      : selected
        ? `Agregar otra unidad de ${product.name}`
        : `Agregar ${product.name}`;

  return `
    <button type="button"
      class="product-card group relative grid min-h-37.5 min-w-63.75
        grid-cols-[104px_minmax(0,1fr)] items-stretch gap-3 rounded-sm border
        bg-ink-900 p-2.5 text-left text-ink-100 transition
        hover:-translate-y-0.5 ${hoverStyle}
        focus-visible:outline-2 focus-visible:outline-rose-400
        disabled:cursor-not-allowed disabled:opacity-50 ${selectedStyles}"
      data-add-product="${product.id}"
      aria-label="${escapeHtml(actionLabel)}"
      aria-pressed="${selected}"
      ${unavailable ? 'disabled' : ''}>
      <span class="grid min-h-31.5 place-items-center overflow-hidden
        rounded-sm bg-ink-850">${imageMarkup}</span>
      <span class="relative flex min-w-0 flex-col items-start gap-1.5 ${selected ? '' : 'pb-6'}">
        ${selected
          ? `<span class="rounded-sm bg-rose-500 px-1.5 py-0.5 font-mono
              text-[7px] font-semibold tracking-wide text-white
              shadow-[0_0_10px_rgba(255,45,149,0.45)]">SELECCIONADO</span>`
          : ''}
        <span class="font-mono text-[8px] uppercase tracking-wide text-ink-400">
          ${escapeHtml(product.brand)} · ${escapeHtml(category(product.category).code)}
        </span>
        <span class="line-clamp-2 text-xs font-semibold leading-snug text-ink-100"
          title="${escapeHtml(product.name)}">${escapeHtml(product.name)}</span>
        <span class="mt-auto flex w-full items-baseline justify-between gap-1.5">
            <strong class="font-mono text-[11px] font-semibold
              ${selected ? 'text-rose-400 drop-shadow-[0_0_8px_rgba(255,45,149,0.45)]' : ''}">
              ${price(Number(product.price))}
            </strong>
          <small class="font-mono text-[8px] text-ink-400">
            ${unavailable ? 'SIN STOCK' : `${product.stock} DISP.`}
          </small>
        </span>
          ${selected ? '' : `<span class="absolute bottom-0 right-0 font-mono
            text-[8px] font-semibold tracking-wide text-violet-300"
            aria-hidden="true">${unavailable ? 'AGOTADO' : '+'}</span>`}
      </span>
    </button>`;
}
