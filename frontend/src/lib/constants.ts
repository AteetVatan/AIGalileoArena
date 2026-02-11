/* Available models (6 providers) and API config. */

export const API_BASE = "/api";

// SSE must bypass the Next.js rewrite proxy (which buffers the response body).
// EventSource connects directly to the backend for real-time streaming.
export const SSE_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface AvailableModel {
  id: string;
  provider: string;
  model_name: string;
  label: string;
  api_key_env: string;
  context_window: string;
}

export const AVAILABLE_MODELS: AvailableModel[] = [
  { id: "openai/gpt-4o", provider: "openai", model_name: "gpt-4o", label: "OpenAI GPT-4o", api_key_env: "OPENAI_API_KEY", context_window: "128k" },
  { id: "anthropic/claude-sonnet", provider: "anthropic", model_name: "claude-sonnet-4-20250514", label: "Anthropic Claude Sonnet", api_key_env: "ANTHROPIC_API_KEY", context_window: "200k" },
  { id: "mistral/large", provider: "mistral", model_name: "mistral-large-latest", label: "Mistral Large", api_key_env: "MISTRAL_API_KEY", context_window: "32k" },
  { id: "deepseek/chat", provider: "deepseek", model_name: "deepseek-chat", label: "DeepSeek Chat", api_key_env: "DEEPSEEK_API_KEY", context_window: "32k" },
  { id: "grok/3", provider: "grok", model_name: "grok-3", label: "Grok 3", api_key_env: "GROK_API_KEY", context_window: "131k" },
];

export const ROLE_COLORS: Record<string, string> = {
  Orthodox: "text-cyan-300",
  Heretic: "text-pink-300",
  Skeptic: "text-purple-300",
  Judge: "text-emerald-300",
};