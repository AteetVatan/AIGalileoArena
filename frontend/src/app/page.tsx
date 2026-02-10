"use client";

import dynamic from "next/dynamic";
import {
  ArrowUpRight, Swords
} from "lucide-react";

const Earth3D = dynamic(() => import("@/components/Earth3D"), { ssr: false });
const StartDashboard = dynamic(() => import("@/components/StartDashboard"), { ssr: false });



export default function Home() {
  return (
    <div className="flex min-h-screen w-full bg-background overflow-x-hidden">

      {/* Main Content */}
      <div className="flex flex-1 flex-col overflow-hidden">

        {/* Main Grid */}
        <main className="flex flex-col lg:flex-row flex-1 gap-4 sm:gap-6 overflow-auto px-4 sm:px-6 lg:px-8 pb-6 sm:pb-8">
          {/* Left Section - Hero */}
          <div className="flex-1 relative overflow-hidden flex flex-col pt-[50px] sm:pt-[60px] lg:pt-[60px] min-h-[500px] lg:min-h-0">




            {/* Earth Visualization */}
            <div className="relative flex-1 w-full flex items-center justify-center -mt-[20px] sm:-mt-[30px] lg:-mt-[38px]">
              <Earth3D />

              {/* Heart Rate Card Overlay */}
              <div className="absolute bottom-4 left-4 sm:bottom-6 sm:left-6 glass-card p-4 sm:p-6 flex flex-col gap-2 sm:gap-3 z-10 max-w-[280px] sm:max-w-[320px] backdrop-blur-xl border-primary/20 bg-background/30">
                <div className="flex items-center gap-2 sm:gap-3">
                  <div className="p-1.5 sm:p-2 rounded-full bg-primary/20 text-primary animate-pulse">
                    <Swords className="h-4 w-4 sm:h-5 sm:w-5" />
                  </div>
                  <span className="text-xs sm:text-sm font-semibold text-foreground tracking-wide">Agentic Arena</span>
                </div>
                <p className="text-xs sm:text-sm text-muted-foreground leading-relaxed">
                  Multi-model agentic debate platform. Pick a dataset, select LLM models, and watch <span className="text-foreground font-medium">Orthodox</span>, <span className="text-foreground font-medium">Heretic</span>, <span className="text-foreground font-medium">Skeptic</span> & <span className="text-foreground font-medium">Judge</span> agents duke it out live.
                </p>
              </div>

              {/* Get Started Button */}
              <div className="absolute top-4 right-4 sm:top-1/2 sm:right-4 sm:-translate-y-1/2 lg:top-1/2 lg:right-4 lg:-translate-y-1/2 z-20">
                <a
                  href="/datasets"
                  className="group relative inline-flex h-10 sm:h-12 items-center justify-center overflow-hidden rounded-full bg-slate-950 px-6 sm:px-8 font-medium text-slate-200 transition-all duration-300 hover:bg-slate-950/50 hover:text-white hover:shadow-[0_0_40px_rgba(59,130,246,0.6)] focus:outline-none focus:ring-2 focus:ring-slate-400 focus:ring-offset-2 focus:ring-offset-slate-50"
                >
                  <span className="absolute inset-0 overflow-hidden rounded-full">
                    <span className="absolute inset-0 rounded-full bg-[image:radial-gradient(75%_100%_at_50%_0%,rgba(56,189,248,0.6)_0%,rgba(56,189,248,0)_75%)] opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
                  </span>
                  <div className="relative flex items-center gap-1.5 sm:gap-2 z-10">
                    <span className="bg-gradient-to-r from-indigo-400 to-cyan-400 bg-clip-text text-transparent group-hover:text-white transition-colors duration-300 font-bold tracking-wide text-sm sm:text-base">Get Started</span>
                    <ArrowUpRight className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-cyan-400 group-hover:text-white transition-transform group-hover:translate-x-1 group-hover:-translate-y-1" />
                  </div>
                  <span className="absolute -bottom-0 left-[1.125rem] h-px w-[calc(100%-2.25rem)] bg-gradient-to-r from-emerald-400/0 via-emerald-400/90 to-emerald-400/0 transition-opacity duration-500 group-hover:opacity-40" />
                </a>
              </div>

              {/* Galileo Signature */}
              {/* Galileo Tribute Card */}
              <div className="hidden sm:block absolute bottom-4 right-4 sm:bottom-6 sm:right-6 z-10 max-w-[280px] sm:max-w-[320px] pointer-events-none select-none text-right">
                <div className="glass-card p-5 rounded-2xl bg-black/40 backdrop-blur-xl border border-white/10 flex flex-col items-end gap-3 pointer-events-auto shadow-2xl relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                  <div className="flex items-center gap-3 mb-1 z-10">
                    <span className="text-xs font-bold tracking-[0.2em] text-cyan-400 uppercase">Agentic Arena</span>
                    <div className="h-px w-8 bg-gradient-to-l from-cyan-400 to-transparent"></div>
                  </div>

                  <p className="text-sm text-slate-300 font-serif leading-relaxed text-right z-10">
                    Galilaeus pro Copernico stetit. Pressus ab <span className="text-cyan-300 font-semibold drop-shadow-[0_0_8px_rgba(103,232,249,0.3)]">orthodoxis</span> et <span className="text-cyan-300 font-semibold drop-shadow-[0_0_8px_rgba(103,232,249,0.3)]">scepticis</span>, voce cessit—non mente. Scientia tamen perseverat.
                  </p>

                  <div className="mt-1 opacity-90 z-10 relative">
                    <div className="absolute -inset-4 bg-gradient-to-r from-transparent via-white/5 to-transparent blur-xl -skew-x-12 translate-x-[-100%] group-hover:translate-x-[100%] transition-transform duration-1000"></div>
                    <span className="font-great-vibes text-4xl text-white -rotate-6 block tracking-wide" style={{ fontFamily: 'var(--font-great-vibes)' }}>
                      Galileo Galilei
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Right Section - Analytics Dashboard */}
          <div className="w-full lg:w-[520px] flex flex-col justify-center relative">
            <StartDashboard />
          </div>
        </main>
      </div>
    </div>
  );
}
