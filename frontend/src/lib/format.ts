import { mediaUrl, type Product } from './api';

// Mismos valores que ProductCategory en el backend (app/Models/product.py)
export const CATEGORIES = [
  { value: 'cpu', label: 'Procesadores', code: 'CPU' },
  { value: 'gpu', label: 'Tarjetas de video', code: 'GPU' },
  { value: 'placa_madre', label: 'Placas madre', code: 'MB' },
  { value: 'ram', label: 'Memoria RAM', code: 'RAM' },
  { value: 'almacenamiento', label: 'Almacenamiento', code: 'SSD' },
  { value: 'fuente', label: 'Fuentes de poder', code: 'PSU' },
  { value: 'gabinete', label: 'Gabinetes', code: 'CASE' },
  { value: 'refrigeracion', label: 'Refrigeración', code: 'COOL' },
  { value: 'monitor', label: 'Monitores', code: 'MON' },
  { value: 'periferico', label: 'Periféricos', code: 'PER' },
] as const;

export function category(value: string) {
  return CATEGORIES.find((c) => c.value === value) ?? { value, label: value, code: value.toUpperCase() };
}

// Moneda de los precios; cámbiala aquí si la tienda usa otra
const money = new Intl.NumberFormat('es-MX', { style: 'currency', currency: 'USD', currencyDisplay: 'narrowSymbol' });

export function price(value: number): string {
  return money.format(value);
}

export function date(value: string): string {
  return new Date(value).toLocaleDateString('es', { day: 'numeric', month: 'long', year: 'numeric' });
}

export function escapeHtml(value: unknown): string {
  return String(value ?? '').replace(/[&<>"']/g, (ch) => `&#${ch.charCodeAt(0)};`);
}

export function stockLabel(stock: number): { text: string; tone: string } {
  if (stock <= 0) return { text: 'Sin stock', tone: 'text-danger' };
  if (stock <= 5) return { text: `Quedan ${stock}`, tone: 'text-warn' };
  return { text: 'En stock', tone: 'text-ok' };
}

/** Imagen del producto, o un recuadro rayado con el código de la categoría. */
export function productImage(p: Product, sizeClass = 'text-2xl'): string {
  const src = mediaUrl(p.image_url);
  if (src) {
    return `<img src="${escapeHtml(src)}" alt="${escapeHtml(p.name)}" loading="lazy" class="h-full w-full object-contain p-4" />`;
  }
  return `<div class="hatch flex h-full w-full items-center justify-center">
    <span class="font-mono ${sizeClass} font-medium tracking-widest text-ink-700">${escapeHtml(category(p.category).code)}</span>
  </div>`;
}

export function productCard(p: Product): string {
  const stock = stockLabel(p.stock);
  return `<a href="/producto?id=${p.id}" class="group flex flex-col border-r border-b border-ink-800 bg-ink-950 transition-colors hover:bg-ink-900">
    <div class="aspect-[4/3] border-b border-ink-800 bg-ink-900">${productImage(p)}</div>
    <div class="flex flex-1 flex-col gap-1 p-4">
      <p class="label">${escapeHtml(p.brand)} · ${escapeHtml(category(p.category).code)}</p>
      <h3 class="line-clamp-2 text-[15px] font-medium leading-snug text-ink-100 group-hover:text-violet-300">${escapeHtml(p.name)}</h3>
      <div class="mt-auto flex items-end justify-between gap-2 pt-3">
        <span class="font-mono text-lg font-medium text-ink-100">${price(p.price)}</span>
        <span class="font-mono text-[11px] ${stock.tone}">${stock.text}</span>
      </div>
    </div>
  </a>`;
}
