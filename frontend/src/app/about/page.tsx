import type { Metadata } from "next";
import Image from "next/image";
import Link from "next/link";
import { ArrowLeft, Linkedin, Github, Globe, Mail, BookOpen } from "lucide-react";

export const metadata: Metadata = {
    title: "About Galileo AI — Galileo Arena",
    description:
        "A tribute to evidence, not authority. Learn about the Galileo Standard for LLM behavior.",
};

function SectionCard({ children, className = "" }: { children: React.ReactNode; className?: string }) {
    return (
        <div className={`glass-card p-6 sm:p-8 space-y-4 ${className}`}>
            {children}
        </div>
    );
}

export default function AboutPage() {
    return (
        <div className="flex flex-col min-h-screen bg-background">
            <main className="flex-1 overflow-y-auto pt-16 sm:pt-20 pb-16 px-4 sm:px-6">
                <div className="max-w-3xl mx-auto space-y-10">

                    {/* Back link */}
                    <Link
                        href="/"
                        className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground transition-colors group"
                    >
                        <ArrowLeft className="w-4 h-4 group-hover:-translate-x-0.5 transition-transform" />
                        Back to Arena
                    </Link>

                    {/* Title */}
                    <header className="space-y-3">
                        <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-foreground">
                            About Galileo AI
                        </h1>
                        <p className="text-lg sm:text-xl text-primary font-medium italic">
                            A tribute to evidence, not authority
                        </p>
                    </header>

                    {/* Intro */}
                    <section className="space-y-4 text-muted-foreground leading-relaxed">
                        <p>
                            Galileo AI is inspired by <span className="text-foreground font-medium">Galileo Galilei</span> — not as a symbol of rebellion,
                            but as a symbol of discipline: the idea that claims about reality must answer to evidence, not status, confidence, or tradition.
                        </p>
                        <p>
                            Centuries ago, <span className="text-foreground font-medium">Nicolaus Copernicus</span> helped shift humanity&apos;s understanding of the cosmos.
                            Galileo defended that evidence-based worldview and paid a steep personal price, including condemnation and restriction under the Roman Inquisition.
                        </p>
                        <p>
                            That story matters today because we&apos;re building systems that don&apos;t just describe reality — they influence decisions inside it.
                        </p>
                    </section>

                    {/* Galileo Images */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                        <div className="relative aspect-[4/5] rounded-xl overflow-hidden border border-white/[0.08]">
                            <Image
                                src="/galileo-portrait.jpg"
                                alt="Portrait of Galileo Galilei"
                                fill
                                className="object-cover"
                                sizes="(max-width: 640px) 100vw, 50vw"
                            />
                            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-4">
                                <p className="text-sm text-white/80 font-medium">Galileo Galilei</p>
                            </div>
                        </div>
                        <div className="relative aspect-[4/5] rounded-xl overflow-hidden border border-white/[0.08]">
                            <Image
                                src="/galileo-study.jpg"
                                alt="Galileo's study — desk, books, and instruments"
                                fill
                                className="object-cover"
                                sizes="(max-width: 640px) 100vw, 50vw"
                            />
                            <div className="absolute bottom-0 inset-x-0 bg-gradient-to-t from-black/70 to-transparent p-4">
                                <p className="text-sm text-white/80 font-medium">Galileo&apos;s Study</p>
                            </div>
                        </div>
                    </div>

                    {/* The Modern Problem */}
                    <SectionCard>
                        <h2 className="text-xl sm:text-2xl font-bold text-foreground">The modern problem</h2>
                        <div className="space-y-3 text-muted-foreground leading-relaxed">
                            <p>
                                LLMs can be brilliant and still be wrong.<br />
                                They can sound confident while being ungrounded.<br />
                                They can &ldquo;complete&rdquo; an answer even when the truth is: <em className="text-foreground">they don&apos;t know.</em>
                            </p>
                            <p>If we accept that behavior, we get a world where:</p>
                            <ul className="space-y-2 pl-1">
                                {[
                                    "fluent outputs replace facts",
                                    "confidence replaces calibration",
                                    "speed replaces correctness",
                                    "and users stop being able to tell the difference",
                                ].map((item) => (
                                    <li key={item} className="flex items-start gap-2">
                                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-destructive shrink-0" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                            <p className="text-primary font-semibold pt-2">Galileo AI exists to prevent that.</p>
                        </div>
                    </SectionCard>

                    {/* The Galileo Standard */}
                    <SectionCard>
                        <h2 className="text-xl sm:text-2xl font-bold text-foreground">
                            The Galileo Standard for LLM behavior
                        </h2>
                        <div className="space-y-3 text-muted-foreground leading-relaxed">
                            <p>
                                In Galileo AI, models are not judged by style, cleverness, or persuasion.<br />
                                They&apos;re judged by <span className="text-foreground font-medium">realistic, reliable behavior.</span>
                            </p>
                            <p className="font-semibold text-foreground">The standard:</p>
                            <ul className="space-y-3">
                                {[
                                    { label: "Reality-aligned", desc: "Prefer verifiable claims. Don't invent details to fill gaps." },
                                    { label: "Grounded by default", desc: "If sources/context are missing, say what's missing and what would verify it." },
                                    { label: "Calibrated uncertainty", desc: "If the model isn't sure, it must say so clearly — no fake precision." },
                                    { label: "Transparent assumptions", desc: "Separate facts vs assumptions vs guesses." },
                                    { label: "Consistency under repetition", desc: "Similar inputs shouldn't produce chaotic shifts without cause." },
                                    { label: "Non-dogmatic updating", desc: "New evidence should update outputs cleanly — no narrative defense." },
                                ].map(({ label, desc }) => (
                                    <li key={label} className="flex items-start gap-3">
                                        <span className="mt-1.5 h-2 w-2 rounded-full bg-primary shrink-0" />
                                        <span>
                                            <span className="text-foreground font-semibold">{label}</span>
                                            <span className="text-muted-foreground"> — {desc}</span>
                                        </span>
                                    </li>
                                ))}
                            </ul>
                            <p className="text-sm italic text-accent pt-2">
                                This is what &ldquo;truth-first&rdquo; looks like in practice.
                            </p>
                        </div>
                    </SectionCard>

                    {/* What Galileo AI Does */}
                    <SectionCard>
                        <h2 className="text-xl sm:text-2xl font-bold text-foreground">What Galileo AI does</h2>
                        <div className="space-y-3 text-muted-foreground leading-relaxed">
                            <p>
                                Galileo AI is an <span className="text-foreground font-medium">evaluation + analytics layer</span> that turns model selection into an engineering decision.
                            </p>
                            <p>It helps you:</p>
                            <ul className="space-y-2 pl-1">
                                {[
                                    "compare multiple LLMs across the same datasets and cases",
                                    "detect regressions when models update",
                                    "track truthfulness, consistency, and calibration over time",
                                    "expose trade-offs: quality vs latency vs cost",
                                    "make model choice repeatable, explainable, and defensible",
                                ].map((item) => (
                                    <li key={item} className="flex items-start gap-2">
                                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-green-400 shrink-0" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                            <p className="text-primary font-semibold pt-2">
                                In short: we test the truth before we trust the model.
                            </p>
                        </div>
                    </SectionCard>

                    {/* About Me */}
                    <SectionCard className="border-primary/20">
                        <div className="flex flex-col sm:flex-row gap-5 items-start">
                            <div className="relative w-28 h-28 sm:w-32 sm:h-32 rounded-full overflow-hidden border-2 border-primary/30 shrink-0">
                                <Image
                                    src="/ateet.jpeg"
                                    alt="Ateet Bahamani"
                                    fill
                                    className="object-cover"
                                    sizes="128px"
                                />
                            </div>
                            <div>
                                <h2 className="text-xl sm:text-2xl font-bold text-foreground">About Me</h2>
                                <p className="text-sm font-medium text-primary tracking-wide mt-1">
                                    Ateet Bahamani &middot; AI Architect / AI Engineer
                                </p>
                            </div>
                        </div>
                        <div className="space-y-3 text-muted-foreground leading-relaxed">
                            <p>
                                I&apos;m Ateet Bahamani, an AI Architect building AI systems with one obsession: <span className="text-foreground font-medium">reliability at scale.</span>
                            </p>
                            <p>My work sits at the intersection of:</p>
                            <ul className="space-y-2 pl-1">
                                {[
                                    "LLM evaluation & analytics (measuring what matters, not what looks good)",
                                    "agentic workflows with guardrails (tools + memory + structure, without chaos)",
                                    "clean architecture (systems that stay maintainable as they grow)",
                                    "fullstack execution (backend + frontend, ship end-to-end)",
                                ].map((item) => (
                                    <li key={item} className="flex items-start gap-2">
                                        <span className="mt-1.5 h-1.5 w-1.5 rounded-full bg-accent shrink-0" />
                                        <span>{item}</span>
                                    </li>
                                ))}
                            </ul>
                            <p>
                                I build AI products that behave like responsible instruments: <span className="text-foreground font-medium">grounded, honest, and repeatable</span> : not just impressive demos.
                            </p>
                            <p>
                                If you&apos;re building with LLMs and you care about truthfulness, quality, and decision-grade reliability, I&apos;m always open to connect and collaborate.
                            </p>
                        </div>
                    </SectionCard>

                    {/* Links */}
                    <SectionCard>
                        <h2 className="text-xl sm:text-2xl font-bold text-foreground">Links</h2>
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                            {[
                                { icon: Linkedin, label: "LinkedIn", href: "https://www.linkedin.com/in/ateet-vatan-bahmani/" },
                                { icon: Github, label: "GitHub", href: "https://github.com/AteetVatan" },
                                { icon: BookOpen, label: "Blog", href: "https://ateetai.vercel.app/blog" },
                                { icon: Globe, label: "Portfolio", href: "https://ateetai.vercel.app" },
                                { icon: Mail, label: "Email", href: "mailto:ab@masxai.com" },
                            ].map(({ icon: Icon, label, href }) => (
                                <a
                                    key={label}
                                    href={href}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-3 rounded-xl border border-white/[0.08] bg-white/[0.03] px-4 py-3 text-sm text-muted-foreground hover:text-cyan-300 hover:border-cyan-500/25 hover:bg-cyan-500/[0.06] transition-all duration-300"
                                >
                                    <Icon className="w-4 h-4 shrink-0" />
                                    {label}
                                </a>
                            ))}
                        </div>
                    </SectionCard>

                    <div className="h-4" />
                </div>
            </main>
        </div>
    );
}
