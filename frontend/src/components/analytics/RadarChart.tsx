"use client";

import { useMemo } from "react";
import {
    Radar, RadarChart as RechartsRadarChart, PolarGrid,
    PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer, Legend, Tooltip,
} from "recharts";
import type { RadarEntry } from "@/lib/galileoTypes";

const PALETTE = [
    "#22d3ee", "#fb7185", "#c084fc", "#4ade80", "#fbbf24",
    "#60a5fa", "#f472b6", "#2dd4bf", "#fb923c", "#a78bfa",
];

const DIMENSION_LABELS: Record<string, string> = {
    correctness: "Correctness",
    grounding: "Grounding",
    calibration: "Calibration",
    falsifiable: "Falsifiable",
    deference_penalty: "Deference",
    refusal_penalty: "Refusal",
};

interface RadarChartProps {
    entries: RadarEntry[];
    modelNames: Map<string, string>;
}

export default function RadarChart({ entries, modelNames }: RadarChartProps) {
    const { chartData, llmIds } = useMemo(() => {
        const byDimension = new Map<string, Record<string, number | string>>();
        const ids = new Set<string>();

        for (const e of entries) {
            ids.add(e.llm_id);
            const existing = byDimension.get(e.dimension) ?? {
                dimension: DIMENSION_LABELS[e.dimension] ?? e.dimension,
            };
            if (e.avg_value !== null) {
                existing[e.llm_id] = Math.round(e.avg_value * 100) / 100;
            }
            byDimension.set(e.dimension, existing);
        }

        return {
            chartData: Array.from(byDimension.values()),
            llmIds: Array.from(ids),
        };
    }, [entries]);

    if (!chartData.length) {
        return (
            <div className="flex items-center justify-center h-64 text-gray-500">
                No radar data available
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height={360}>
            <RechartsRadarChart cx="50%" cy="50%" outerRadius="75%" data={chartData}>
                <PolarGrid stroke="#1e293b" strokeDasharray="3 3" />
                <PolarAngleAxis
                    dataKey="dimension"
                    stroke="#64748b"
                    fontSize={11}
                    tickLine={false}
                />
                <PolarRadiusAxis stroke="#1e293b" fontSize={10} axisLine={false} />
                <Tooltip
                    contentStyle={{
                        backgroundColor: "rgba(15, 23, 42, 0.85)",
                        backdropFilter: "blur(12px)",
                        WebkitBackdropFilter: "blur(12px)",
                        border: "1px solid rgba(34, 211, 238, 0.15)",
                        borderLeft: "3px solid rgba(34, 211, 238, 0.6)",
                        borderRadius: "12px",
                        color: "#e2e8f0",
                        boxShadow: "0 8px 32px rgba(0,0,0,0.4)",
                    }}
                />
                <Legend wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }} />
                {llmIds.map((id, i) => (
                    <Radar
                        key={id}
                        name={modelNames.get(id) ?? id.slice(0, 8)}
                        dataKey={id}
                        stroke={PALETTE[i % PALETTE.length]}
                        strokeWidth={2}
                        fill={PALETTE[i % PALETTE.length]}
                        fillOpacity={0.12}
                        style={{ filter: `drop-shadow(0 0 4px ${PALETTE[i % PALETTE.length]}40)` }}
                    />
                ))}
            </RechartsRadarChart>
        </ResponsiveContainer>
    );
}
