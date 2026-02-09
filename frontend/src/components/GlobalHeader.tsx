"use client";

import Link from "next/link";

export function GlobalHeader() {
    return (
        <div className="flex w-full gap-3 sm:gap-6 px-4 sm:px-6 lg:px-8 pt-3 sm:pt-[14px] absolute top-0 left-0 z-50 pointer-events-none">
            {/* Left Section - Galileo Arena */}
            <div className="flex-1 pointer-events-auto">
                <Link
                    href="/"
                    className="block text-2xl sm:text-3xl lg:text-4xl font-extrabold leading-tight text-foreground mb-0 hover:text-primary transition-colors cursor-pointer w-fit"
                >
                    Galileo Arena
                </Link>
            </div>
        </div>
    );
}
