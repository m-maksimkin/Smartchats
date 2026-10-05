import { useState } from 'react';

import { AiSettingsForm } from '../components/AiSettingsForm';
import { ChatWindow } from '../components/ChatWindow';
import { FieldError } from '../components/FieldError';
import { InterfaceSettingsForm } from '../components/InterfaceSettingsForm';
import { SaveBar } from '../components/SaveBar';
import { mount } from '../mount';
import type { ChatMessage, PageConfig } from '../types';
import { useChatSettings } from '../useChatSettings';

type Tab = 'ai' | 'interface';

const PREVIEW_MESSAGES: ChatMessage[] = [
  { id: 1, role: 'user', text: 'Как оформить возврат?', sources: [], pending: false, failed: false },
  {
    id: 2,
    role: 'assistant',
    text: 'Возврат можно оформить в течение 14 дней в личном кабинете.',
    sources: [],
    pending: false,
    failed: false,
  },
];

function SettingsPage({ config }: { config: PageConfig }) {
  const { draft, options, saving, error, fieldErrors, dirty, update, save, discard } = useChatSettings(
    config.chatUuid,
  );
  const [tab, setTab] = useState<Tab>('ai');
  const [savedMessage, setSavedMessage] = useState('');

  if (!draft || !options) {
    return <div className="text-center text-muted py-5">{error || 'Загрузка настроек...'}</div>;
  }

  const onSave = async () => {
    if (await save()) {
      setSavedMessage('Настройки сохранены');
    }
  };

  return (
    <div className="row g-4">
      <div className="col-lg-7">
        <div className="border rounded p-4">
          <div className="mb-4">
            <label className="form-label fw-semibold" htmlFor="sc-name">Название чат-бота</label>
            <input
              id="sc-name"
              className={`form-control${fieldErrors.name ? ' is-invalid' : ''}`}
              maxLength={50}
              value={draft.name}
              onChange={(event) => update({ name: event.target.value })}
            />
            <FieldError message={fieldErrors.name} />
          </div>

          <ul className="nav nav-tabs mb-4">
            <li className="nav-item">
              <button type="button" className={`nav-link${tab === 'ai' ? ' active' : ''}`} onClick={() => setTab('ai')}>
                ИИ
              </button>
            </li>
            <li className="nav-item">
              <button
                type="button"
                className={`nav-link${tab === 'interface' ? ' active' : ''}`}
                onClick={() => setTab('interface')}
              >
                Интерфейс
              </button>
            </li>
          </ul>

          {tab === 'ai' ? (
            <AiSettingsForm value={draft} options={options} fieldErrors={fieldErrors} onChange={update} />
          ) : (
            <InterfaceSettingsForm value={draft} fieldErrors={fieldErrors} onChange={update} />
          )}

          <hr className="my-4" />
          <SaveBar
            dirty={dirty}
            saving={saving}
            error={error}
            savedMessage={savedMessage}
            onSave={onSave}
            onDiscard={discard}
          />
        </div>
      </div>

      <div className="col-lg-5">
        <div className="sc-sticky">
          <div className="d-flex justify-content-between align-items-center mb-2">
            <span className="fw-semibold">Предпросмотр</span>
            <a href={config.playgroundUrl} className="small">Проверить в песочнице</a>
          </div>
          <ChatWindow appearance={draft} messages={PREVIEW_MESSAGES} status="ready" />
        </div>
      </div>
    </div>
  );
}

mount('settings-root', (config) => <SettingsPage config={config} />);
