import type { Product } from '../api';

export type BuilderCategory =
  | 'cpu' | 'gpu' | 'placa_madre' | 'ram'
  | 'almacenamiento' | 'refrigeracion' | 'fuente';

export interface BuilderCategoryConfig {
  value: BuilderCategory;
  label: string;
  shortLabel: string;
  code: string;
  description: string;
}

export interface SelectedProduct {
  product: Product;
  quantity: number;
}

export interface BuildItemInput {
  product_id: number;
  quantity: number;
}

export interface CompatibilityRule {
  rule_id: string;
  status: 'compatible' | 'incompatible' | 'warning';
  message: string;
  components: string[];
}

export interface CompatibilityResult {
  status: 'compatible' | 'incompatible' | 'warning' | 'review_required';
  is_compatible: boolean;
  summary: string;
  total_rules: number;
  compatible_count: number;
  incompatible_count: number;
  warning_count: number;
  results: CompatibilityRule[];
}
