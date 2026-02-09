"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { api } from "@/lib/api";
import { AVAILABLE_MODELS } from "@/lib/constants";
import CopernicanSystem from "@/components/CopernicanSystem";
import type {
    Dataset,
    DatasetCase,
    KeyValidationResult,
    KeyValidationStatus,
} from "@/lib/types";

export default function DatasetsPage() {
    const [datasets, setDatasets] = useState<Dataset[]>([]);
    const [selected, setSelected] = useState<string>("");
    const [cases, setCases] = useState<DatasetCase[]>([]);
    const [casesLoading, setCasesLoading] = useState(false);
    const [selectedCaseId, setSelectedCaseId] = useState<string>("");
    const [selectedModel, setSelectedModel] = useState<string>("");
    const [launching, setLaunching] = useState(false);
    const [error, setError] = useState<string>("");
    const [availableKeys, setAvailableKeys] = useState<Set<string> | null>(null);
    const [keyValidation, setKeyValidation] = useState<
        Map<string, KeyValidationResult>
    >(new Map());
    const [validationLoading, setValidationLoading] = useState(false);
    const [validationError, setValidationError] = useState<string | null>(null);
    const [highlightCaseSelector, setHighlightCaseSelector] = useState(false);
    const [highlightModelSelector, setHighlightModelSelector] = useState(false);
    const selectRef = useRef<HTMLSelectElement>(null);
    const modelSelectorRef = useRef<HTMLDivElement>(null);
    const caseSelectorRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        api.listDatasets().then(setDatasets).catch(console.error);

        api
            .getAvailableKeys()
            .then((response) => {
                setAvailableKeys(new Set(response.available_keys));
            })
            .catch((err) => {
                console.error("Failed to fetch available keys:", err);
                setAvailableKeys(new Set());
            });
    }, []);

    const handleRefreshValidation = useCallback(async () => {
        setValidationLoading(true);
        setValidationError(null);
        try {
            const results = await api.validateKeys(true);
            setKeyValidation(new Map(Object.entries(results)));
        } catch (err) {
            console.error("Failed to refresh validation:", err);
            setValidationError("Failed to refresh key status");
        } finally {
            setValidationLoading(false);
        }
    }, []);

    const handleSelectDataset = useCallback((dsId: string) => {
        setSelected(dsId);
        setSelectedCaseId("");
        setSelectedModel("");
        setCases([]);
        setCasesLoading(true);
        setHighlightCaseSelector(false);
        setHighlightModelSelector(false);
        api
            .getDataset(dsId)
            .then((detail) => setCases(detail.cases))
            .catch(console.error)
            .finally(() => setCasesLoading(false));
    }, []);

    const isModelAvailable = useCallback(
        (model: (typeof AVAILABLE_MODELS)[0]) => {
            if (availableKeys === null) return true;
            return availableKeys.has(model.api_key_env);
        },
        [availableKeys]
    );

    const getValidationStatus = useCallback(
        (model: (typeof AVAILABLE_MODELS)[0]): KeyValidationStatus | null => {
            const validation = keyValidation.get(model.api_key_env);
            return validation?.status || null;
        },
        [keyValidation]
    );

    const isModelDisabled = useCallback(
        (model: (typeof AVAILABLE_MODELS)[0]): boolean => {
            if (!isModelAvailable(model)) return true;
            const status = getValidationStatus(model);
            return (
                status === "INVALID_KEY" || status === "NO_FUNDS_OR_BUDGET"
            );
        },
        [isModelAvailable, getValidationStatus]
    );

    const getStatusBadge = useCallback(
        (status: KeyValidationStatus | null): { icon: string; tooltip: string; color: string } => {
            switch (status) {
                case "VALID": return { icon: "✅", tooltip: "API key is valid", color: "text-green-400" };
                case "INVALID_KEY": return { icon: "❌", tooltip: "API key is invalid or revoked", color: "text-red-400" };
                case "NO_FUNDS_OR_BUDGET": return { icon: "💰", tooltip: "Account has no credits", color: "text-yellow-400" };
                case "RATE_LIMIT": return { icon: "⏱️", tooltip: "Rate limited", color: "text-yellow-400" };
                case "PERMISSION_OR_REGION": return { icon: "🚫", tooltip: "Access restricted", color: "text-orange-400" };
                case "PROVIDER_OUTAGE": return { icon: "⚠️", tooltip: "Provider outage", color: "text-gray-400" };
                case "TIMEOUT": return { icon: "⏳", tooltip: "Validation timed out", color: "text-gray-400" };
                case "UNKNOWN_ERROR": return { icon: "❓", tooltip: "Unknown status", color: "text-gray-400" };
                default: return { icon: "", tooltip: "", color: "" };
            }
        },
        []
    );

    useEffect(() => {
        if (selectedModel && availableKeys) {
            const model = AVAILABLE_MODELS.find(
                (m) => `${m.provider}/${m.model_name}` === selectedModel
            );
            if (model && !availableKeys.has(model.api_key_env)) {
                setSelectedModel("");
            }
        }
    }, [availableKeys, selectedModel]);

    // Scroll to and highlight Target Case when dataset is selected and cases are loaded
    useEffect(() => {
        if (selected && caseSelectorRef.current && !casesLoading && cases.length > 0) {
            setTimeout(() => {
                caseSelectorRef.current?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
                setHighlightCaseSelector(true);
                setTimeout(() => setHighlightCaseSelector(false), 3000);
            }, 300);
        }
    }, [selected, casesLoading, cases.length]);

    // Scroll to and highlight Inference Engine when case is selected
    useEffect(() => {
        if (selectedCaseId && modelSelectorRef.current) {
            setTimeout(() => {
                modelSelectorRef.current?.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center',
                    inline: 'nearest'
                });
                setHighlightModelSelector(true);
                selectRef.current?.focus();
                setTimeout(() => setHighlightModelSelector(false), 3000);
            }, 300);
        }
    }, [selectedCaseId]);

    const handleLaunch = async () => {
        if (!selected || !selectedCaseId || !selectedModel) return;
        setLaunching(true);
        setError("");
        try {
            const m = AVAILABLE_MODELS.find(
                (am) => `${am.provider}/${am.model_name}` === selectedModel
            )!;
            const modelConfigs = [
                { provider: m.provider, model_name: m.model_name, api_key_env: m.api_key_env },
            ];
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
        <div className="relative min-h-screen w-full overflow-hidden flex flex-col items-center justify-start lg:justify-center p-8 pt-20 sm:pt-8">
            {/* Background System */}
            <CopernicanSystem />

            {/* Main Content Container */}
            <div className="relative z-10 w-full max-w-6xl grid grid-cols-1 lg:grid-cols-12 gap-8 items-start">

                {/* Header / Intro - Left Side */}
                <div className="lg:col-span-4 flex flex-col justify-center space-y-6 lg:sticky lg:top-24">
                    <h1 className="text-4xl sm:text-5xl lg:text-6xl text-white font-great-vibes leading-tight bg-gradient-to-r from-cyan-200 via-indigo-200 to-white bg-clip-text text-transparent drop-shadow-[0_0_15px_rgba(34,211,238,0.3)]" style={{ fontFamily: 'var(--font-great-vibes)' }}>
                        Systema <span className="hidden sm:inline"><br /></span>Cosmicum
                    </h1>
                    <p className="text-lg text-slate-300 font-light leading-relaxed backdrop-blur-sm bg-slate-900/30 p-4 rounded-xl border border-white/5">
                        Select a dataset to begin the evaluation orbit. Each case revolves around a central premise, tested by the gravitational pull of agentic debate.
                    </p>

                    {/* Case Selector - Relocated */}
                    {/* Case Selector - With Auto-Scroll and Highlight */}
                    {selected && (
                        <div
                            ref={caseSelectorRef}
                            className={`glass-card p-6 backdrop-blur-xl rounded-xl space-y-3 animate-in fade-in slide-in-from-left-4 duration-700 transition-all ${highlightCaseSelector
                                ? 'border-cyan-400/60 bg-cyan-500/10 shadow-[0_0_30px_rgba(34,211,238,0.4)] ring-2 ring-cyan-400/30'
                                : 'border-primary/20 bg-background/30'
                                }`}
                        >
                            <label className="text-xs font-semibold text-muted-foreground uppercase tracking-widest pl-1">Target Case</label>
                            {casesLoading ? (
                                <div className="h-12 w-full rounded-xl bg-muted/20 animate-pulse" />
                            ) : (
                                <div className="relative">
                                    <select
                                        value={selectedCaseId}
                                        onChange={(e) => setSelectedCaseId(e.target.value)}
                                        className="w-full appearance-none bg-background/50 border border-primary/20 rounded-xl px-5 py-4 text-foreground placeholder-muted-foreground focus:outline-none focus:border-primary/50 focus:ring-1 focus:ring-primary/20 transition-all"
                                    >
                                        <option value="" className="bg-background">-- Select a specific case --</option>
                                        {cases.map((c) => (
                                            <option key={c.case_id} value={c.case_id} className="bg-background">
                                                {c.topic}
                                            </option>
                                        ))}
                                    </select>
                                    <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-muted-foreground">▼</div>
                                </div>
                            )}
                        </div>
                    )}
                </div>

                {/* Interactive Panel - Right Side */}
                <div className="lg:col-span-8 flex flex-col gap-6">

                    {/* Dataset Selection - Horizontal Scroll or Grid */}
                    <div className="glass-panel border-white/10 bg-slate-950/40 backdrop-blur-md rounded-3xl p-6 shadow-2xl">
                        <h2 className="text-xs font-semibold text-cyan-400 mb-4 tracking-widest uppercase">Available Datasets</h2>
                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {datasets.map((ds) => (
                                <button
                                    key={ds.id}
                                    onClick={() => handleSelectDataset(ds.id)}
                                    className={`group relative overflow-hidden rounded-2xl p-5 text-left transition-all duration-300 border ${selected === ds.id
                                        ? "bg-cyan-500/10 border-cyan-500/50 shadow-[0_0_20px_rgba(6,182,212,0.15)] ring-1 ring-cyan-500/30"
                                        : "bg-white/5 border-white/5 hover:bg-white/10 hover:border-white/10"
                                        }`}
                                >
                                    <div className="absolute inset-0 bg-gradient-to-br from-cyan-500/0 via-cyan-500/0 to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                    <h3 className={`text-lg font-medium transition-colors ${selected === ds.id ? "text-cyan-200" : "text-white"}`}>{ds.id}</h3>
                                    <p className="text-sm text-slate-400 mt-2 line-clamp-2 leading-relaxed">{ds.description}</p>
                                    <div className="flex items-center gap-2 mt-4 text-xs text-white/30">
                                        <span className="px-2 py-1 rounded-full bg-white/5">{ds.case_count} orbits</span>
                                        <span>v{ds.version}</span>
                                    </div>
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Model Configuration */}
                    {(selected && selectedCaseId) && (
                        <div className="glass-panel border-white/10 bg-slate-950/60 backdrop-blur-xl rounded-3xl p-8 shadow-2xl animate-in fade-in slide-in-from-bottom-4 duration-700">



                            {/* Model Selector */}
                            {selected && selectedCaseId && (
                                <div
                                    ref={modelSelectorRef}
                                    className={`space-y-6 p-6 -m-6 rounded-2xl transition-all duration-500 ${highlightModelSelector
                                        ? 'bg-gradient-to-br from-cyan-500/10 via-indigo-500/10 to-cyan-500/5 shadow-[inset_0_0_40px_rgba(34,211,238,0.2)] border-2 border-cyan-400/40'
                                        : 'bg-transparent border-2 border-transparent'
                                        }`}
                                >
                                    <div className="flex items-center justify-between">
                                        <label className="text-xs font-semibold text-cyan-400 uppercase tracking-widest pl-1">Inference Engine</label>
                                        <button
                                            onClick={handleRefreshValidation}
                                            disabled={validationLoading}
                                            className="text-xs text-cyan-400 hover:text-cyan-300 transition flex items-center gap-1"
                                        >
                                            {validationLoading ? "Aligning..." : "Verify Connection"}
                                        </button>
                                    </div>

                                    <div className="relative">
                                        <select
                                            ref={selectRef}
                                            value={selectedModel}
                                            onChange={(e) => {
                                                const value = e.target.value;
                                                if (!value) {
                                                    setSelectedModel("");
                                                    setError("");
                                                    return;
                                                }
                                                const model = AVAILABLE_MODELS.find(
                                                    (m) => `${m.provider}/${m.model_name}` === value
                                                );
                                                if (model && (!isModelAvailable(model) || isModelDisabled(model))) {
                                                    if (selectRef.current) selectRef.current.value = selectedModel || "";
                                                    return;
                                                }
                                                setSelectedModel(value);
                                                setError("");
                                            }}
                                            className="w-full appearance-none bg-white/5 border border-white/10 rounded-xl px-5 py-4 text-white focus:outline-none focus:border-cyan-500/50 focus:ring-1 focus:ring-cyan-500/20 transition-all"
                                        >
                                            <option value="" className="bg-slate-950">-- Select Intelligence Model --</option>
                                            {AVAILABLE_MODELS.map((m) => {
                                                const key = `${m.provider}/${m.model_name}`;
                                                const isAvailable = isModelAvailable(m);
                                                const isDisabled = isModelDisabled(m);
                                                const status = getValidationStatus(m);
                                                const badge = getStatusBadge(status);

                                                return (
                                                    <option
                                                        key={key}
                                                        value={key}
                                                        disabled={!isAvailable || isDisabled}
                                                        className="bg-slate-950"
                                                    >
                                                        {badge.icon} {m.label}
                                                        {!isAvailable ? " (Key Missing)" : isDisabled ? " (Unavailable)" : ""}
                                                    </option>
                                                );
                                            })}
                                        </select>
                                        <div className="absolute right-4 top-1/2 -translate-y-1/2 pointer-events-none text-white/30">▼</div>
                                    </div>

                                    {/* Launch Button */}
                                    <div className="pt-4 flex flex-col gap-4">
                                        <button
                                            onClick={handleLaunch}
                                            disabled={launching || !selectedModel}
                                            className="group relative w-full h-14 overflow-hidden rounded-xl bg-gradient-to-r from-indigo-500 to-cyan-500 disabled:from-slate-800 disabled:to-slate-900 transition-all duration-300 shadow-lg hover:shadow-cyan-500/25"
                                        >
                                            <div className="absolute inset-0 bg-white/20 group-hover:translate-x-full transition-transform duration-700 ease-out skew-x-12 -translate-x-[150%]" />
                                            <span className="relative flex items-center justify-center gap-2 font-medium text-lg tracking-wide text-white">
                                                {launching ? (
                                                    <>Igniting Sequence...</>
                                                ) : (
                                                    <>Commence Debate</>
                                                )}
                                            </span>
                                        </button>
                                        {error && <p className="text-center text-sm text-red-400 bg-red-950/30 py-2 rounded-lg border border-red-500/20">{error}</p>}
                                    </div>
                                </div>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
