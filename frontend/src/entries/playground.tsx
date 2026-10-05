import { useState } from 'react';

import { AiSettingsForm } from '../components/AiSettingsForm';
import { ChatWindow } from '../components/ChatWindow';
import { SaveBar } from '../components/SaveBar';
import { mount } from '../mount';
import type { PageConfig } from '../types';
import { useChatSettings } from '../useChatSettings';
import { useChatSocket } from '../useChatSocket';

function PlaygroundPage({ config }: { config: PageConfig }) {
  const { draft, options, saving, error, fieldErrors, dirty, update, save, discard } = useChatSettings(
    config.chatUuid,
  );
  const chat = useChatSocket(config.chatUuid);
  const [savedMessage, setSavedMessage] = useState('');

  if (!draft || !options) {
    return <div className="text-center text-muted py-5">{error || 'Загрузка...'}</div>;
  }

  const onSave = async () => {
    if (await save()) {
      setSavedMessage('Сохранено, диалог начат заново');
      chat.reset();
    }
  };

  return (
    <div className="row g-4">
      <div className="col-lg-4">
        <div className="border rounded p-4">
          <AiSettingsForm value={draft} options={options} fieldErrors={fieldErrors} onChange={update} compact />
          <hr className="my-4" />
          <SaveBar
            dirty={dirty}
            saving={saving}
            error={error}
            savedMessage={savedMessage}
            onSave={onSave}
            onDiscard={discard}
          />
          <div className="mt-3 small">
            <a href={config.settingsUrl}>Все настройки</a>
            <span className="text-muted"> · </span>
            <a href={config.sourcesUrl}>Источники</a>
          </div>
        </div>
      </div>

      <div className="col-lg-8 d-flex justify-content-center">
        <div className="sc-playground-chat">
          <ChatWindow
            appearance={draft}
            messages={chat.messages}
            status={chat.status}
            answering={chat.answering}
            onSend={chat.send}
            onReset={chat.reset}
          />
        </div>
      </div>
    </div>
  );
}

mount('playground-root', (config) => <PlaygroundPage config={config} />);
