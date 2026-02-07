"use client";

import { useRef, useEffect } from "react";
import type { AgentMessage } from "@/lib/types";

const ROLE_COLORS: Record<string, string> = {
  Orthodox: "text-blue-400",
  Heretic: "text-orange-400",
  Skeptic: "text-purple-400",
  Judge: "text-emerald-400",
};

interface Props {
  messages: AgentMessage[];
}

export function LiveTranscript({ messages }: Props) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages.length]);

  return (
    <div className="card-glow">
      <h2 className="text-lg font-bold text-cyan-400 mb-3">Live Debate</h2>
      <div className="max-h-96 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">Waiting for agents...</p>
        )}
        {messages.map((msg, i) => (
          <div key={i} className="bg-slate-800/50 rounded-lg p-3">
            <div className="flex items-center gap-2 mb-1">
              <span className={`text-xs font-bold ${ROLE_COLORS[msg.role] ?? "text-slate-400"}`}>
                {msg.role}
              </span>
              <span className="text-xs text-slate-600 font-mono">{msg.model_key}</span>
            </div>
            <p className="text-xs text-slate-300 leading-relaxed line-clamp-4">
              {msg.content}
            </p>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  );
}
