"use client";

import type { ModelMetrics } from "@/lib/types";

interface Props {
  models: ModelMetrics[];
}

export function Leaderboard({ models }: Props) {
  const sorted = [...models].sort((a, b) => b.pass_rate - a.pass_rate);

  return (
    <div className="card-glow">
      <h2 className="text-lg font-bold text-cyan-400 mb-4">Leaderboard</h2>
      {sorted.length === 0 ? (
        <p className="text-sm text-slate-500">Waiting for results...</p>
      ) : (
        <div className="space-y-3">
          {sorted.map((m, i) => (
            <div
              key={m.model_key}
              className="flex items-center justify-between p-3 bg-slate-800/60 rounded-lg"
            >
              <div className="flex items-center gap-3">
                <span className="text-xs font-bold text-slate-500 w-5">
                  #{i + 1}
                </span>
                <div>
                  <p className="text-sm font-mono">{m.model_key}</p>
                  <p className="text-xs text-slate-500">
                    {m.passed_cases}/{m.total_cases} passed &middot;{" "}
                    {m.avg_latency_ms.toFixed(0)}ms avg
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span
                  className={`text-sm font-bold ${
                    m.model_passes_eval ? "text-green-400" : "text-red-400"
                  }`}
                >
                  {(m.pass_rate * 100).toFixed(1)}%
                </span>
                <span
                  className={`ml-2 text-xs px-2 py-0.5 rounded ${
                    m.model_passes_eval
                      ? "bg-green-900/40 text-green-400"
                      : "bg-red-900/40 text-red-400"
                  }`}
                >
                  {m.model_passes_eval ? "PASS" : "FAIL"}
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
