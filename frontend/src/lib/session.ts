import { api, ApiError, tokens, type Tokens, type User } from './api';

let current: Promise<User | null> | null = null;
const listeners = new Set<(user: User | null) => void>();

function publish(user: User | null) {
  current = Promise.resolve(user);
  listeners.forEach((fn) => fn(user));
}

/** Usuario con sesión iniciada, o null. Se pide al backend una sola vez por página. */
export function currentUser(): Promise<User | null> {
  if (!tokens.access) return Promise.resolve(null);
  current ??= api<User>('/users/me').catch((err) => {
    if (err instanceof ApiError && err.status === 401) tokens.clear();
    return null;
  });
  return current;
}

/** Se llama con el usuario actual y cada vez que cambia (login, logout, edición de perfil). */
export function onUserChange(fn: (user: User | null) => void) {
  listeners.add(fn);
  currentUser().then(fn);
}

export function setUser(user: User) {
  publish(user);
}

export async function login(identifier: string, password: string): Promise<User | null> {
  const form = new URLSearchParams({ username: identifier, password });
  tokens.save(await api<Tokens>('/auth/login', { method: 'POST', form, auth: false }));
  current = null;
  const user = await currentUser();
  publish(user);
  return user;
}

export async function logout() {
  const refresh_token = tokens.refresh;
  if (refresh_token) {
    await api('/auth/logout', { method: 'POST', json: { refresh_token }, auth: false }).catch(() => {});
  }
  tokens.clear();
  publish(null);
}

/** Para páginas privadas: si no hay sesión, manda al login y vuelve aquí después. */
export async function requireUser(): Promise<User> {
  const user = await currentUser();
  if (!user) {
    const next = encodeURIComponent(location.pathname + location.search);
    location.replace(`/login?next=${next}`);
    return new Promise(() => {});
  }
  return user;
}

/** Destino seguro tras iniciar sesión (solo rutas internas). */
export function nextUrl(fallback = '/'): string {
  const next = new URLSearchParams(location.search).get('next');
  return next && next.startsWith('/') && !next.startsWith('//') ? next : fallback;
}
