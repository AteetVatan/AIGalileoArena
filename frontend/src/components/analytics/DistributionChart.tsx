"use client";

import { useMemo } from "react";
import {
    BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer,
    ErrorBar, CartesianGrid, Cell,
} from "recharts";
import type { DistributionItem } from "@/lib/galileoTypes";

const BAR_COLORS = [
    "#22d3ee", "#60a5fa", "#c084fc", "#4ade80", "#fbbf24",
    "#fb7185", "#f472b6", "#2dd4bf", "#fb923c", "#a78bfa",
];

interface DistributionChartProps {
    items: DistributionItem[];
    modelNames: Map<string, string>;
}

export default function DistributionChart({ items, modelNames }: DistributionChartProps) {
    const chartData = useMemo(() => {
        return items
            .filter((d) => d.mean !== null)
            .map((d) => ({
                name: (modelNames.get(d.llm_id) ?? d.llm_id.slice(0, 8)).split("/").pop()!,
                mean: Math.round((d.mean ?? 0) * 100) / 100,
                p25: d.p25,
                p75: d.p75,
                spread: d.stddev ? Math.round(d.stddev * 100) / 100 : 0,
                n: d.n,
            }))
            .sort((a, b) => b.mean - a.mean);
    }, [items, modelNames]);

    if (!chartData.length) {
        return (
            <div className="flex items-center justify-center h-64 text-gray-500">
                No distribution data available
            </div>
        );
    }

    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={chartData} margin={{ top: 5, right: 20, bottom: 15, left: 0 }}>
                <defs>
                    {chartData.map((_, i) => (
                        <linearGradient key={i} id={`dist-bar-${i}`} x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor={BAR_COLORS[i % BAR_COLORS.length]} stopOpacity={0.9} />
                            <stop offset="100%" stopColor={BAR_COLORS[i % BAR_COLORS.length]} stopOpacity={0.3} />
                        </linearGradient>
                    ))}
                </defs>
                <CartesianGrid strokeDasharray="3 6" stroke="#1e293b" vertical={false} />
                <XAxis
                    dataKey="name"
                    stroke="#334155"
                    fontSize={11}
                    angle={-10}
                    textAnchor="end"
                    tickLine={false}
                />
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
                    formatter={(v: number, name: string) => {
                        if (name === "mean") return [`${v}`, "Mean Score"];
                        return [v, name];
                    }}
                    cursor={{ fill: "rgba(34, 211, 238, 0.05)" }}
                />
                <Bar dataKey="mean" radius={[6, 6, 0, 0]}>
                    {chartData.map((_, i) => (
                        <Cell key={i} fill={`url(#dist-bar-${i})`} />
                    ))}
                    <ErrorBar dataKey="spread" stroke="#fbbf24" strokeWidth={1.5} />
                </Bar>
            </BarChart>
        </ResponsiveContainer>
    );
}
