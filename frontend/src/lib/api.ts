// Cliente de la API de TechZone (backend FastAPI).
// Guarda los tokens en localStorage y renueva el access token una vez si el backend responde 401.

export const API_URL = (import.meta.env.PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');

const ACCESS_KEY = 'tz_access';
const REFRESH_KEY = 'tz_refresh';

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export interface Tokens {
  access_token: string;
  refresh_token: string;
}

export interface Page<T> {
  items: T[];
  total: number;
  skip: number;
  limit: number;
}

export type Role = 'usuario' | 'asesor' | 'admin';

export interface User {
  id: number;
  username: string;
  full_name: string | null;
  avatar_url: string | null;
  role: Role;
  bio: string | null;
  email: string;
  is_active: boolean;
  is_verified: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: number;
  name: string;
  brand: string;
  category: string;
  description: string | null;
  price: number;
  stock: number;
  image_url: string | null;
  specs: Record<string, unknown>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

function storage(): Storage | null {
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

export const tokens = {
  get access() {
    return storage()?.getItem(ACCESS_KEY) ?? null;
  },
  get refresh() {
    return storage()?.getItem(REFRESH_KEY) ?? null;
  },
  save(t: Tokens) {
    storage()?.setItem(ACCESS_KEY, t.access_token);
    storage()?.setItem(REFRESH_KEY, t.refresh_token);
  },
  clear() {
    storage()?.removeItem(ACCESS_KEY);
    storage()?.removeItem(REFRESH_KEY);
  },
};

/** Convierte las rutas relativas del backend (/uploads/...) en URLs absolutas. */
export function mediaUrl(path: string | null | undefined): string | null {
  if (!path) return null;
  return path.startsWith('/') ? `${API_URL}${path}` : path;
}

/** Saca un mensaje legible de una respuesta de error de FastAPI. */
function errorMessage(body: unknown, status: number): string {
  const detail = (body as { detail?: unknown } | null)?.detail;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail) && detail.length) {
    // Errores de validación (422): [{ loc: [...], msg: "..." }]
    return detail
      .map((d: { loc?: (string | number)[]; msg?: string }) => {
        const field = d.loc?.filter((p) => p !== 'body' && p !== 'query').join('.');
        const msg = (d.msg ?? '').replace(/^Value error, /, '');
        return field ? `${field}: ${msg}` : msg;
      })
      .join(' · ');
  }
  if (status >= 500) return 'El servidor tuvo un problema. Intenta de nuevo en un momento.';
  return 'No se pudo completar la solicitud.';
}

let refreshing: Promise<boolean> | null = null;

async function refreshTokens(): Promise<boolean> {
  const refresh_token = tokens.refresh;
  if (!refresh_token) return false;
  // Si varias peticiones fallan a la vez, comparten un solo refresh
  refreshing ??= fetch(`${API_URL}/api/auth/refresh`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ refresh_token }),
  })
    .then(async (res) => {
      if (!res.ok) {
        tokens.clear();
        return false;
      }
      tokens.save(await res.json());
      return true;
    })
    .catch(() => false)
    .finally(() => {
      refreshing = null;
    });
  return refreshing;
}

interface RequestOptions {
  method?: string;
  json?: unknown;
  form?: FormData | URLSearchParams;
  query?: Record<string, string | number | boolean | null | undefined>;
  auth?: boolean;
}

export async function api<T>(path: string, opts: RequestOptions = {}, retried = false): Promise<T> {
  const url = new URL(`${API_URL}/api${path}`);
  for (const [key, value] of Object.entries(opts.query ?? {})) {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value));
  }

  const headers: Record<string, string> = {};
  let body: BodyInit | undefined;
  if (opts.json !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(opts.json);
  } else if (opts.form) {
    body = opts.form;
  }
  const access = tokens.access;
  if (access && opts.auth !== false) headers.Authorization = `Bearer ${access}`;

  let res: Response;
  try {
    res = await fetch(url, { method: opts.method ?? 'GET', headers, body });
  } catch {
    throw new ApiError(0, 'No hay conexión con el servidor.');
  }

  if (res.status === 401 && access && !retried && (await refreshTokens())) {
    return api<T>(path, opts, true);
  }
  if (res.status === 204) return undefined as T;

  const data = await res.json().catch(() => null);
  if (!res.ok) throw new ApiError(res.status, errorMessage(data, res.status));
  return data as T;
}
