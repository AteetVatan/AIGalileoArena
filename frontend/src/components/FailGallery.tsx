"use client";

import Link from "next/link";
import type { CaseResult } from "@/lib/types";

interface Props {
  runId: string;
  results: CaseResult[];
}

export function FailGallery({ runId, results }: Props) {
  const failures = results.filter((r) => !r.passed).slice(0, 8);

  if (failures.length === 0) return null;

  return (
    <div className="card-glow">
      <h2 className="text-lg font-bold text-red-400 mb-3">
        Recent Failures ({failures.length})
      </h2>
      <div className="space-y-2">
        {failures.map((f, i) => (
          <Link
            key={i}
            href={`/run/${runId}/case/${f.case_id}`}
            className="block p-2 bg-slate-800/50 rounded hover:bg-slate-700/50 transition"
          >
            <div className="flex justify-between items-center">
              <span className="text-xs font-mono text-slate-400">{f.case_id}</span>
              <span className="text-xs text-red-400 font-bold">
                {f.score}/100
              </span>
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {f.model_key} &middot; {f.verdict}
              {f.critical_fail_reason && (
                <span className="text-red-500 ml-1">
                  CRITICAL: {f.critical_fail_reason.slice(0, 40)}
                </span>
              )}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}
