/* Available models (6 providers) and API config. */

export const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AvailableModel {
  provider: string;
  model_name: string;
  label: string;
  api_key_env: string;
}

export const AVAILABLE_MODELS: AvailableModel[] = [
  { provider: "openai", model_name: "gpt-4o", label: "OpenAI GPT-4o", api_key_env: "OPENAI_API_KEY" },
  { provider: "openai", model_name: "gpt-4o-mini", label: "OpenAI GPT-4o Mini", api_key_env: "OPENAI_API_KEY" },
  { provider: "anthropic", model_name: "claude-sonnet-4-20250514", label: "Anthropic Claude Sonnet", api_key_env: "ANTHROPIC_API_KEY" },
  { provider: "anthropic", model_name: "claude-3-haiku-20240307", label: "Anthropic Claude Haiku", api_key_env: "ANTHROPIC_API_KEY" },
  { provider: "mistral", model_name: "mistral-large-latest", label: "Mistral Large", api_key_env: "MISTRAL_API_KEY" },
  { provider: "deepseek", model_name: "deepseek-chat", label: "DeepSeek Chat", api_key_env: "DEEPSEEK_API_KEY" },
  { provider: "deepseek", model_name: "deepseek-reasoner", label: "DeepSeek Reasoner", api_key_env: "DEEPSEEK_API_KEY" },
  { provider: "gemini", model_name: "gemini-2.0-flash", label: "Gemini 2.0 Flash", api_key_env: "GEMINI_API_KEY" },
  { provider: "gemini", model_name: "gemini-1.5-pro", label: "Gemini 1.5 Pro", api_key_env: "GEMINI_API_KEY" },
  { provider: "grok", model_name: "grok-2", label: "Grok 2", api_key_env: "GROK_API_KEY" },
  { provider: "grok", model_name: "grok-2-mini", label: "Grok 2 Mini", api_key_env: "GROK_API_KEY" },
];
