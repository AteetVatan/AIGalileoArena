"use client";

import type { CaseResult } from "@/lib/types";

interface Props {
  results: CaseResult[];
}

export function TopicHeatmap({ results }: Props) {
  // Group by model_key, compute avg score per model
  const byModel: Record<string, number[]> = {};
  for (const r of results) {
    if (!byModel[r.model_key]) byModel[r.model_key] = [];
    byModel[r.model_key].push(r.score);
  }

  if (Object.keys(byModel).length === 0) return null;

  return (
    <div className="card-glow">
      <h2 className="text-lg font-bold text-cyan-400 mb-3">Model Score Heatmap</h2>
      <div className="space-y-2">
        {Object.entries(byModel).map(([model, scores]) => {
          const avg = scores.reduce((a, b) => a + b, 0) / scores.length;
          const pct = Math.round(avg);
          return (
            <div key={model} className="flex items-center gap-3">
              <span className="text-xs font-mono w-40 truncate text-slate-400">
                {model}
              </span>
              <div className="flex-1 bg-slate-800 rounded-full h-4 overflow-hidden">
                <div
                  className={`h-full rounded-full transition-all duration-500 ${
                    pct >= 80 ? "bg-green-500" : pct >= 50 ? "bg-yellow-500" : "bg-red-500"
                  }`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-xs text-slate-400 w-10 text-right">{pct}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}
