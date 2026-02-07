/* Shared TypeScript interfaces. */

export type Verdict = "SUPPORTED" | "REFUTED" | "INSUFFICIENT";
export type RunStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface Dataset {
  id: string;
  version: string;
  description: string;
  case_count: number;
}

export interface DatasetCase {
  case_id: string;
  topic: string;
  claim: string;
  pressure_score: number;
  label: Verdict;
  evidence_packets: Evidence[];
}

export interface Evidence {
  eid: string;
  summary: string;
  source: string;
  date: string;
}

export interface ModelConfig {
  provider: string;
  model_name: string;
  api_key_env: string;
}

export interface RunRequest {
  dataset_id: string;
  models: ModelConfig[];
  max_cases?: number;
  mode: string;
}

export interface RunInfo {
  run_id: string;
  dataset_id: string;
  status: RunStatus;
  models: { provider: string; model_name: string }[];
  created_at: string;
  finished_at: string | null;
}

export interface CaseResult {
  case_id: string;
  model_key: string;
  verdict: Verdict;
  label: Verdict;
  score: number;
  passed: boolean;
  confidence: number;
  latency_ms: number;
  critical_fail_reason: string | null;
}

export interface ModelMetrics {
  model_key: string;
  total_cases: number;
  passed_cases: number;
  failed_cases: number;
  critical_fails: number;
  pass_rate: number;
  avg_score: number;
  avg_latency_ms: number;
  total_cost: number;
  high_pressure_pass_rate: number;
  model_passes_eval: boolean;
}

export interface RunSummary {
  run_id: string;
  status: RunStatus;
  total_cases: number;
  models: ModelMetrics[];
}

export interface AgentMessage {
  role: string;
  model_key: string;
  content: string;
  created_at?: string;
}

export interface SSEEvent {
  seq: number;
  event_type: string;
  payload: Record<string, unknown>;
  timestamp: string;
}
