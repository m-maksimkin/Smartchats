import type { ChatSettings, SettingsResponse } from './types';

export class ApiError extends Error {
  constructor(message: string, readonly fieldErrors: Record<string, string> = {}) {
    super(message);
  }
}

function csrfToken(): string {
  const match = document.cookie.match(/(?:^|;\s*)csrftoken=([^;]+)/);
  return match ? decodeURIComponent(match[1]) : '';
}

interface NinjaValidationError {
  loc: (string | number)[];
  msg: string;
}

async function request<T>(url: string, init: RequestInit = {}): Promise<T> {
  const response = await fetch(url, {
    credentials: 'same-origin',
    ...init,
    headers: {
      'Content-Type': 'application/json',
      'X-CSRFToken': csrfToken(),
      ...init.headers,
    },
  });
  if (response.ok) {
    return response.json() as Promise<T>;
  }
  if (response.status === 422) {
    const body = (await response.json()) as { detail: NinjaValidationError[] };
    const fieldErrors: Record<string, string> = {};
    for (const error of body.detail) {
      const field = String(error.loc[error.loc.length - 1]);
      fieldErrors[field] = error.msg.replace(/^Value error, /, '');
    }
    throw new ApiError('Проверьте выделенные поля', fieldErrors);
  }
  if (response.status === 401 || response.status === 403) {
    throw new ApiError('Сессия истекла, войдите снова');
  }
  throw new ApiError('Не удалось сохранить настройки');
}

const settingsUrl = (chatUuid: string) => `/api/chats/${chatUuid}/settings`;

export function fetchSettings(chatUuid: string): Promise<SettingsResponse> {
  return request<SettingsResponse>(settingsUrl(chatUuid));
}

export function saveSettings(chatUuid: string, settings: ChatSettings): Promise<SettingsResponse> {
  const { updated: _updated, ...payload } = settings;
  return request<SettingsResponse>(settingsUrl(chatUuid), {
    method: 'PUT',
    body: JSON.stringify(payload),
  });
}
