"use client";

import Link from "next/link";

export function GlobalHeader() {
    return (
        <div className="flex w-full gap-3 sm:gap-6 px-4 sm:px-6 lg:px-8 pt-3 sm:pt-[14px] absolute top-0 left-0 z-50 pointer-events-none">
            <style>{`
                @keyframes analytics-shimmer {
                    0% { background-position: -200% center; }
                    100% { background-position: 200% center; }
                }
                @keyframes analytics-glow {
                    0%, 100% { box-shadow: 0 0 8px rgba(6,182,212,0.3), 0 0 20px rgba(139,92,246,0.15); }
                    50% { box-shadow: 0 0 14px rgba(6,182,212,0.5), 0 0 32px rgba(139,92,246,0.25); }
                }
                .analytics-btn {
                    position: relative;
                    background: linear-gradient(135deg, rgba(6,182,212,0.12), rgba(139,92,246,0.12));
                    backdrop-filter: blur(12px);
                    border: 1px solid transparent;
                    background-clip: padding-box;
                    animation: analytics-glow 3s ease-in-out infinite;
                }
                .analytics-btn::before {
                    content: '';
                    position: absolute;
                    inset: -1px;
                    border-radius: inherit;
                    padding: 1px;
                    background: linear-gradient(135deg, #06b6d4, #8b5cf6, #ec4899, #06b6d4);
                    background-size: 300% 300%;
                    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
                    -webkit-mask-composite: xor;
                    mask-composite: exclude;
                    animation: analytics-shimmer 4s linear infinite;
                    pointer-events: none;
                }
                .analytics-btn:hover {
                    background: linear-gradient(135deg, rgba(6,182,212,0.22), rgba(139,92,246,0.22));
                    transform: translateY(-1px) scale(1.04);
                    box-shadow: 0 0 18px rgba(6,182,212,0.5), 0 0 40px rgba(139,92,246,0.3) !important;
                }
                .analytics-btn:hover .analytics-label {
                    background-size: 200% auto;
                    animation: analytics-shimmer 1.5s linear infinite;
                }
                .analytics-label {
                    background: linear-gradient(90deg, #67e8f9, #c4b5fd, #f9a8d4, #67e8f9);
                    background-size: 100% auto;
                    -webkit-background-clip: text;
                    -webkit-text-fill-color: transparent;
                    background-clip: text;
                    transition: background-size 0.3s;
                }
            `}</style>
            <div className="flex-1 flex items-center gap-4 pointer-events-auto">
                <Link
                    href="/"
                    className="block text-2xl sm:text-3xl lg:text-4xl font-extrabold leading-tight text-foreground mb-0 hover:text-primary transition-colors cursor-pointer w-fit"
                >
                    Galileo Arena
                </Link>
                <Link
                    href="/graphs"
                    className="analytics-btn text-sm font-semibold px-4 py-1.5 rounded-xl transition-all duration-300 ease-out cursor-pointer flex items-center gap-1.5"
                >
                    <span className="text-base">📊</span>
                    <span className="analytics-label tracking-wide">Analytics</span>
                </Link>
            </div>
        </div>
    );
}

