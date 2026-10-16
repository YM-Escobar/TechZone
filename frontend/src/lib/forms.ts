import { escapeHtml } from './format';

/**
 * Maneja el envío de un formulario: desactiva el botón, muestra el error en `[data-alert]`
 * y llama a `handler` con los datos. Si `handler` devuelve un texto, se muestra como éxito.
 */
export function onSubmit(
  form: HTMLFormElement,
  handler: (data: FormData) => Promise<string | void>,
) {
  const button = form.querySelector<HTMLButtonElement>('button[type=submit], button:not([type])');
  const alert = form.querySelector<HTMLElement>('[data-alert]');
  const label = button?.textContent ?? '';

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    if (button) {
      button.disabled = true;
      button.textContent = 'Un momento…';
    }
    showAlert(alert, null);
    try {
      const ok = await handler(new FormData(form));
      if (ok) showAlert(alert, ok, 'ok');
    } catch (err) {
      showAlert(alert, (err as Error).message, 'error');
    } finally {
      if (button) {
        button.disabled = false;
        button.textContent = label;
      }
    }
  });
}

export function showAlert(el: HTMLElement | null, message: string | null, kind: 'ok' | 'error' = 'error') {
  if (!el) return;
  if (!message) {
    el.hidden = true;
    return;
  }
  el.hidden = false;
  el.className = kind === 'ok' ? 'alert-ok' : 'alert-error';
  el.innerHTML = escapeHtml(message);
}

export const str = (data: FormData, key: string) => String(data.get(key) ?? '').trim();
