/* Typed API client for the FastAPI backend. */

import { API_BASE } from "./constants";
import type {
  Dataset,
  DatasetDetail,
  RunInfo,
  RunSummary,
  CaseResult,
  RunRequest,
  AvailableKeysResponse,
  KeyValidationResult,
} from "./types";
import {
  RunInfoSchema,
  RunSummarySchema
} from "./schemas";
import type { CaseReplayData } from "./eventTypes";

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
    const data = await fetchJSON<unknown>(`/runs/${runId}`);
    return RunInfoSchema.parseAsync(data);
  },

  async getRunSummary(runId: string): Promise<RunSummary> {
    const data = await fetchJSON<unknown>(`/runs/${runId}/summary`);
    return RunSummarySchema.parseAsync(data);
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
    return fetchJSON<CaseReplayData>(`/runs/${runId}/cases/${caseId}`);
  },

  async getRunMessages(runId: string) {
    return fetchJSON<Array<{
      role: string;
      model_key: string;
      content: string;
      phase: string | null;
      round: number | null;
      created_at: string;
    }>>(`/runs/${runId}/messages`);
  },

  async getAvailableKeys(): Promise<{ available_keys: string[] }> {
    return fetchJSON<{ available_keys: string[] }>("/models/available-keys");
  },

  async validateKeys(force?: boolean): Promise<Record<string, KeyValidationResult>> {
    try {
      const qs = new URLSearchParams();
      qs.set("validate", "true");
      if (force) {
        qs.set("force", "true");
      }
      const response = await fetchJSON<AvailableKeysResponse>(
        `/models/available-keys?${qs}`
      );
      return response.validation || {};
    } catch (err) {
      // Handle errors gracefully - return empty dict so validation failure doesn't break the page
      const errorMessage = err instanceof Error ? err.message : String(err);
      // Only log non-rate-limit errors to avoid console spam
      if (!errorMessage.includes("429") && !errorMessage.includes("Rate limit")) {
        console.error("Failed to validate keys:", err);
      }
      return {};
    }
  },

  eventsUrl(runId: string): string {
    return `${API_BASE}/runs/${runId}/events`;
  },
};
