import { useEffect, useRef, useState, type FormEvent } from 'react';
import Markdown from 'react-markdown';

import type { ChatMessage, ChatSettings, ChatStatus } from '../types';

export type ChatAppearance = Pick<
  ChatSettings,
  'name' | 'display_name' | 'welcome_message' | 'suggested_messages' | 'input_placeholder' | 'accent_color'
>;

const STATUS_TEXT: Record<ChatStatus, string> = {
  connecting: 'Подключение...',
  indexing: 'Обрабатываем источники...',
  ready: '',
  error: 'Не удалось подготовить чат-бота',
  closed: 'Соединение закрыто. Обновите страницу.',
};

interface ChatWindowProps {
  appearance: ChatAppearance;
  messages: ChatMessage[];
  status: ChatStatus;
  answering?: boolean;
  onSend?: (text: string) => void;
  onReset?: () => void;
}

export function ChatWindow({ appearance, messages, status, answering = false, onSend, onReset }: ChatWindowProps) {
  const [input, setInput] = useState('');
  const listRef = useRef<HTMLDivElement>(null);
  const interactive = Boolean(onSend);
  const canSend = interactive && status === 'ready' && !answering;
  const title = appearance.display_name || appearance.name;
  const statusText = interactive ? STATUS_TEXT[status] : '';

  useEffect(() => {
    listRef.current?.scrollTo({ top: listRef.current.scrollHeight });
  }, [messages]);

  const submit = (event: FormEvent) => {
    event.preventDefault();
    if (canSend && input.trim()) {
      onSend?.(input);
      setInput('');
    }
  };

  return (
    <div className="sc-chat card shadow-sm" style={{ ['--sc-accent' as string]: appearance.accent_color }}>
      <div className="sc-chat-header d-flex align-items-center justify-content-between">
        <span className="fw-semibold">{title}</span>
        {onReset && (
          <button type="button" className="btn btn-sm sc-chat-header-button" onClick={onReset} title="Начать заново">
            ↻
          </button>
        )}
      </div>

      <div className="sc-chat-messages" ref={listRef}>
        {appearance.welcome_message && (
          <div className="sc-message sc-message-assistant">{appearance.welcome_message}</div>
        )}
        {messages.map((message) => (
          <div
            key={message.id}
            className={`sc-message sc-message-${message.role}${message.failed ? ' sc-message-failed' : ''}`}
          >
            {message.role === 'assistant' ? (
              message.text ? <Markdown>{message.text}</Markdown> : <span className="sc-typing">...</span>
            ) : (
              message.text
            )}
            {message.sources.length > 0 && (
              <div className="sc-sources">Источники: {message.sources.join(', ')}</div>
            )}
          </div>
        ))}
        {statusText && <div className="sc-status text-muted small text-center">{statusText}</div>}
      </div>

      {messages.length === 0 && appearance.suggested_messages.length > 0 && (
        <div className="sc-suggestions">
          {appearance.suggested_messages.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              className="btn btn-sm btn-outline-secondary"
              disabled={interactive && !canSend}
              onClick={() => canSend && onSend?.(suggestion)}
            >
              {suggestion}
            </button>
          ))}
        </div>
      )}

      <form className="sc-chat-input d-flex" onSubmit={submit}>
        <input
          className="form-control me-2"
          type="text"
          value={input}
          maxLength={4000}
          placeholder={appearance.input_placeholder}
          disabled={!canSend}
          onChange={(event) => setInput(event.target.value)}
        />
        <button type="submit" className="btn sc-send-button" disabled={!canSend || !input.trim()}>
          Отправить
        </button>
      </form>
    </div>
  );
}
