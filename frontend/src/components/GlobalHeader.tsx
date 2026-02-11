"use client";

import Link from "next/link";
import { ArrowUpRight, BarChart3, Info, Rocket, Workflow } from "lucide-react";
import { useNavLock } from "@/hooks/useNavLock";

export function GlobalHeader() {
    const { locked } = useNavLock();

    const disabledClass = "pointer-events-none opacity-40 cursor-not-allowed";

    return (
        <div className="flex w-full gap-3 sm:gap-6 px-4 sm:px-6 lg:px-8 pt-3 sm:pt-[14px] absolute top-0 left-0 z-50 pointer-events-none">
            <div className="flex-1 flex items-start gap-4 pointer-events-auto">
                <div className="flex flex-col items-start gap-1">
                    <Link
                        href="/"
                        className={`block text-2xl sm:text-3xl lg:text-4xl font-extrabold leading-tight text-foreground mb-0 hover:text-primary transition-colors cursor-pointer w-fit tracking-tight ${locked ? disabledClass : ""}`}
                        aria-disabled={locked}
                        tabIndex={locked ? -1 : undefined}
                        onClick={locked ? (e) => e.preventDefault() : undefined}
                    >
                        Galileo Arena
                    </Link>
                    <Link
                        href="/methodology"
                        className={`group relative flex items-center gap-1.5 text-[11px] font-medium px-2.5 py-1 rounded-lg border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm text-white/50 hover:text-cyan-300 hover:border-cyan-500/25 hover:bg-cyan-500/[0.06] transition-all duration-300 ${locked ? disabledClass : ""}`}
                        aria-disabled={locked}
                        tabIndex={locked ? -1 : undefined}
                        onClick={locked ? (e) => e.preventDefault() : undefined}
                    >
                        <Workflow className="w-3 h-3" />
                        <span className="tracking-wide">Methodology</span>
                    </Link>
                </div>
                <Link
                    href="/about"
                    className={`group flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm text-white/60 hover:text-cyan-300 hover:border-cyan-500/25 hover:bg-cyan-500/[0.06] transition-all duration-300 ${locked ? disabledClass : ""}`}
                    aria-disabled={locked}
                    tabIndex={locked ? -1 : undefined}
                    onClick={locked ? (e) => e.preventDefault() : undefined}
                >
                    <Info className="w-3.5 h-3.5" />
                    <span className="tracking-wide">About</span>
                </Link>
                <Link
                    href="/graphs"
                    className={`group flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm text-white/60 hover:text-cyan-300 hover:border-cyan-500/25 hover:bg-cyan-500/[0.06] transition-all duration-300 ${locked ? disabledClass : ""}`}
                    aria-disabled={locked}
                    tabIndex={locked ? -1 : undefined}
                    onClick={locked ? (e) => e.preventDefault() : undefined}
                >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span className="tracking-wide">Analytics</span>
                </Link>
                <Link
                    href="/datasets"
                    className={`group flex items-center gap-2 text-sm sm:text-base font-semibold px-5 sm:px-6 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg shadow-teal-900/30 hover:shadow-teal-600/25 hover:-translate-y-0.5 transition-all duration-300 ${locked ? disabledClass : ""}`}
                    aria-disabled={locked}
                    tabIndex={locked ? -1 : undefined}
                    onClick={locked ? (e) => e.preventDefault() : undefined}
                >
                    <Rocket className="w-4 h-4 sm:w-[18px] sm:h-[18px]" />
                    <span className="tracking-wide">Get Started</span>
                    <ArrowUpRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 opacity-60 group-hover:opacity-100 transition-opacity" />
                </Link>
            </div>
        </div>
    );
}
