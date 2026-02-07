"use client";

import type { CaseResult } from "@/lib/types";

interface Props {
  results: CaseResult[];
}

const LABELS = ["SUPPORTED", "REFUTED", "INSUFFICIENT"] as const;

export function ConfusionMatrix({ results }: Props) {
  // Build a simple count matrix: verdict (predicted) vs label (actual)
  const matrix: Record<string, Record<string, number>> = {};
  for (const l of LABELS) {
    matrix[l] = {};
    for (const v of LABELS) matrix[l][v] = 0;
  }

  for (const r of results) {
    const actual = r.label || "INSUFFICIENT";
    const predicted = r.verdict || "INSUFFICIENT";
    if (matrix[actual] && matrix[actual][predicted] !== undefined) {
      matrix[actual][predicted]++;
    }
  }

  if (results.length === 0) return null;

  return (
    <div className="card-glow">
      <h2 className="text-lg font-bold text-cyan-400 mb-3">Confusion Matrix</h2>
      <div className="overflow-x-auto">
        <table className="w-full text-xs">
          <thead>
            <tr>
              <th className="text-left text-slate-500 py-1 px-2">Actual \ Predicted</th>
              {LABELS.map((l) => (
                <th key={l} className="text-center text-slate-400 py-1 px-2">
                  {l.slice(0, 3)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {LABELS.map((actual) => (
              <tr key={actual}>
                <td className="text-slate-400 py-1 px-2 font-medium">
                  {actual.slice(0, 3)}
                </td>
                {LABELS.map((predicted) => {
                  const count = matrix[actual][predicted];
                  const isCorrect = actual === predicted;
                  return (
                    <td
                      key={predicted}
                      className={`text-center py-1 px-2 rounded ${
                        isCorrect && count > 0
                          ? "bg-green-900/30 text-green-400"
                          : count > 0
                          ? "bg-red-900/20 text-red-400"
                          : "text-slate-600"
                      }`}
                    >
                      {count}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
