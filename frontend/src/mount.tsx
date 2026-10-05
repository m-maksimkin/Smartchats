import { StrictMode, type ReactElement } from 'react';
import { createRoot } from 'react-dom/client';

import './styles.css';
import type { PageConfig } from './types';

export function mount(rootId: string, render: (config: PageConfig) => ReactElement) {
  const root = document.getElementById(rootId);
  const configElement = document.getElementById('sc-config');
  if (!root || !configElement?.textContent) {
    return;
  }
  const config = JSON.parse(configElement.textContent) as PageConfig;
  createRoot(root).render(<StrictMode>{render(config)}</StrictMode>);
}
