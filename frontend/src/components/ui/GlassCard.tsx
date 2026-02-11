"use client";

interface GlassCardProps {
    children: React.ReactNode;
    title?: string;
    className?: string;
    size?: "sm" | "md" | "lg";
}

const SIZE_CONFIG = {
    sm: { padding: "p-3", titleText: "text-[9px]", mb: "mb-1.5", gap: "gap-1", dot: "w-1 h-1" },
    md: { padding: "p-5", titleText: "text-[10px]", mb: "mb-3", gap: "gap-1.5", dot: "w-1.5 h-1.5" },
    lg: { padding: "p-6", titleText: "text-xs", mb: "mb-4", gap: "gap-2", dot: "w-1.5 h-1.5" },
} as const;

export function GlassCard({ children, title, className = "", size = "md" }: GlassCardProps) {
    const cfg = SIZE_CONFIG[size];

    return (
        <div className={`relative group rounded-2xl overflow-hidden ${className}`}>
            {/* Edge-lit top bar */}
            <div className="absolute top-0 left-4 right-4 h-px bg-gradient-to-r from-transparent via-cyan-400/40 to-transparent group-hover:via-cyan-300/60 transition-colors duration-500" />

            {/* Card body */}
            <div className={`relative bg-[hsl(224_28%_9%/0.7)] backdrop-blur-xl rounded-2xl border border-white/[0.06] ${cfg.padding} shadow-[0_1px_2px_rgba(0,0,0,0.5),inset_0_1px_0_rgba(255,255,255,0.04)] group-hover:shadow-[0_4px_24px_rgba(0,0,0,0.4),inset_0_1px_0_rgba(255,255,255,0.06)] group-hover:-translate-y-0.5 transition-all duration-300 h-full flex flex-col`}>
                {title && (
                    <h3 className={`${cfg.titleText} font-semibold text-white/40 uppercase tracking-[0.15em] ${cfg.mb} flex items-center ${cfg.gap} flex-shrink-0`}>
                        <span className={`${cfg.dot} rounded-full bg-cyan-400/60`} />
                        {title}
                    </h3>
                )}
                <div className="flex-1 min-h-0">{children}</div>
            </div>
        </div>
    );
}
