"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import { AVAILABLE_MODELS, type AvailableModel } from "@/lib/constants";
import type { Dataset } from "@/lib/types";

export default function DatasetsPage() {
  const router = useRouter();
  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selected, setSelected] = useState<string>("");
  const [models, setModels] = useState<Set<string>>(new Set());
  const [launching, setLaunching] = useState(false);

  useEffect(() => {
    api.listDatasets().then(setDatasets).catch(console.error);
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
    if (!selected || models.size === 0) return;
    setLaunching(true);
    try {
      const modelConfigs = Array.from(models).map((key) => {
        const m = AVAILABLE_MODELS.find(
          (am) => `${am.provider}/${am.model_name}` === key
        )!;
        return { provider: m.provider, model_name: m.model_name, api_key_env: m.api_key_env };
      });
      const resp = await api.createRun({
        dataset_id: selected,
        models: modelConfigs,
        mode: "debate",
      });
      if (resp.run_id && resp.run_id !== "starting") {
        router.push(`/run/${resp.run_id}`);
      }
    } catch (err) {
      console.error(err);
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
            onClick={() => setSelected(ds.id)}
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

      {/* Model selector */}
      {selected && (
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
        </div>
      )}
    </div>
  );
}
