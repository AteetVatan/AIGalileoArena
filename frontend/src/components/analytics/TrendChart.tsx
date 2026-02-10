"use client";

import { useMemo } from "react";
import {
    AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
    Legend, CartesianGrid,
} from "recharts";
import type { ModelTrendSeries } from "@/lib/galileoTypes";

const PALETTE = [
    "#22d3ee", "#fb7185", "#c084fc", "#4ade80", "#fbbf24",
    "#60a5fa", "#f472b6", "#2dd4bf", "#fb923c", "#a78bfa",
];

interface TrendChartProps {
    series: ModelTrendSeries[];
    modelNames: Map<string, string>;
}

export default function TrendChart({ series, modelNames }: TrendChartProps) {
    const chartData = useMemo(() => {
        const bucketMap = new Map<string, Record<string, number | string>>();

        for (const s of series) {
            for (const b of s.buckets) {
                const key = b.bucket.slice(0, 10);
                const existing = bucketMap.get(key) ?? { date: key };
                if (b.score_avg !== null) {
                    existing[s.llm_id] = Math.round(b.score_avg * 100) / 100;
                }
                bucketMap.set(key, existing);
            }
        }

        return Array.from(bucketMap.values()).sort(
            (a, b) => String(a.date).localeCompare(String(b.date)),
        );
    }, [series]);

    if (!chartData.length) {
        return (
            <div className="flex items-center justify-center h-64 text-gray-500">
                No trend data available
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height={320}>
            <AreaChart data={chartData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                <defs>
                    {series.map((s, i) => (
                        <linearGradient key={s.llm_id} id={`trend-grad-${i}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0.3} />
                            <stop offset="95%" stopColor={PALETTE[i % PALETTE.length]} stopOpacity={0} />
                        </linearGradient>
                    ))}
                </defs>
                <CartesianGrid strokeDasharray="3 6" stroke="#1e293b" />
                <XAxis dataKey="date" stroke="#334155" fontSize={11} tickLine={false} />
                <YAxis stroke="#334155" fontSize={11} tickLine={false} axisLine={false} />
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
                <Legend
                    wrapperStyle={{ fontSize: "11px", paddingTop: "8px" }}
                />
                {series.map((s, i) => (
                    <Area
                        key={s.llm_id}
                        type="monotone"
                        dataKey={s.llm_id}
                        name={modelNames.get(s.llm_id) ?? s.llm_id.slice(0, 8)}
                        stroke={PALETTE[i % PALETTE.length]}
                        strokeWidth={2.5}
                        fill={`url(#trend-grad-${i})`}
                        dot={false}
                        activeDot={{
                            r: 5,
                            strokeWidth: 2,
                            stroke: PALETTE[i % PALETTE.length],
                            fill: "#0f172a",
                            style: { filter: `drop-shadow(0 0 6px ${PALETTE[i % PALETTE.length]})` },
                        }}
                        connectNulls={false}
                    />
                ))}
            </AreaChart>
        </ResponsiveContainer>
    );
}
