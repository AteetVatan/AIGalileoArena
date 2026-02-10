"use client";

import { useMemo, Suspense, lazy } from "react";
import {
    useModelsSummary, useModelsTrend, useDistribution,
    useScoreBreakdown, useRadar,
} from "@/lib/galileoQueries";
import type { GalileoQueryParams } from "@/lib/galileoApi";

const TrendChart = lazy(() => import("@/components/analytics/TrendChart"));
const DistributionChart = lazy(() => import("@/components/analytics/DistributionChart"));
const ScoreBreakdownChart = lazy(() => import("@/components/analytics/ScoreBreakdownChart"));
const RadarChart = lazy(() => import("@/components/analytics/RadarChart"));

const PARAMS: GalileoQueryParams = { window: 30, includeScheduled: true };

function Spinner() {
    return (
        <div className="flex items-center justify-center h-48">
            <div className="relative w-8 h-8">
                <div className="absolute inset-0 rounded-full border-2 border-transparent border-t-cyan-400 animate-spin" />
                <div className="absolute inset-1 rounded-full border-2 border-transparent border-b-purple-500 animate-spin" style={{ animationDirection: "reverse", animationDuration: "0.6s" }} />
            </div>
        </div>
    );
}

interface MiniCardProps {
    title: string;
    children: React.ReactNode;
}

function MiniCard({ title, children }: MiniCardProps) {
    return (
        <div className="relative group rounded-2xl p-px overflow-hidden">
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-transparent to-purple-500/20 opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="relative bg-slate-900/70 backdrop-blur-xl rounded-2xl p-4 shadow-[inset_0_1px_0_rgba(255,255,255,0.06)]">
                <h3 className="text-[10px] font-semibold text-cyan-400/80 uppercase tracking-[0.15em] mb-3 flex items-center gap-1.5">
                    <span className="w-1 h-1 rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.6)]" />
                    {title}
                </h3>
                {children}
            </div>
        </div>
    );
}

export default function StartDashboard() {
    const { data: summaryData } = useModelsSummary(PARAMS);
    const { data: trendData } = useModelsTrend(PARAMS);
    const { data: distData } = useDistribution(PARAMS);
    const { data: breakdownData } = useScoreBreakdown(PARAMS);
    const { data: radarData } = useRadar(PARAMS);

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
        <div className="grid grid-cols-2 gap-3">
            <MiniCard title="Score Trend">
                <Suspense fallback={<Spinner />}>
                    {trendData?.series?.length ? (
                        <TrendChart series={trendData.series} modelNames={modelNames} />
                    ) : (
                        <Spinner />
                    )}
                </Suspense>
            </MiniCard>

            <MiniCard title="Distribution">
                <Suspense fallback={<Spinner />}>
                    {distData?.items?.length ? (
                        <DistributionChart items={distData.items} modelNames={modelNames} />
                    ) : (
                        <Spinner />
                    )}
                </Suspense>
            </MiniCard>

            <MiniCard title="Breakdown">
                <Suspense fallback={<Spinner />}>
                    {breakdownData?.items?.length ? (
                        <ScoreBreakdownChart items={breakdownData.items} modelNames={modelNames} />
                    ) : (
                        <Spinner />
                    )}
                </Suspense>
            </MiniCard>

            <MiniCard title="Radar">
                <Suspense fallback={<Spinner />}>
                    {radarData?.entries?.length ? (
                        <RadarChart entries={radarData.entries} modelNames={modelNames} />
                    ) : (
                        <Spinner />
                    )}
                </Suspense>
            </MiniCard>
        </div>
    );
}
