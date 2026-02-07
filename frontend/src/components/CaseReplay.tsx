"use client";

const ROLE_COLORS: Record<string, string> = {
  Orthodox: "border-blue-500/40 bg-blue-950/20",
  Heretic: "border-orange-500/40 bg-orange-950/20",
  Skeptic: "border-purple-500/40 bg-purple-950/20",
  Judge: "border-emerald-500/40 bg-emerald-950/20",
};

interface Props {
  data: {
    case_id: string;
    messages: { role: string; model_key: string; content: string; created_at: string }[];
    results: {
      model_key: string;
      verdict: string;
      label: string;
      score: number;
      passed: boolean;
      judge_json: Record<string, unknown>;
      critical_fail_reason: string | null;
    }[];
  };
}

export function CaseReplay({ data }: Props) {
  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">
        Case Replay: <span className="text-cyan-400">{data.case_id}</span>
      </h1>

      {/* Messages */}
      <div className="space-y-3">
        {data.messages.map((m, i) => (
          <div
            key={i}
            className={`border rounded-lg p-4 ${ROLE_COLORS[m.role] ?? "border-slate-700"}`}
          >
            <div className="flex items-center gap-2 mb-2">
              <span className="text-sm font-bold">{m.role}</span>
              <span className="text-xs text-slate-500 font-mono">{m.model_key}</span>
            </div>
            <p className="text-sm text-slate-300 whitespace-pre-wrap leading-relaxed">
              {m.content}
            </p>
          </div>
        ))}
      </div>

      {/* Results */}
      <div className="card-glow">
        <h2 className="text-lg font-bold mb-3">Scoring Results</h2>
        {data.results.map((r, i) => (
          <div key={i} className="bg-slate-800/50 rounded-lg p-3 mb-2">
            <div className="flex justify-between items-center mb-2">
              <span className="font-mono text-sm">{r.model_key}</span>
              <span
                className={`text-sm font-bold px-2 py-0.5 rounded ${
                  r.passed
                    ? "bg-green-900/40 text-green-400"
                    : "bg-red-900/40 text-red-400"
                }`}
              >
                {r.score}/100 {r.passed ? "PASS" : "FAIL"}
              </span>
            </div>
            <p className="text-xs text-slate-400">
              Verdict: {r.verdict} | Label: {r.label}
            </p>
            {r.critical_fail_reason && (
              <p className="text-xs text-red-400 mt-1">
                Critical: {r.critical_fail_reason}
              </p>
            )}
            <details className="mt-2">
              <summary className="text-xs text-slate-500 cursor-pointer hover:text-slate-300">
                Judge JSON
              </summary>
              <pre className="text-xs text-slate-400 mt-1 bg-slate-900 p-2 rounded overflow-x-auto">
                {JSON.stringify(r.judge_json, null, 2)}
              </pre>
            </details>
          </div>
        ))}
      </div>
    </div>
  );
}
