"use client";

import type { ModelMetrics } from "@/lib/types";

interface Props {
  models: ModelMetrics[];
}

export function Leaderboard({ models }: Props) {
  const sorted = [...models].sort((a, b) => b.pass_rate - a.pass_rate);

  return (
    <div className="glass-panel rounded-3xl p-6">
      <h2 className="text-lg font-medium text-cyan-300 mb-4">Leaderboard</h2>
      {sorted.length === 0 ? (
        <p className="text-sm text-white/50">Waiting for results...</p>
      ) : (
        <div className="space-y-3">
          {sorted.map((m, i) => (
            <div
              key={m.model_key}
              className="glass-button rounded-xl p-4 flex items-center justify-between transition"
            >
              <div className="flex items-center gap-3">
                <span className="text-xs font-medium text-white/40 w-5">
                  #{i + 1}
                </span>
                <div>
                  <p className="text-sm font-mono text-white/90">{m.model_key}</p>
                  <p className="text-xs text-white/50">
                    {m.passed_cases}/{m.total_cases} passed &middot;{" "}
                    {m.avg_latency_ms.toFixed(0)}ms avg
                  </p>
                </div>
              </div>
              <div className="text-right">
                <span
                  className={`text-sm font-medium ${
                    m.model_passes_eval ? "text-green-300" : "text-red-300"
                  }`}
                >
                  {(m.pass_rate * 100).toFixed(1)}%
                </span>
                <span
                  className={`ml-2 text-xs px-2 py-1 rounded-full ${
                    m.model_passes_eval
                      ? "bg-green-500/20 text-green-300 border border-green-500/30"
                      : "bg-red-500/20 text-red-300 border border-red-500/30"
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
