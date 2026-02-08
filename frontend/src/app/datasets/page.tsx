"use client";

import { useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";
import { AVAILABLE_MODELS } from "@/lib/constants";
import type { Dataset, DatasetCase } from "@/lib/types";

export default function DatasetsPage() {
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [cases, setCases] = useState<DatasetCase[]>([]);
  const [casesLoading, setCasesLoading] = useState(false);
  const [selectedCaseId, setSelectedCaseId] = useState<string>("");
  const [models, setModels] = useState<Set<string>>(new Set());
  const [launching, setLaunching] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    api.listDatasets().then(setDatasets).catch(console.error);
  }, []);

  const handleSelectDataset = useCallback((dsId: string) => {
    setSelected(dsId);
    setSelectedCaseId("");
    setCases([]);
    setCasesLoading(true);
    api
      .getDataset(dsId)
      .then((detail) => setCases(detail.cases))
      .catch(console.error)
      .finally(() => setCasesLoading(false));
  }, []);

  const toggleModel = (key: string) => {
    setModels((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const handleLaunch = async () => {
    if (!selected || !selectedCaseId || models.size === 0) return;
    setLaunching(true);
    setError("");
    try {
      const modelConfigs = Array.from(models).map((key) => {
        const m = AVAILABLE_MODELS.find(
          (am) => `${am.provider}/${am.model_name}` === key
        )!;
        return { provider: m.provider, model_name: m.model_name, api_key_env: m.api_key_env };
      });
      const resp = await api.createRun({
        dataset_id: selected,
        case_id: selectedCaseId,
        models: modelConfigs,
        mode: "debate",
      });
      if (resp.run_id) {
        window.location.href = `/run/${resp.run_id}`;
      } else {
        setError("No run_id in response: " + JSON.stringify(resp));
      }
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      console.error(err);
      setError(msg);
    } finally {
      setLaunching(false);
    }
  };

  return (
    <div className="space-y-10">
      <h1 className="text-3xl font-bold">Datasets</h1>

      {/* Dataset cards */}
      <div className="grid md:grid-cols-2 gap-4">
        {datasets.map((ds) => (
          <button
            key={ds.id}
            onClick={() => handleSelectDataset(ds.id)}
            className={`card-glow text-left transition ${
              selected === ds.id ? "border-cyan-500 ring-1 ring-cyan-500/30" : ""
            }`}
          >
            <h3 className="text-lg font-semibold text-cyan-400">{ds.id}</h3>
            <p className="text-sm text-slate-400 mt-1">{ds.description}</p>
            <p className="text-xs text-slate-500 mt-2">
              {ds.case_count} cases &middot; v{ds.version}
            </p>
          </button>
        ))}
      </div>

      {/* Case selector */}
      {selected && (
        <div className="card-glow space-y-4">
          <h2 className="text-xl font-semibold">Select Case Topic</h2>
          {casesLoading ? (
            <p className="text-sm text-slate-400">Loading cases...</p>
          ) : cases.length === 0 ? (
            <p className="text-sm text-slate-500">No cases found.</p>
          ) : (
            <select
              value={selectedCaseId}
              onChange={(e) => setSelectedCaseId(e.target.value)}
              className="w-full bg-slate-800 border border-slate-600 rounded-lg px-3 py-2 text-sm text-slate-200 focus:border-cyan-500 focus:ring-1 focus:ring-cyan-500/30 outline-none"
            >
              <option value="">-- Choose a case --</option>
              {cases.map((c) => (
                <option key={c.case_id} value={c.case_id}>
                  {c.topic}
                </option>
              ))}
            </select>
          )}
        </div>
      )}

      {/* Model selector */}
      {selected && selectedCaseId && (
        <div className="card-glow space-y-4">
          <h2 className="text-xl font-semibold">Select Models</h2>
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-2">
            {AVAILABLE_MODELS.map((m) => {
              const key = `${m.provider}/${m.model_name}`;
              return (
                <label
                  key={key}
                  className="flex items-center gap-2 text-sm cursor-pointer hover:text-white"
                >
                  <input
                    type="checkbox"
                    checked={models.has(key)}
                    onChange={() => toggleModel(key)}
                    className="accent-cyan-500"
                  />
                  <span className="text-slate-300">{m.label}</span>
                </label>
              );
            })}
          </div>

          <div className="flex items-end gap-4 mt-4">
            <button
              onClick={handleLaunch}
              disabled={launching || models.size === 0}
              className="px-6 py-2 bg-cyan-600 hover:bg-cyan-500 disabled:bg-slate-700 rounded-lg font-medium text-sm transition"
            >
              {launching ? "Starting..." : "Run Debate"}
            </button>
          </div>
          {error && (
            <p className="text-sm text-red-400 mt-2">{error}</p>
          )}
        </div>
      )}
    </div>
  );
}
