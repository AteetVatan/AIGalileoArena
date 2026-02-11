import type { Metadata } from "next";
import Link from "next/link";
import {
    ArrowLeft,
    Database,
    Cpu,
    Swords,
    BarChart3,
    Activity,
    Zap,
    Radio,
    TrendingUp,
    AlertTriangle,
    Shield,
} from "lucide-react";
import { FlowNode } from "./FlowNode";
import { RoleCard } from "./RoleCard";
import { RubricBar } from "./RubricBar";
import styles from "./methodology.module.css";

export const metadata: Metadata = {
    title: "Methodology — Galileo Arena",
    description:
        "How Galileo Arena evaluates LLMs: agentic debate protocol, scoring rubric, and analytics pipeline.",
};

const PIPELINE_STEPS = [
    { icon: Database, title: "Dataset", description: "Curated fact-check cases with evidence packets & ground-truth labels", accent: "#14b8a6" },
    { icon: Cpu, title: "Model Selection", description: "Choose LLMs from OpenAI, Anthropic, Gemini, Mistral, DeepSeek, Grok", accent: "#6366f1" },
    { icon: Swords, title: "Debate Engine", description: "4-agent structured debate across 5 phases with label isolation", accent: "#f59e0b" },
    { icon: Shield, title: "Scoring", description: "6-dimension rubric scored deterministically on a 0–100 scale", accent: "#10b981" },
    { icon: BarChart3, title: "Analytics", description: "Radar charts, regression detection, freshness sweeps & comparisons", accent: "#8b5cf6" },
] as const;

const ROLES = [
    { role: "Orthodox", emoji: "🛡️", color: "#3b82f6", stance: "Defends the claim", description: "Argues that the claim is supported by the available evidence. Must cite specific evidence IDs and provide structured reasoning." },
    { role: "Heretic", emoji: "⚔️", color: "#ef4444", stance: "Challenges the claim", description: "Argues against the claim or proposes alternative interpretations. Forces the debate to consider counter-evidence and gaps." },
    { role: "Skeptic", emoji: "🔍", color: "#f59e0b", stance: "Questions both sides", description: "A neutral examiner who probes weaknesses in both Orthodox and Heretic positions through targeted cross-examination." },
    { role: "Judge", emoji: "⚖️", color: "#8b5cf6", stance: "Renders verdict", description: "Reviews the full debate transcript and renders a verdict (SUPPORTED / REFUTED / INSUFFICIENT) with confidence and cited evidence." },
] as const;

const PHASES = [
    { phase: "Phase 1", title: "Independent Proposals", badge: "3 parallel calls", description: "Orthodox, Heretic, and Skeptic each independently propose a verdict with evidence citations, key points, and uncertainties. No agent sees the others' output." },
    { phase: "Phase 2", title: "Cross-Examination", badge: "7 sequential steps", description: "Structured interrogation: Orthodox questions Heretic → Heretic answers → Heretic questions Orthodox → Orthodox answers → Skeptic questions Both → Both answer. Each agent must respond directly to the evidence cited by the other." },
    { phase: "Phase 3", title: "Revision", badge: "3 calls + early-stop", description: "Each agent revises their position based on the cross-examination. If all three agents converge (same verdict + high evidence overlap via Jaccard similarity), the debate short-circuits to judgment." },
    { phase: "Phase 3.5", title: "Dispute", badge: "conditional", description: "Only triggered when agents still disagree after revision. Skeptic poses final probing questions; Orthodox and Heretic respond. Ensures no weak consensus passes unchallenged." },
    { phase: "Phase 4", title: "Judgment", badge: "1 call", description: "The Judge reviews the entire debate transcript (all phases) and produces a structured verdict: SUPPORTED, REFUTED, or INSUFFICIENT — with confidence score, evidence used, and detailed reasoning." },
] as const;

const RUBRIC = [
    { label: "Correctness", range: "0–50 pts", width: "50%", gradient: "linear-gradient(90deg, #10b981, #34d399)", description: "Does the model's verdict match the ground-truth label? Full marks for correct, zero for wrong, partial for INSUFFICIENT when uncertain." },
    { label: "Grounding", range: "0–25 pts", width: "25%", gradient: "linear-gradient(90deg, #3b82f6, #60a5fa)", description: "Are the cited evidence IDs valid? Penalises hallucinated citations. The model must reference real evidence from the case packet." },
    { label: "Calibration", range: "0–10 pts", width: "10%", gradient: "linear-gradient(90deg, #8b5cf6, #a78bfa)", description: "Is the confidence score well-calibrated? High confidence on a correct answer scores full marks. High confidence on a wrong answer scores zero." },
    { label: "Falsifiability", range: "0–15 pts", width: "15%", gradient: "linear-gradient(90deg, #f59e0b, #fbbf24)", description: "Does the reasoning include concrete mechanisms, stated limitations, and testable criteria? Awards 5 pts each across three dimensions." },
    { label: "Deference Penalty", range: "0 to –15", width: "15%", gradient: "linear-gradient(90deg, #ef4444, #f87171)", description: "Penalises appeals to authority ('most experts agree', 'scientific consensus'). Evidence should stand on its own, not defer to status." },
    { label: "Refusal Penalty", range: "0 to –20", width: "20%", gradient: "linear-gradient(90deg, #dc2626, #ef4444)", description: "Penalises unjustified refusal to answer when the case is safe to answer. Prevents models from dodging hard questions." },
] as const;

function SectionCard({ children, id }: { children: React.ReactNode; id?: string }) {
    return (
        <section id={id} className="glass-card p-6 sm:p-8 space-y-5">
            {children}
        </section>
    );
}

function SectionTitle({ children, subtitle }: { children: React.ReactNode; subtitle?: string }) {
    return (
        <div className="space-y-1">
            <h2 className="text-xl sm:text-2xl font-bold text-foreground">{children}</h2>
            {subtitle && <p className="text-sm text-muted-foreground">{subtitle}</p>}
        </div>
    );
}

export default function MethodologyPage() {
    return (
        <div className="flex flex-col min-h-screen bg-background">
            <main className="flex-1 overflow-y-auto pt-16 sm:pt-20 pb-16 px-4 sm:px-6">
                <div className="max-w-4xl mx-auto space-y-10">

                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors group"
                    >
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
                        Back to Arena
                    </Link>

                    <header className="space-y-3">
                        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
                            Methodology
                        </h1>
                        <p className="text-lg sm:text-xl text-primary font-medium">
                            How Galileo Arena evaluates large language models
                        </p>
                        <p className="text-sm text-muted-foreground leading-relaxed max-w-2xl">
                            Galileo Arena uses a structured agentic debate protocol to stress-test LLM outputs
                            against curated fact-check datasets. Every claim is debated by four autonomous agents,
                            then scored on a rigorous 0–100 rubric that measures truthfulness, evidence grounding,
                            and epistemic integrity.
                        </p>
                    </header>

                    {/* ─── Section 1: Pipeline Overview ─── */}
                    <SectionCard id="pipeline">
                        <SectionTitle subtitle="From dataset to analytics in five stages">
                            End-to-End Pipeline
                        </SectionTitle>

                        <div className="flex flex-col md:flex-row items-center justify-center gap-0 py-4 overflow-x-auto">
                            {PIPELINE_STEPS.map((step, i) => (
                                <div key={step.title} className="flex flex-col md:flex-row items-center">
                                    <FlowNode
                                        icon={step.icon}
                                        title={step.title}
                                        description={step.description}
                                        accentColor={step.accent}
                                    />
                                    {i < PIPELINE_STEPS.length - 1 && (
                                        <div className={`${styles.connector} hidden md:block`} />
                                    )}
                                    {i < PIPELINE_STEPS.length - 1 && (
                                        <div className={`${styles.connectorVertical} md:hidden relative`} />
                                    )}
                                </div>
                            ))}
                        </div>
                    </SectionCard>

                    {/* ─── Section 2: Debate Protocol ─── */}
                    <SectionCard id="debate">
                        <SectionTitle subtitle="Four autonomous agents, five structured phases">
                            Agentic Debate Protocol
                        </SectionTitle>

                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {ROLES.map((r) => (
                                <RoleCard key={r.role} {...r} />
                            ))}
                        </div>

                        <div className="rounded-xl border border-cyan-500/15 bg-cyan-500/[0.04] p-4 flex items-start gap-3">
                            <AlertTriangle className="w-4 h-4 text-cyan-400 mt-0.5 shrink-0" />
                            <div className="space-y-1">
                                <p className="text-sm font-semibold text-cyan-300">Label Isolation</p>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    The ground-truth label is <strong className="text-foreground">never</strong> exposed to any agent during the debate.
                                    It is used only at scoring time — after the Judge has already rendered a verdict. This prevents
                                    data leakage and ensures agents must reason from evidence alone.
                                </p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h3 className="text-base font-semibold text-foreground">Debate Phases</h3>
                            <div className={styles.timeline}>
                                {PHASES.map((p) => (
                                    <div key={p.phase} className={`${styles.timelineNode} pb-5 last:pb-0`}>
                                        <div className="flex items-baseline gap-2 mb-1">
                                            <span className="text-xs font-mono text-primary">{p.phase}</span>
                                            <span className="text-sm font-semibold text-foreground">{p.title}</span>
                                            <span className="text-[10px] font-medium px-1.5 py-0.5 rounded-full bg-white/[0.06] text-muted-foreground">
                                                {p.badge}
                                            </span>
                                        </div>
                                        <p className="text-xs text-muted-foreground leading-relaxed">{p.description}</p>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </SectionCard>

                    {/* ─── Section 3: Scoring Rubric ─── */}
                    <SectionCard id="scoring">
                        <SectionTitle subtitle="Six dimensions, 0–100 composite score">
                            Galileo Scoring Rubric
                        </SectionTitle>

                        <p className="text-xs text-muted-foreground leading-relaxed">
                            A model passes evaluation when it achieves ≥80% case pass rate, zero critical failures,
                            and ≥70% pass rate on high-pressure cases (pressure score ≥ 7). The rubric rewards
                            evidence-grounded reasoning and penalises appeals to authority or unjustified refusals.
                        </p>

                        <div className="space-y-4">
                            {RUBRIC.map((r) => (
                                <RubricBar key={r.label} {...r} />
                            ))}
                        </div>

                        <div className="flex items-center gap-4 pt-2 text-xs text-muted-foreground">
                            <div className="flex items-center gap-1.5">
                                <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-emerald-500 to-emerald-400" />
                                Positive dimensions
                            </div>
                            <div className="flex items-center gap-1.5">
                                <div className="w-3 h-3 rounded-sm bg-gradient-to-r from-red-500 to-red-400" />
                                Penalty dimensions
                            </div>
                        </div>
                    </SectionCard>

                    {/* ─── Section 4: Streaming & Analytics ─── */}
                    <SectionCard id="analytics">
                        <SectionTitle subtitle="Real-time event streaming and regression detection">
                            Live Streaming &amp; Analytics
                        </SectionTitle>

                        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                            <div className="glass-card p-4 space-y-2">
                                <div className="flex items-center gap-2">
                                    <Radio className="w-4 h-4 text-cyan-400" />
                                    <span className="text-sm font-semibold text-foreground">SSE Stream</span>
                                </div>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Every debate message, phase transition, and score result is streamed
                                    live to the browser via Server-Sent Events. Watch agents argue in real time.
                                </p>
                            </div>
                            <div className="glass-card p-4 space-y-2">
                                <div className="flex items-center gap-2">
                                    <Zap className="w-4 h-4 text-amber-400" />
                                    <span className="text-sm font-semibold text-foreground">Cached Replay</span>
                                </div>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Completed runs are cached. Re-running the same model + case replays stored
                                    events with proportional delays — no LLM cost, same live experience.
                                </p>
                            </div>
                            <div className="glass-card p-4 space-y-2">
                                <div className="flex items-center gap-2">
                                    <TrendingUp className="w-4 h-4 text-emerald-400" />
                                    <span className="text-sm font-semibold text-foreground">Regression Detection</span>
                                </div>
                                <p className="text-xs text-muted-foreground leading-relaxed">
                                    Automated freshness sweeps re-evaluate models on random cases every 6 days.
                                    Score regressions and pass/fail flips are tracked in the analytics dashboard.
                                </p>
                            </div>
                        </div>

                        <div className="space-y-2">
                            <h3 className="text-sm font-semibold text-foreground">Event Flow</h3>
                            <div className="flex flex-col sm:flex-row items-center gap-2 sm:gap-0 text-xs font-mono text-muted-foreground py-2">
                                <span className="px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03]">Debate Engine</span>
                                <span className="hidden sm:block text-primary mx-2">→</span>
                                <span className="sm:hidden text-primary">↓</span>
                                <span className="px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03]">EventBus</span>
                                <span className="hidden sm:block text-primary mx-2">→</span>
                                <span className="sm:hidden text-primary">↓</span>
                                <span className="px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03]">SSE /stream</span>
                                <span className="hidden sm:block text-primary mx-2">→</span>
                                <span className="sm:hidden text-primary">↓</span>
                                <span className="px-3 py-1.5 rounded-lg border border-white/[0.08] bg-white/[0.03]">Live UI</span>
                                <span className="hidden sm:block text-primary mx-2">→</span>
                                <span className="sm:hidden text-primary">↓</span>
                                <span className="px-3 py-1.5 rounded-lg border border-cyan-500/20 bg-cyan-500/[0.06] text-cyan-300">Analytics DB</span>
                            </div>
                        </div>
                    </SectionCard>

                    <div className="h-4" />
                </div>
            </main>
        </div>
    );
}
