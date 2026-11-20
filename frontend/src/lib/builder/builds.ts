import { api } from '../api';
import type { BuildItemInput } from './types';

export interface BuildCreateInput {
  name: string;
  description: string | null;
  is_public: boolean;
  items: BuildItemInput[];
}

export interface SavedBuild {
  id: number;
  name: string;
  is_public: boolean;
  total_price: number;
}

export function saveBuilder(data: BuildCreateInput): Promise<SavedBuild> {
  return api<SavedBuild>('/builds', {
    method: 'POST',
    json: data,
  });
}
