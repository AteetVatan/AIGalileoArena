import type { ReactNode } from "react";

type CardSize = "sm" | "md" | "lg";

interface GlassCardProps {
    title?: string;
    size?: CardSize;
    children: ReactNode;
    className?: string;
}

const sizeConfig = {
    sm: { padding: "p-4", titleText: "text-[10px]", dot: "w-1 h-1", gap: "gap-1.5", mb: "mb-3" },
    md: { padding: "p-5", titleText: "text-xs", dot: "w-1.5 h-1.5", gap: "gap-2", mb: "mb-4" },
    lg: { padding: "p-6", titleText: "text-sm", dot: "w-2 h-2", gap: "gap-2", mb: "mb-4" },
} as const;

export function GlassCard({ title, size = "md", children, className = "" }: GlassCardProps) {
    const cfg = sizeConfig[size];

    return (
        <div className={`relative group rounded-2xl p-px overflow-hidden ${className}`}>
            <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-cyan-500/20 via-transparent to-purple-500/20 opacity-60 group-hover:opacity-100 transition-opacity duration-500" />
            <div className={`relative bg-slate-900/80 backdrop-blur-xl rounded-2xl ${cfg.padding} shadow-[inset_0_1px_0_rgba(255,255,255,0.06)] h-full flex flex-col`}>
                {title && (
                    <h3 className={`${cfg.titleText} font-semibold text-cyan-400/80 uppercase tracking-[0.15em] ${cfg.mb} flex items-center ${cfg.gap} flex-shrink-0`}>
                        <span className={`${cfg.dot} rounded-full bg-cyan-400 shadow-[0_0_6px_rgba(34,211,238,0.6)]`} />
                        {title}
                    </h3>
                )}
                <div className="flex-1 min-h-0">
                    {children}
                </div>
            </div>
        </div>
    );
}
