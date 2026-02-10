"use client";

import { useMemo, Suspense, lazy } from "react";
import {
    useModelsSummary, useModelsTrend, useDistribution,
    useScoreBreakdown, useRadar,
} from "@/lib/galileoQueries";
import type { GalileoQueryParams } from "@/lib/galileoApi";
import { GlassCard } from "@/components/ui/GlassCard";
import { NeonSpinner } from "@/components/ui/NeonSpinner";

const TrendChart = lazy(() => import("@/components/analytics/TrendChart"));
const DistributionChart = lazy(() => import("@/components/analytics/DistributionChart"));
const ScoreBreakdownChart = lazy(() => import("@/components/analytics/ScoreBreakdownChart"));
const RadarChart = lazy(() => import("@/components/analytics/RadarChart"));

const PARAMS: GalileoQueryParams = { window: 30, includeScheduled: true };

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
        <div className="grid grid-cols-2 grid-rows-2 gap-3 h-full">
            <GlassCard title="Score Trend" size="sm">
                <Suspense fallback={<NeonSpinner />}>
                    {trendData?.series?.length ? (
                        <TrendChart series={trendData.series} modelNames={modelNames} />
                    ) : (
                        <NeonSpinner />
                    )}
                </Suspense>
            </GlassCard>

            <GlassCard title="Distribution" size="sm">
                <Suspense fallback={<NeonSpinner />}>
                    {distData?.items?.length ? (
                        <DistributionChart items={distData.items} modelNames={modelNames} />
                    ) : (
                        <NeonSpinner />
                    )}
                </Suspense>
            </GlassCard>

            <GlassCard title="Breakdown" size="sm">
                <Suspense fallback={<NeonSpinner />}>
                    {breakdownData?.items?.length ? (
                        <ScoreBreakdownChart items={breakdownData.items} modelNames={modelNames} />
                    ) : (
                        <NeonSpinner />
                    )}
                </Suspense>
            </GlassCard>

            <GlassCard title="Radar" size="sm">
                <Suspense fallback={<NeonSpinner />}>
                    {radarData?.entries?.length ? (
                        <RadarChart entries={radarData.entries} modelNames={modelNames} />
                    ) : (
                        <NeonSpinner />
                    )}
                </Suspense>
            </GlassCard>
        </div>
    );
}
