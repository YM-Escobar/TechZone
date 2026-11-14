import type { User } from './api';
import { requireUser } from './session';

export async function requireAdminUser(): Promise<User | null> {
  const user = await requireUser();
  if (user.role !== 'admin') {
    location.replace('/');
    return null;
  }
  return user;
}
