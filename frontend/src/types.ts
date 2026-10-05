export type ReasoningEffort = 'none' | 'low' | 'medium' | 'high';

export interface ChatSettings {
  name: string;
  instructions: string;
  model: string;
  temperature: number;
  reasoning_effort: ReasoningEffort;
  max_output_tokens: number | null;
  similarity_top_k: number;
  similarity_cutoff: number;
  rewrite_followups: boolean;
  display_name: string;
  welcome_message: string;
  suggested_messages: string[];
  input_placeholder: string;
  accent_color: string;
  updated?: string;
}

export interface ModelChoice {
  value: string;
  label: string;
  reasoning: boolean;
}

export interface Choice {
  value: string;
  label: string;
}

export interface InstructionPreset {
  key: string;
  title: string;
  text: string;
}

export interface SettingsOptions {
  models: ModelChoice[];
  reasoning_efforts: Choice[];
  presets: InstructionPreset[];
}

export interface SettingsResponse {
  settings: ChatSettings;
  options: SettingsOptions;
}

export interface PageConfig {
  chatUuid: string;
  sourcesUrl: string;
  playgroundUrl: string;
  settingsUrl: string;
}

export type ChatStatus = 'connecting' | 'indexing' | 'ready' | 'error' | 'closed';

export interface ChatMessage {
  id: number;
  role: 'user' | 'assistant';
  text: string;
  sources: string[];
  pending: boolean;
  failed: boolean;
}
