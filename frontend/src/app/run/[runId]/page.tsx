"use client";

import { useState, useCallback, useEffect } from "react";
import { useParams } from "next/navigation";
import { useSSE } from "@/hooks/useSSE";
import { useRunData } from "@/hooks/useRunData";
import { api } from "@/lib/api";
import { Leaderboard } from "@/components/Leaderboard";
import { LiveTranscript } from "@/components/LiveTranscript";
import { PressureScatter } from "@/components/PressureScatter";
import { ConfusionMatrix } from "@/components/ConfusionMatrix";
import { CalibrationChart } from "@/components/CalibrationChart";
import { FailGallery } from "@/components/FailGallery";
import type { SSEEvent, AgentMessage, CaseResult, DatasetDetail } from "@/lib/types";

export default function RunDashboard() {
  const { runId } = useParams<{ runId: string }>();
  const { run, summary, loading } = useRunData(runId);
  const [messages, setMessages] = useState<AgentMessage[]>([]);
  const [scores, setScores] = useState<CaseResult[]>([]);
  const [progress, setProgress] = useState({ completed: 0, total: 0 });
  const [datasetInfo, setDatasetInfo] = useState<{ datasetId: string; caseTopic: string } | null>(null);

  const handleEvent = useCallback((event: SSEEvent) => {
    const p = event.payload as Record<string, any>;
    switch (event.event_type) {
      case "agent_message":
        setMessages((prev) => [
          ...prev,
          {
            role: p.role,
            model_key: p.model_key,
            content: p.content,
            phase: p.phase,
            round: p.round,
          },
        ]);
        break;
      case "case_scored":
        setScores((prev) => [
          ...prev,
          {
            case_id: p.case_id,
            model_key: p.model_key,
            verdict: p.verdict,
            label: "",
            score: p.score,
            passed: p.passed,
            confidence: 0,
            latency_ms: 0,
            critical_fail_reason: null,
          },
        ]);
        break;
      case "metrics_update":
        setProgress({ completed: p.completed ?? 0, total: p.total ?? 0 });
        break;
    }
  }, []);

  useSSE(runId ? api.eventsUrl(runId) : null, handleEvent);

  // Fetch dataset and case information when run data is available
  useEffect(() => {
    if (!run?.dataset_id || !run?.case_id) return;

    const fetchDatasetInfo = async () => {
      try {
        const dataset: DatasetDetail = await api.getDataset(run.dataset_id);
        const caseData = dataset.cases.find((c) => c.case_id === run.case_id);
        if (caseData) {
          setDatasetInfo({
            datasetId: dataset.id,
            caseTopic: caseData.topic,
          });
        }
      } catch (err) {
        console.error("Failed to fetch dataset info:", err);
      }
    };

    fetchDatasetInfo();
  }, [run?.dataset_id, run?.case_id]);

  if (loading) {
    return <div className="text-slate-400 text-center py-20">Loading run...</div>;
  }

  const pct =
    progress.total > 0
      ? Math.round((progress.completed / progress.total) * 100)
      : 0;

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">
            {datasetInfo ? (
              <span>
                <span className="text-cyan-400">{datasetInfo.datasetId}</span>
                <span className="text-slate-400">-</span>
                <span className="text-cyan-400">{datasetInfo.caseTopic}</span>
              </span>
            ) : (
              <>
                Run <span className="text-cyan-400">{runId?.slice(0, 8)}</span>
              </>
            )}
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Status:{" "}
            <span
              className={
                run?.status === "COMPLETED"
                  ? "text-green-400"
                  : run?.status === "FAILED"
                  ? "text-red-400"
                  : "text-yellow-400"
              }
            >
              {run?.status || "PENDING"}
            </span>
          </p>
        </div>
        {progress.total > 0 && (
          <div className="text-right">
            <p className="text-sm text-slate-400 mb-1">
              {progress.completed}/{progress.total} cases ({pct}%)
            </p>
            <div className="w-48 bg-slate-800 rounded-full h-2">
              <div
                className="bg-cyan-500 h-2 rounded-full transition-all duration-300"
                style={{ width: `${pct}%` }}
              />
            </div>
          </div>
        )}
      </div>

      {/* Debug Info - Only shown when backend is in debug mode */}
      {(run?.debug_mode ?? summary?.debug_mode ?? false) && (
        <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
          <h2 className="text-sm font-bold text-slate-400 mb-2">Debug Info</h2>
          <div className="space-y-1 text-xs font-mono">
            <div className="flex justify-between">
              <span className="text-slate-500">Total LLM Cost:</span>
              <span className="text-cyan-400">
                ${(run?.total_llm_cost ?? summary?.total_llm_cost ?? 0).toFixed(6)}
              </span>
            </div>
            {summary?.models && summary.models.length > 0 && (
              <div className="mt-2 pt-2 border-t border-slate-700">
                <div className="text-slate-500 mb-1">Per Model Costs:</div>
                {summary.models.map((model) => (
                  <div key={model.model_key} className="flex justify-between ml-2">
                    <span className="text-slate-400">{model.model_key}:</span>
                    <span className="text-cyan-400">${model.total_cost.toFixed(6)}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Main grid */}
      <div className="grid lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <LiveTranscript messages={messages} />
          <PressureScatter results={scores} />
          <ConfusionMatrix results={scores} />
        </div>
        <div className="space-y-6">
          <Leaderboard models={summary?.models ?? []} />
          <CalibrationChart results={scores} />
          <FailGallery runId={runId} results={scores} />
        </div>
      </div>
    </div>
  );
}
