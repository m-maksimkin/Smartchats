import type { ChatSettings, ReasoningEffort, SettingsOptions } from '../types';
import { FieldError } from './FieldError';

interface AiSettingsFormProps {
  value: ChatSettings;
  options: SettingsOptions;
  fieldErrors: Record<string, string>;
  onChange: (changes: Partial<ChatSettings>) => void;
  compact?: boolean;
}

export function AiSettingsForm({ value, options, fieldErrors, onChange, compact = false }: AiSettingsFormProps) {
  const selectedModel = options.models.find((model) => model.value === value.model);
  const reasoning = selectedModel?.reasoning ?? false;

  const applyPreset = (key: string) => {
    const preset = options.presets.find((item) => item.key === key);
    if (preset) {
      onChange({ instructions: preset.text });
    }
  };

  return (
    <div className="d-flex flex-column gap-3">
      <div>
        <label className="form-label fw-semibold" htmlFor="sc-model">Модель</label>
        <select
          id="sc-model"
          className="form-select"
          value={value.model}
          onChange={(event) => onChange({ model: event.target.value })}
        >
          {options.models.map((model) => (
            <option key={model.value} value={model.value}>{model.label}</option>
          ))}
        </select>
        <FieldError message={fieldErrors.model} />
      </div>

      {reasoning ? (
        <div>
          <label className="form-label fw-semibold" htmlFor="sc-reasoning">Глубина рассуждений</label>
          <select
            id="sc-reasoning"
            className="form-select"
            value={value.reasoning_effort}
            onChange={(event) => onChange({ reasoning_effort: event.target.value as ReasoningEffort })}
          >
            {options.reasoning_efforts.map((choice) => (
              <option key={choice.value} value={choice.value}>{choice.label}</option>
            ))}
          </select>
          <div className="form-text">Чем глубже, тем точнее и медленнее ответ.</div>
        </div>
      ) : (
        <div>
          <label className="form-label fw-semibold d-flex justify-content-between" htmlFor="sc-temperature">
            <span>Температура</span>
            <span className="text-muted">{value.temperature.toFixed(1)}</span>
          </label>
          <input
            id="sc-temperature"
            type="range"
            className="form-range"
            min={0}
            max={1}
            step={0.1}
            value={value.temperature}
            onChange={(event) => onChange({ temperature: Number(event.target.value) })}
          />
          <div className="d-flex justify-content-between form-text">
            <span>Точнее</span>
            <span>Креативнее</span>
          </div>
        </div>
      )}

      <div>
        <div className="d-flex flex-wrap justify-content-between align-items-end gap-2 mb-2">
          <label className="form-label fw-semibold mb-0" htmlFor="sc-instructions">Инструкции</label>
          <select
            className="form-select form-select-sm sc-preset-select"
            value=""
            onChange={(event) => applyPreset(event.target.value)}
            aria-label="Шаблон инструкций"
          >
            <option value="">Шаблон...</option>
            {options.presets.map((preset) => (
              <option key={preset.key} value={preset.key}>{preset.title}</option>
            ))}
          </select>
        </div>
        <textarea
          id="sc-instructions"
          className={`form-control${fieldErrors.instructions ? ' is-invalid' : ''}`}
          rows={compact ? 8 : 12}
          maxLength={10000}
          value={value.instructions}
          onChange={(event) => onChange({ instructions: event.target.value })}
        />
        <FieldError message={fieldErrors.instructions} />
      </div>

      {!compact && (
        <>
          <div>
            <label className="form-label fw-semibold" htmlFor="sc-max-tokens">Максимальная длина ответа (токены)</label>
            <input
              id="sc-max-tokens"
              type="number"
              className={`form-control${fieldErrors.max_output_tokens ? ' is-invalid' : ''}`}
              min={64}
              max={16000}
              placeholder="Без ограничения"
              value={value.max_output_tokens ?? ''}
              onChange={(event) =>
                onChange({ max_output_tokens: event.target.value ? Number(event.target.value) : null })
              }
            />
            <FieldError message={fieldErrors.max_output_tokens} />
          </div>

          <div>
            <label className="form-label fw-semibold d-flex justify-content-between" htmlFor="sc-top-k">
              <span>Фрагментов источников в ответе</span>
              <span className="text-muted">{value.similarity_top_k}</span>
            </label>
            <input
              id="sc-top-k"
              type="range"
              className="form-range"
              min={1}
              max={10}
              step={1}
              value={value.similarity_top_k}
              onChange={(event) => onChange({ similarity_top_k: Number(event.target.value) })}
            />
          </div>

          <div>
            <label className="form-label fw-semibold d-flex justify-content-between" htmlFor="sc-cutoff">
              <span>Порог релевантности</span>
              <span className="text-muted">{value.similarity_cutoff.toFixed(2)}</span>
            </label>
            <input
              id="sc-cutoff"
              type="range"
              className="form-range"
              min={0}
              max={1}
              step={0.05}
              value={value.similarity_cutoff}
              onChange={(event) => onChange({ similarity_cutoff: Number(event.target.value) })}
            />
            <div className="form-text">Фрагменты с меньшим сходством не попадут в контекст.</div>
          </div>

          <div className="form-check form-switch">
            <input
              id="sc-rewrite"
              className="form-check-input"
              type="checkbox"
              checked={value.rewrite_followups}
              onChange={(event) => onChange({ rewrite_followups: event.target.checked })}
            />
            <label className="form-check-label" htmlFor="sc-rewrite">
              Учитывать историю диалога при поиске
            </label>
            <div className="form-text">
              Уточняющий вопрос переписывается в самостоятельный перед поиском по источникам.
            </div>
          </div>
        </>
      )}
    </div>
  );
}
