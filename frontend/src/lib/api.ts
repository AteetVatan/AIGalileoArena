/* Typed API client for the FastAPI backend. */

import { API_BASE } from "./constants";
import type { Dataset, DatasetDetail, RunInfo, RunSummary, CaseResult, RunRequest } from "./types";

async function fetchJSON<T>(path: string): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
  return res.json() as Promise<T>;
}

export const api = {
  async listDatasets(): Promise<Dataset[]> {
    return fetchJSON<Dataset[]>("/datasets");
  },

  async getDataset(id: string) {
    return fetchJSON<DatasetDetail>(`/datasets/${id}`);
  },

  async createRun(body: RunRequest): Promise<{ run_id: string }> {
    const res = await fetch(`${API_BASE}/runs`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API ${res.status}: ${await res.text()}`);
    return res.json();
  },

  async getRun(runId: string): Promise<RunInfo> {
    return fetchJSON<RunInfo>(`/runs/${runId}`);
  },

  async getRunSummary(runId: string): Promise<RunSummary> {
    return fetchJSON<RunSummary>(`/runs/${runId}/summary`);
  },

  async getRunCases(
    runId: string,
    params?: { model?: string; status?: string; skip?: number; limit?: number }
  ): Promise<{ total: number; cases: CaseResult[] }> {
    const qs = new URLSearchParams();
    if (params?.model) qs.set("model", params.model);
    if (params?.status) qs.set("status", params.status);
    if (params?.skip) qs.set("skip", String(params.skip));
    if (params?.limit) qs.set("limit", String(params.limit));
    return fetchJSON(`/runs/${runId}/cases?${qs}`);
  },

  async getCaseReplay(runId: string, caseId: string) {
    return fetchJSON<{
      case_id: string;
      messages: { role: string; model_key: string; content: string; created_at: string }[];
      results: Record<string, unknown>[];
    }>(`/runs/${runId}/cases/${caseId}`);
  },

  eventsUrl(runId: string): string {
    return `${API_BASE}/runs/${runId}/events`;
  },
};
