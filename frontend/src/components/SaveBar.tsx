interface SaveBarProps {
  dirty: boolean;
  saving: boolean;
  error: string;
  savedMessage: string;
  onSave: () => void;
  onDiscard: () => void;
}

export function SaveBar({ dirty, saving, error, savedMessage, onSave, onDiscard }: SaveBarProps) {
  return (
    <div className="sc-save-bar d-flex align-items-center justify-content-end gap-2">
      {error && <span className="text-danger small me-auto">{error}</span>}
      {!error && savedMessage && !dirty && <span className="text-success small me-auto">{savedMessage}</span>}
      <button type="button" className="btn btn-outline-secondary" disabled={!dirty || saving} onClick={onDiscard}>
        Отменить
      </button>
      <button type="button" className="btn btn-dark" disabled={!dirty || saving} onClick={onSave}>
        {saving ? 'Сохранение...' : 'Сохранить'}
      </button>
    </div>
  );
}
