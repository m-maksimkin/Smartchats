import type { ChatSettings } from '../types';
import { FieldError } from './FieldError';

const MAX_SUGGESTIONS = 6;

interface InterfaceSettingsFormProps {
  value: ChatSettings;
  fieldErrors: Record<string, string>;
  onChange: (changes: Partial<ChatSettings>) => void;
}

export function InterfaceSettingsForm({ value, fieldErrors, onChange }: InterfaceSettingsFormProps) {
  const suggestionsText = value.suggested_messages.join('\n');

  return (
    <div className="d-flex flex-column gap-3">
      <div>
        <label className="form-label fw-semibold" htmlFor="sc-display-name">Имя в окне чата</label>
        <input
          id="sc-display-name"
          className={`form-control${fieldErrors.display_name ? ' is-invalid' : ''}`}
          maxLength={60}
          placeholder={value.name}
          value={value.display_name}
          onChange={(event) => onChange({ display_name: event.target.value })}
        />
        <FieldError message={fieldErrors.display_name} />
      </div>

      <div>
        <label className="form-label fw-semibold" htmlFor="sc-welcome">Приветственное сообщение</label>
        <textarea
          id="sc-welcome"
          className={`form-control${fieldErrors.welcome_message ? ' is-invalid' : ''}`}
          rows={2}
          maxLength={500}
          value={value.welcome_message}
          onChange={(event) => onChange({ welcome_message: event.target.value })}
        />
        <FieldError message={fieldErrors.welcome_message} />
      </div>

      <div>
        <label className="form-label fw-semibold" htmlFor="sc-suggestions">Подсказки для вопросов</label>
        <textarea
          id="sc-suggestions"
          className={`form-control${fieldErrors.suggested_messages ? ' is-invalid' : ''}`}
          rows={4}
          value={suggestionsText}
          onChange={(event) =>
            onChange({ suggested_messages: event.target.value.split('\n').slice(0, MAX_SUGGESTIONS) })
          }
        />
        <div className="form-text">Каждая подсказка с новой строки, до {MAX_SUGGESTIONS} штук.</div>
        <FieldError message={fieldErrors.suggested_messages} />
      </div>

      <div>
        <label className="form-label fw-semibold" htmlFor="sc-placeholder">Подсказка в поле ввода</label>
        <input
          id="sc-placeholder"
          className={`form-control${fieldErrors.input_placeholder ? ' is-invalid' : ''}`}
          maxLength={120}
          value={value.input_placeholder}
          onChange={(event) => onChange({ input_placeholder: event.target.value })}
        />
        <FieldError message={fieldErrors.input_placeholder} />
      </div>

      <div>
        <label className="form-label fw-semibold" htmlFor="sc-accent">Цвет акцента</label>
        <div className="d-flex align-items-center gap-2">
          <input
            id="sc-accent"
            type="color"
            className="form-control form-control-color"
            value={value.accent_color}
            onChange={(event) => onChange({ accent_color: event.target.value })}
          />
          <code>{value.accent_color}</code>
        </div>
        <FieldError message={fieldErrors.accent_color} />
      </div>
    </div>
  );
}
