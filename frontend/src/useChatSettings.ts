import { useCallback, useEffect, useState } from 'react';

import { ApiError, fetchSettings, saveSettings } from './api';
import type { ChatSettings, SettingsOptions } from './types';

export function useChatSettings(chatUuid: string) {
  const [saved, setSaved] = useState<ChatSettings | null>(null);
  const [draft, setDraft] = useState<ChatSettings | null>(null);
  const [options, setOptions] = useState<SettingsOptions | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    fetchSettings(chatUuid)
      .then((response) => {
        setSaved(response.settings);
        setDraft(response.settings);
        setOptions(response.options);
      })
      .catch(() => setError('Не удалось загрузить настройки'));
  }, [chatUuid]);

  const update = useCallback((changes: Partial<ChatSettings>) => {
    setDraft((current) => (current ? { ...current, ...changes } : current));
  }, []);

  const discard = useCallback(() => {
    setDraft(saved);
    setFieldErrors({});
    setError('');
  }, [saved]);

  const save = useCallback(async (): Promise<boolean> => {
    if (!draft) {
      return false;
    }
    setSaving(true);
    setError('');
    setFieldErrors({});
    try {
      const response = await saveSettings(chatUuid, draft);
      setSaved(response.settings);
      setDraft(response.settings);
      return true;
    } catch (exception) {
      if (exception instanceof ApiError) {
        setError(exception.message);
        setFieldErrors(exception.fieldErrors);
      } else {
        setError('Не удалось сохранить настройки');
      }
      return false;
    } finally {
      setSaving(false);
    }
  }, [chatUuid, draft]);

  const dirty = JSON.stringify(saved) !== JSON.stringify(draft);

  return { draft, options, saving, error, fieldErrors, dirty, update, save, discard };
}
