"use client";

import { useState, useMemo, Suspense, lazy } from "react";
import {
    useModelsSummary, useModelsTrend, useDistribution,
    useUplift, useFailures, usePareto,
    useScoreBreakdown, useRadar, useHeatmap,
    useHallucinationTrend, useCalibrationScatter, useCostPerPass,
} from "@/lib/galileoQueries";
import { useDatasets } from "@/lib/queries";
import type { GalileoQueryParams } from "@/lib/galileoApi";
import ModelsTable from "@/components/analytics/ModelsTable";

const TrendChart = lazy(() => import("@/components/analytics/TrendChart"));
const DistributionChart = lazy(() => import("@/components/analytics/DistributionChart"));
const ScoreBreakdownChart = lazy(() => import("@/components/analytics/ScoreBreakdownChart"));
const RadarChart = lazy(() => import("@/components/analytics/RadarChart"));
const HeatmapChart = lazy(() => import("@/components/analytics/HeatmapChart"));
const HallucinationTrendChart = lazy(() => import("@/components/analytics/HallucinationTrendChart"));
const CalibrationScatter = lazy(() => import("@/components/analytics/CalibrationScatter"));
const CostPerPassChart = lazy(() => import("@/components/analytics/CostPerPassChart"));


const TAB_PERFORMANCE = "performance";
const TAB_ROBUSTNESS = "robustness";
const TAB_EFFECTIVENESS = "effectiveness";
const TAB_OPS = "ops";

interface TabDef {
    id: string;
    label: string;
    icon: string;
}

const TABS: TabDef[] = [
    { id: TAB_PERFORMANCE, label: "Performance", icon: "📊" },
    { id: TAB_ROBUSTNESS, label: "Robustness", icon: "🛡️" },
    // { id: TAB_EFFECTIVENESS, label: "Galileo Effect", icon: "🔬" },  // TODO: re-enable when baseline mode is implemented
    { id: TAB_OPS, label: "Operations", icon: "⚙️" },
];

const WINDOW_OPTIONS = [7, 14, 30, 90] as const;

function ChartLoader() {
    return (
        <div className="flex items-center justify-center h-64">
            <div className="relative w-10 h-10">
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-cyan-400 animate-spin" />
                <div className="absolute inset-1 rounded-full border-2 border-transparent border-b-purple-500 animate-spin" style={{ animationDirection: "reverse", animationDuration: "0.6s" }} />
            </div>
        </div>
    );
}

interface CardProps {
    title: string;
    children: React.ReactNode;
}

function Card({ title, children }: CardProps) {
    return (
        <div className="relative group rounded-2xl p-px overflow-hidden">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-transparent to-purple-500/20 opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative bg-slate-900/80 backdrop-blur-xl rounded-2xl p-5 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                <h3 className="text-xs font-semibold text-cyan-400/80 uppercase tracking-[0.15em] mb-4 flex items-center gap-2">
                    <span className="w-1.5 h-1.5 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.6)]" />
                    {title}
                </h3>
                {children}
            </div>
        </div>
    );
}

export default function GraphsPage() {
    const [activeTab, setActiveTab] = useState(TAB_PERFORMANCE);
    const [window, setWindow] = useState<number>(30);

    const params: GalileoQueryParams = useMemo(
        () => ({ window, includeScheduled: true }),
        [window],
    );

    const { data: summaryData, isLoading: summaryLoading } = useModelsSummary(params);
    const { data: trendData, isLoading: trendLoading } = useModelsTrend(params);

    const modelNames = useMemo(() => {
        const map = new Map<string, string>();
        if (summaryData?.models) {
            for (const m of summaryData.models) {
                map.set(m.llm_id, m.display_name);
            }
        }
        return map;
    }, [summaryData]);

    return (
        <div className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white pt-16">
            <div className="max-w-7xl mx-auto px-4 pt-4 pb-2 flex items-center justify-end gap-3">
                <select
                    value={window}
                    onChange={(e) => setWindow(Number(e.target.value))}
                    className="bg-slate-800/60 border border-cyan-500/20 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 shadow-[0_0_8px_rgba(6,182,212,0.1)] transition-shadow hover:shadow-[0_0_12px_rgba(6,182,212,0.2)]"
                >
                    {WINDOW_OPTIONS.map((w) => (
                        <option key={w} value={w}>{w}d window</option>
                    ))}
                </select>
            </div>

            <div className="max-w-7xl mx-auto px-4 py-6">
                <div className="flex gap-1 mb-6 bg-slate-800/40 backdrop-blur-sm rounded-2xl p-1 w-fit border border-white/5">
                    {TABS.map((tab) => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`px-5 py-2.5 rounded-xl text-sm font-medium transition-all duration-300 ${activeTab === tab.id
                                ? "bg-gradient-to-r from-cyan-500/25 to-purple-500/25 text-cyan-200 shadow-[0_0_20px_rgba(6,182,212,0.15)] border border-cyan-500/20"
                                : "text-gray-500 hover:text-gray-300 hover:bg-white/5"
                                }`}
                        >
                            {tab.icon} {tab.label}
                        </button>
                    ))}
                </div>

                <Suspense fallback={<ChartLoader />}>
                    {activeTab === TAB_PERFORMANCE && (
                        <PerformanceTab params={params} modelNames={modelNames} summaryData={summaryData} trendData={trendData} />
                    )}
                    {activeTab === TAB_ROBUSTNESS && (
                        <RobustnessTab params={params} modelNames={modelNames} />
                    )}
                    {/* TODO: re-enable when baseline mode is implemented
                    {activeTab === TAB_EFFECTIVENESS && (
                        <EffectivenessTab params={params} modelNames={modelNames} />
                    )}
                    */}
                    {activeTab === TAB_OPS && (
                        <OpsTab params={params} modelNames={modelNames} />
                    )}
                </Suspense>
            </div>
        </div>
    );
}

interface TabProps {
    params: GalileoQueryParams;
    modelNames: Map<string, string>;
}

interface PerformanceTabProps extends TabProps {
    summaryData: ReturnType<typeof useModelsSummary>["data"];
    trendData: ReturnType<typeof useModelsTrend>["data"];
}

function PerformanceTab({ params, modelNames, summaryData, trendData }: PerformanceTabProps) {
    const { data: distData } = useDistribution(params);
    const { data: breakdownData } = useScoreBreakdown(params);
    const { data: radarData } = useRadar(params);

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Score Trend">
                    {trendData?.series?.length ? (
                        <TrendChart series={trendData.series} modelNames={modelNames} />
                    ) : (
                        <ChartLoader />
                    )}
                </Card>
                <Card title="Score Distribution">
                    {distData?.items?.length ? (
                        <DistributionChart items={distData.items} modelNames={modelNames} />
                    ) : (
                        <ChartLoader />
                    )}
                </Card>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Score Breakdown">
                    {breakdownData?.items?.length ? (
                        <ScoreBreakdownChart items={breakdownData.items} modelNames={modelNames} />
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No breakdown data</div>
                    )}
                </Card>
                <Card title="Radar / Spider">
                    {radarData?.entries?.length ? (
                        <RadarChart entries={radarData.entries} modelNames={modelNames} />
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No radar data</div>
                    )}
                </Card>
            </div>
            <Card title="All Models">
                {summaryData?.models ? (
                    <ModelsTable models={summaryData.models} windowDays={params.window ?? 30} />
                ) : (
                    <ChartLoader />
                )}
            </Card>
        </div>
    );
}

function RobustnessTab({ params, modelNames }: TabProps) {
    const { data: distData } = useDistribution(params);
    const { data: failData } = useFailures(params);
    const { data: hallucinationData } = useHallucinationTrend(params);
    const { data: calibrationData } = useCalibrationScatter(params);
    const { data: datasets } = useDatasets();
    const [heatmapDatasetId, setHeatmapDatasetId] = useState<string | null>(null);
    const activeDatasetId = heatmapDatasetId ?? datasets?.[0]?.id ?? null;
    const { data: heatmapData } = useHeatmap(activeDatasetId, params);

    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Score Stability (σ)">
                    {distData?.items?.length ? (
                        <div className="space-y-3">
                            {distData.items
                                .filter((d) => d.stddev !== null)
                                .sort((a, b) => (a.stddev ?? 0) - (b.stddev ?? 0))
                                .map((d, i) => (
                                    <div key={d.llm_id} className="flex items-center gap-3 group/row">
                                        <span className="text-xs font-mono text-cyan-500/60 w-5">{i + 1}</span>
                                        <span className="text-sm text-gray-300 w-32 truncate group-hover/row:text-white transition-colors">
                                            {modelNames.get(d.llm_id) ?? d.llm_id.slice(0, 8)}
                                        </span>
                                        <div className="flex-1 bg-slate-800/60 rounded-full h-2.5 overflow-hidden">
                                            <div
                                                className="h-full bg-gradient-to-r from-emerald-400 via-cyan-400 to-amber-400 rounded-full transition-all shadow-[0_0_8px_rgba(34,211,238,0.3)]"
                                                style={{ width: `${Math.min((d.stddev ?? 0) * 20, 100)}%` }}
                                            />
                                        </div>
                                        <span className="text-xs text-gray-500 font-mono w-12 text-right">
                                            {d.stddev?.toFixed(2) ?? "—"}
                                        </span>
                                    </div>
                                ))}
                        </div>
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No stability data</div>
                    )}
                </Card>
                <Card title="Failure Breakdown">
                    {failData?.items?.length ? (
                        <div className="space-y-2.5">
                            {failData.items.map((f) => (
                                <div key={`${f.llm_id}-${f.failure_type}`} className="flex items-center gap-3 group/fail hover:bg-white/[0.03] rounded-lg px-2 py-1.5 -mx-2 transition-colors">
                                    <span className="text-sm text-gray-300 w-36 truncate group-hover/fail:text-white transition-colors">
                                        {modelNames.get(f.llm_id) ?? f.llm_id.slice(0, 8)}
                                    </span>
                                    <span className="text-[10px] px-2.5 py-0.5 bg-gradient-to-r from-rose-500/20 to-rose-500/10 text-rose-400 rounded-full border border-rose-500/20 shadow-[0_0_6px_rgba(244,63,94,0.15)]">
                                        {f.failure_type}
                                    </span>
                                    <span className="text-xs text-gray-500 font-mono ml-auto tabular-nums">{f.count}×</span>
                                </div>
                            ))}
                        </div>
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No failures recorded 🎉</div>
                    )}
                </Card>
            </div>
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Hallucination Rate Trend">
                    {hallucinationData?.series?.length ? (
                        <HallucinationTrendChart series={hallucinationData.series} modelNames={modelNames} />
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No hallucination data</div>
                    )}
                </Card>
                <Card title="Confidence vs Correctness">
                    {calibrationData?.points?.length ? (
                        <CalibrationScatter points={calibrationData.points} modelNames={modelNames} />
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No calibration data</div>
                    )}
                </Card>
            </div>
            <Card title="Case Pass/Fail Heatmap">
                <div className="flex items-center gap-3 mb-4">
                    <label className="text-xs text-gray-500 uppercase tracking-wider">Dataset</label>
                    <select
                        value={activeDatasetId ?? ""}
                        onChange={(e) => setHeatmapDatasetId(e.target.value || null)}
                        className="bg-slate-800/60 border border-cyan-500/20 rounded-lg px-3 py-1.5 text-sm text-gray-300 focus:outline-none focus:ring-2 focus:ring-cyan-500/40 shadow-[0_0_8px_rgba(6,182,212,0.1)]"
                    >
                        {datasets?.map((ds) => (
                            <option key={ds.id} value={ds.id}>{ds.id}</option>
                        ))}
                    </select>
                </div>
                {heatmapData?.cells?.length ? (
                    <HeatmapChart cells={heatmapData.cells} modelNames={modelNames} />
                ) : (
                    <div className="text-gray-500 h-32 flex items-center justify-center">
                        {activeDatasetId ? "No heatmap data for this dataset" : "No datasets available"}
                    </div>
                )}
            </Card>
        </div>
    );
}

function EffectivenessTab({ params, modelNames }: TabProps) {
    const { data: upliftData } = useUplift(params);

    return (
        <div className="space-y-6">
            <Card title="Galileo Effect (Uplift)">
                {upliftData?.items?.length ? (
                    <div className="space-y-4">
                        {upliftData.items
                            .sort((a, b) => (b.delta ?? 0) - (a.delta ?? 0))
                            .map((u) => (
                                <div key={u.llm_id} className="flex items-center gap-4">
                                    <span className="text-sm text-gray-300 w-40 truncate">
                                        {modelNames.get(u.llm_id) ?? u.llm_id.slice(0, 8)}
                                    </span>
                                    <div className="flex-1 flex items-center gap-3">
                                        <span className="text-xs text-gray-500 font-mono">
                                            Baseline: {u.avg_baseline?.toFixed(2) ?? "—"}
                                        </span>
                                        <span className="text-lg">→</span>
                                        <span className="text-xs text-cyan-300 font-mono">
                                            Galileo: {u.avg_galileo?.toFixed(2) ?? "—"}
                                        </span>
                                        <span className={`text-sm font-bold ${(u.delta ?? 0) > 0 ? "text-emerald-400" : (u.delta ?? 0) < 0 ? "text-rose-400" : "text-gray-400"
                                            }`}>
                                            {u.delta !== null ? `${u.delta > 0 ? "+" : ""}${u.delta.toFixed(2)}` : "—"}
                                        </span>
                                    </div>
                                    <span className="text-xs text-gray-500">{u.n_pairs} pairs</span>
                                </div>
                            ))}
                    </div>
                ) : (
                    <div className="text-gray-500 h-32 flex items-center justify-center">
                        No uplift data — run baseline + galileo evaluations with shared batch_id
                    </div>
                )}
            </Card>
        </div>
    );
}

function OpsTab({ params, modelNames }: TabProps) {
    const { data: paretoData } = usePareto(params);
    const { data: costData } = useCostPerPass(params);


    return (
        <div className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <Card title="Score vs Latency (Pareto)">
                    {paretoData?.items?.length ? (
                        <div className="space-y-1">
                            {paretoData.items
                                .sort((a, b) => (b.avg_score ?? 0) - (a.avg_score ?? 0))
                                .map((p, i) => (
                                    <div key={p.llm_id} className="flex items-center gap-4 py-2.5 border-b border-white/[0.04] hover:bg-white/[0.03] rounded-lg px-2 -mx-2 transition-colors group/row">
                                        <span className="text-xs font-bold w-6 h-6 flex items-center justify-center rounded-md bg-gradient-to-br from-cyan-500/20 to-purple-500/20 text-cyan-400 border border-cyan-500/20">
                                            {i + 1}
                                        </span>
                                        <span className="text-sm text-gray-300 w-36 truncate group-hover/row:text-white transition-colors">
                                            {modelNames.get(p.llm_id) ?? p.llm_id.slice(0, 8)}
                                        </span>
                                        <div className="flex-1 grid grid-cols-3 gap-4 text-xs font-mono">
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-gray-600 uppercase tracking-wider">Score</span>
                                                <span className="text-cyan-300 drop-shadow-[0_0_4px_rgba(34,211,238,0.4)]">{p.avg_score?.toFixed(2) ?? "—"}</span>
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-gray-600 uppercase tracking-wider">Latency</span>
                                                <span className="text-amber-300 drop-shadow-[0_0_4px_rgba(245,158,11,0.4)]">
                                                    {p.avg_latency_ms ? `${Math.round(p.avg_latency_ms)}ms` : "—"}
                                                </span>
                                            </div>
                                            <div className="flex flex-col">
                                                <span className="text-[10px] text-gray-600 uppercase tracking-wider">Cost</span>
                                                <span className="text-emerald-300 drop-shadow-[0_0_4px_rgba(52,211,153,0.4)]">
                                                    {p.avg_cost_usd !== null ? `$${Number(p.avg_cost_usd).toFixed(4)}` : "—"}
                                                </span>
                                            </div>
                                        </div>
                                        <span className="text-[10px] text-gray-600 font-mono tabular-nums">{p.n} runs</span>
                                    </div>
                                ))}
                        </div>
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No operations data</div>
                    )}
                </Card>
                <Card title="Cost per Passing Answer">
                    {costData?.items?.length ? (
                        <CostPerPassChart items={costData.items} modelNames={modelNames} />
                    ) : (
                        <div className="text-gray-500 h-32 flex items-center justify-center">No cost data</div>
                    )}
                </Card>
            </div>

        </div>
    );
}
