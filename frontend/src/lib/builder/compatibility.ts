import { api } from '../api';
import type { BuildItemInput, CompatibilityResult } from './types';

export function evaluateBuilder(items: BuildItemInput[]): Promise<CompatibilityResult> {
  if (!items.length) throw new Error('Selecciona al menos un componente.');
  return api<CompatibilityResult>('/builds/compatibility', {
    method: 'POST',
    json: { items },
  });
}
