import type { SelectedProduct } from './types';

export function calculateTotal(items: Iterable<SelectedProduct>): number {
  let total = 0;
  for (const item of items) total += Number(item.product.price) * item.quantity;
  return total;
}

export function calculateComponentCount(items: Iterable<SelectedProduct>): number {
  let total = 0;
  for (const item of items) total += item.quantity;
  return total;
}
