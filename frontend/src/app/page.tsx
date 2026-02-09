"use client";

import dynamic from "next/dynamic";
import Image from "next/image";
import {
  Search, Bell, Phone, ChevronLeft, ChevronRight, ArrowUpRight,
  LayoutGrid, MessageSquare, FileText, Settings, Heart, Power, Activity, Calendar, Swords
} from "lucide-react";

const Earth3D = dynamic(() => import("@/components/Earth3D"), { ssr: false });

const navItems = [
  { icon: Heart, active: false },
  { icon: MessageSquare, active: false },
  { icon: FileText, active: false },
  { icon: Settings, active: false },
  { icon: LayoutGrid, active: false },
];

const doctors = [
  { name: "Dr. Hanzer Jon", image: "https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?w=100&h=100&fit=crop&crop=face" },
  { name: "Dr. Steve Alex", image: "https://images.unsplash.com/photo-1559839734-2b71ea197ec2?w=100&h=100&fit=crop&crop=face" },
  { name: "Dr. Johan Fraz", image: "https://images.unsplash.com/photo-1537368910025-700350fe46c7?w=100&h=100&fit=crop&crop=face" },
];

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
              <div className="absolute bottom-4 right-4 sm:top-1/2 sm:right-4 sm:-translate-y-1/2 lg:top-1/2 lg:right-4 lg:-translate-y-1/2 z-20">
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


            </div>
          </div>

          {/* Right Section - Cards */}
          <div className="w-full lg:w-[420px] flex flex-col gap-4 sm:gap-6 justify-center relative">

            {/* Cards Section */}
            <div>
              <div className="grid grid-cols-2 gap-2 sm:gap-3">
                {/* Blood Status Card */}
                <div className="glass-card p-3 sm:p-4">
                  <div className="flex items-center gap-1.5 sm:gap-2 mb-2">
                    <Activity className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
                    <span className="text-[10px] sm:text-xs text-muted-foreground">Blood Status</span>
                  </div>
                  <p className="text-xl sm:text-2xl font-bold text-foreground">116<span className="text-primary">/70</span></p>
                  <div className="mt-3 flex gap-1 items-end">
                    {[60, 75, 85, 70, 90, 95, 88].map((h, i) => (
                      <div key={i} className="w-3 rounded-sm bg-primary/60" style={{ height: `${h * 0.4}px` }} />
                    ))}
                  </div>
                </div>

                {/* Heart Rate Card */}
                <div className="glass-card p-3 sm:p-4 flex items-center gap-2 sm:gap-3">
                  <Heart className="h-4 w-4 sm:h-5 sm:w-5 text-muted-foreground" />
                  <div>
                    <span className="text-[10px] sm:text-xs text-muted-foreground block">Heart Rate</span>
                    <p className="text-xl sm:text-2xl font-bold text-foreground">120 <span className="text-primary text-xs sm:text-sm">bpm</span></p>
                  </div>
                  <div className="ml-auto relative h-12 w-12 sm:h-16 sm:w-16">
                    <svg className="h-full w-full -rotate-90" viewBox="0 0 36 36">
                      <circle cx="18" cy="18" r="14" fill="none" stroke="hsl(var(--secondary))" strokeWidth="3" />
                      <circle cx="18" cy="18" r="14" fill="none" stroke="hsl(var(--primary))" strokeWidth="3" strokeDasharray="85 100" strokeLinecap="round" />
                    </svg>
                    <span className="absolute inset-0 flex items-center justify-center text-[10px] sm:text-xs font-bold text-foreground">120</span>
                  </div>
                </div>

                {/* Blood Count Card */}
                <div className="glass-card p-3 sm:p-4">
                  <div className="flex items-center gap-1.5 sm:gap-2 mb-2">
                    <Activity className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
                    <span className="text-[10px] sm:text-xs text-muted-foreground">Blood Count</span>
                  </div>
                  <p className="text-xl sm:text-2xl font-bold text-foreground">80<span className="text-muted-foreground">-</span><span className="text-primary">90</span></p>
                  <div className="mt-3 flex items-center gap-2">
                    {/* Wave line */}
                    <svg className="flex-1 h-6" viewBox="0 0 100 24">
                      <path
                        d="M0,12 Q10,4 20,12 T40,12 T60,12 T80,12 T100,12"
                        fill="none"
                        stroke="hsl(var(--muted-foreground))"
                        strokeWidth="1.5"
                      />
                    </svg>
                    <span className="text-base sm:text-lg font-bold text-foreground">80</span>
                  </div>
                  <p className="text-right text-[10px] sm:text-xs text-muted-foreground mt-1">/90</p>
                </div>

                {/* Glucose Level Card */}
                <div className="glass-card p-3 sm:p-4">
                  <div className="flex items-center gap-1.5 sm:gap-2 mb-2">
                    <Activity className="h-3 w-3 sm:h-4 sm:w-4 text-muted-foreground" />
                    <span className="text-[10px] sm:text-xs text-muted-foreground">Glucose Level</span>
                  </div>
                  <p className="text-xl sm:text-2xl font-bold text-foreground">230<span className="text-primary">/ml</span></p>
                  <div className="mt-3 flex items-center gap-2">
                    {/* Wave line */}
                    <svg className="flex-1 h-6" viewBox="0 0 100 24">
                      <path
                        d="M0,12 Q10,4 20,12 T40,12 T60,12 T80,12 T100,12"
                        fill="none"
                        stroke="hsl(var(--muted-foreground))"
                        strokeWidth="1.5"
                      />
                    </svg>
                    <span className="text-base sm:text-lg font-bold text-foreground">230</span>
                  </div>
                  <p className="text-right text-[10px] sm:text-xs text-muted-foreground mt-1">/ml</p>
                </div>
              </div>
            </div>



            {/* My Body Condition Section */}
            <div>
              <div className="flex items-center justify-between mb-3 sm:mb-4">
                <div className="flex items-center gap-1.5 sm:gap-2">
                  <span className="h-1.5 w-1.5 sm:h-2 sm:w-2 rounded-full bg-primary" />
                  <h2 className="text-base sm:text-lg font-semibold text-foreground">My Body Condition</h2>
                </div>
                <div className="flex gap-1">
                  <button className="h-5 w-5 sm:h-6 sm:w-6 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
                    <ChevronLeft className="h-2.5 w-2.5 sm:h-3 sm:w-3" />
                  </button>
                  <button className="h-5 w-5 sm:h-6 sm:w-6 rounded-full bg-secondary flex items-center justify-center text-muted-foreground hover:text-foreground transition-colors">
                    <ChevronRight className="h-2.5 w-2.5 sm:h-3 sm:w-3" />
                  </button>
                </div>
              </div>
              <div className="grid grid-cols-4 gap-2 sm:flex sm:gap-3">
                {[
                  { name: "Liver", color: "from-orange-500/20 to-amber-600/20", emoji: "🫁" },
                  { name: "My Heart", color: "from-red-500/20 to-rose-600/20", emoji: "❤️" },
                  { name: "Kidney", color: "from-pink-500/20 to-rose-600/20", emoji: "🫘" },
                  { name: "Brain", color: "from-gray-500/20 to-slate-600/20", emoji: "🧠" },
                ].map((organ) => (
                  <div key={organ.name} className={`glass-card flex-1 aspect-square flex flex-col items-center justify-center p-2 sm:p-3 bg-gradient-to-br ${organ.color}`}>
                    <div className="h-8 w-8 sm:h-12 sm:w-12 rounded-full bg-secondary/50 flex items-center justify-center mb-1 sm:mb-2 text-lg sm:text-2xl">
                      {organ.emoji}
                    </div>
                    <button className="mt-auto flex items-center gap-0.5 sm:gap-1 rounded-full bg-primary/20 px-2 sm:px-3 py-0.5 sm:py-1 text-[10px] sm:text-xs font-medium text-primary hover:bg-primary/30 transition-colors">
                      <span className="hidden sm:inline">{organ.name}</span>
                      <ArrowUpRight className="h-2.5 w-2.5 sm:h-3 sm:w-3" />
                    </button>
                  </div>
                ))}
              </div>

              {/* Galileo Tribute Card - Moved to Bottom */}
              <div className="mt-6 w-full">
                <div className="glass-card p-5 rounded-2xl bg-black/40 backdrop-blur-xl border border-white/10 flex flex-col items-center sm:items-end gap-3 shadow-2xl relative overflow-hidden group">
                  <div className="absolute inset-0 bg-gradient-to-br from-indigo-500/5 via-transparent to-cyan-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-700"></div>

                  <div className="flex items-center gap-3 mb-1 z-10">
                    <span className="text-xs font-bold tracking-[0.2em] text-cyan-400 uppercase">Agentic Arena</span>
                    <div className="h-px w-8 bg-gradient-to-l from-cyan-400 to-transparent"></div>
                  </div>

                  <p className="text-sm text-slate-300 font-serif leading-relaxed text-center sm:text-right z-10">
                    Galilaeus pro Copernico stetit. Pressus ab <span className="text-cyan-300 font-semibold drop-shadow-[0_0_8px_rgba(103,232,249,0.3)]">orthodoxis</span> et <span className="text-cyan-300 font-semibold drop-shadow-[0_0_8px_rgba(103,232,249,0.3)]">skepticis</span>, voce cessit—non mente. Scientia tamen perseverat.
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
        </main>
      </div>
    </div>
  );
}
