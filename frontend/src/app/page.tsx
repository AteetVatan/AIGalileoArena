import Link from "next/link";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6">
      <h1 className="text-5xl font-bold bg-gradient-to-r from-cyan-400 to-blue-500 bg-clip-text text-transparent">
        Galileo Arena
      </h1>
      <p className="text-lg text-slate-400 max-w-xl">
        Multi-model agentic debate platform. Pick a dataset, select LLM models,
        and watch Orthodox, Heretic, Skeptic &amp; Judge agents duke it out live.
      </p>
      <Link
        href="/datasets"
        className="mt-4 px-6 py-3 bg-cyan-600 hover:bg-cyan-500 rounded-lg font-medium transition"
      >
        Get Started
      </Link>
    </div>
  );
}
