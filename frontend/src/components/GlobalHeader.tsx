"use client";

import Link from "next/link";
import { ArrowUpRight, BarChart3, Info, Rocket } from "lucide-react";

export function GlobalHeader() {
    return (
        <div className="flex w-full gap-3 sm:gap-6 px-4 sm:px-6 lg:px-8 pt-3 sm:pt-[14px] absolute top-0 left-0 z-50 pointer-events-none">
            <div className="flex-1 flex items-center gap-4 pointer-events-auto">
                <Link
                    href="/"
                    className="block text-2xl sm:text-3xl lg:text-4xl font-extrabold leading-tight text-foreground mb-0 hover:text-primary transition-colors cursor-pointer w-fit tracking-tight"
                >
                    Galileo Arena
                </Link>
                <Link
                    href="/about"
                    className="group flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm text-white/60 hover:text-cyan-300 hover:border-cyan-500/25 hover:bg-cyan-500/[0.06] transition-all duration-300"
                >
                    <Info className="w-3.5 h-3.5" />
                    <span className="tracking-wide">About</span>
                </Link>
                <Link
                    href="/graphs"
                    className="group flex items-center gap-1.5 text-sm font-medium px-4 py-1.5 rounded-xl border border-white/[0.08] bg-white/[0.03] backdrop-blur-sm text-white/60 hover:text-cyan-300 hover:border-cyan-500/25 hover:bg-cyan-500/[0.06] transition-all duration-300"
                >
                    <BarChart3 className="w-3.5 h-3.5" />
                    <span className="tracking-wide">Analytics</span>
                </Link>
                <Link
                    href="/datasets"
                    className="group flex items-center gap-2 text-sm sm:text-base font-semibold px-5 sm:px-6 py-2 sm:py-2.5 rounded-xl bg-gradient-to-r from-teal-600 to-cyan-600 text-white shadow-lg shadow-teal-900/30 hover:shadow-teal-600/25 hover:-translate-y-0.5 transition-all duration-300"
                >
                    <Rocket className="w-4 h-4 sm:w-[18px] sm:h-[18px]" />
                    <span className="tracking-wide">Get Started</span>
                    <ArrowUpRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 opacity-60 group-hover:opacity-100 transition-opacity" />
                </Link>
            </div>
        </div>
    );
}
