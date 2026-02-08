"use client";

import { useRef, useEffect } from "react";
import type { AgentMessage } from "@/lib/types";
import { parseStructuredMessage } from "@/lib/messageParser";
import { formatStructuredMessage } from "@/lib/messageFormatter";
import { ROLE_COLORS } from "@/lib/constants";

interface Props {
  messages: AgentMessage[];
}

export function LiveTranscript({ messages }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    // Only scroll within the container, not the entire page
    if (containerRef.current) {
      const container = containerRef.current;
      // Scroll to bottom of container smoothly
      container.scrollTo({
        top: container.scrollHeight,
        behavior: "smooth",
      });
    }
  }, [messages.length]);

  return (
    <div className="card-glow">
      <h2 className="text-lg font-bold text-cyan-400 mb-3">Live Debate</h2>
      <div ref={containerRef} className="max-h-96 overflow-y-auto space-y-3 pr-1">
        {messages.length === 0 && (
          <p className="text-sm text-slate-500">Waiting for agents...</p>
        )}
        {messages.map((msg, i) => {
          // Try to parse structured message (JSON or TOML)
          const parsed = parseStructuredMessage(msg.content, msg.phase);

          if (parsed) {
            return (
              <div key={i} className="bg-slate-800/50 rounded-lg p-3">
                {formatStructuredMessage(parsed, msg.role, msg.model_key)}
              </div>
            );
          }

          // Fallback to regular message display
          return (
            <div key={i} className="bg-slate-800/50 rounded-lg p-3">
              <div className="flex items-center gap-2 mb-1">
                <span
                  className={`text-xs font-bold ${ROLE_COLORS[msg.role] ?? "text-slate-400"}`}
                >
                  {msg.role}
                </span>
                <span className="text-xs text-slate-600 font-mono">
                  {msg.model_key}
                </span>
              </div>
              <p className="text-xs text-slate-300 leading-relaxed line-clamp-4">
                {msg.content}
              </p>
            </div>
          );
        })}
      </div>
    </div>
  );
}
