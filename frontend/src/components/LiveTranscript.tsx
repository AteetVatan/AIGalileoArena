"use client";

import { useRef, useEffect, useState } from "react";
import type { AgentMessage } from "@/lib/types";
import { parseStructuredMessage } from "@/lib/messageParser";
import { formatStructuredMessage } from "@/lib/messageFormatter";
import { ROLE_COLORS } from "@/lib/constants";

interface Props {
  messages: AgentMessage[];
}

function getAvatarInitial(role: string): string {
  const roleMap: Record<string, string> = {
    Orthodox: "O",
    Heretic: "H",
    Skeptic: "S",
    Judge: "J",
  };
  return roleMap[role] || role[0]?.toUpperCase() || "?";
}

function getAvatarGradient(role: string): string {
  const gradientMap: Record<string, string> = {
    Orthodox: "from-blue-400 to-cyan-500",
    Heretic: "from-pink-500 to-purple-600",
    Skeptic: "from-purple-400 to-indigo-500",
    Judge: "from-emerald-400 to-teal-500",
  };
  return gradientMap[role] || "from-gray-400 to-gray-500";
}

function shouldAlignRight(role: string): boolean {
  return role === "Heretic";
}

export function LiveTranscript({ messages }: Props) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [highlightedIndex, setHighlightedIndex] = useState<number | null>(null);
  const prevMessageCountRef = useRef(messages.length);
  const messageRefs = useRef<Map<number, HTMLDivElement>>(new Map());

  useEffect(() => {
    // Highlight new message if count increased
    if (messages.length > prevMessageCountRef.current && messages.length > 0) {
      const newMessageIndex = messages.length - 1;
      setHighlightedIndex(newMessageIndex);

      // Scroll to the new message element
      setTimeout(() => {
        const newMessageElement = messageRefs.current.get(newMessageIndex);
        if (newMessageElement) {
          newMessageElement.scrollIntoView({
            behavior: "smooth",
            block: "nearest",
            inline: "nearest"
          });
        }
      }, 100);

      // Remove highlight after 3 seconds
      setTimeout(() => {
        setHighlightedIndex(null);
      }, 3000);
    }

    prevMessageCountRef.current = messages.length;
  }, [messages.length]);

  return (
    <div className="glass-panel rounded-3xl p-8 relative overflow-hidden flex flex-col">
      {/* Scroll fade mask at top */}
      <div className="absolute top-0 left-0 right-0 h-12 bg-gradient-to-b from-[rgba(255,255,255,0.05)] to-transparent z-10 pointer-events-none"></div>

      <h2 className="text-lg font-medium text-cyan-300 mb-6">Live Debate</h2>
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto space-y-8 pr-2 relative z-0 hide-scrollbar"
      >
        {messages.length === 0 && (
          <p className="text-sm text-white/50 text-center py-12">Waiting for agents...</p>
        )}
        {messages.map((msg, i) => {
          const alignRight = shouldAlignRight(msg.role);
          const avatarInitial = getAvatarInitial(msg.role);
          const avatarGradient = getAvatarGradient(msg.role);
          const roleColor = ROLE_COLORS[msg.role] ?? "text-white/60";

          // Try to parse structured message (JSON or TOML)
          const parsed = parseStructuredMessage(msg.content, msg.phase);
          const isHighlighted = highlightedIndex === i;

          return (
            <div
              key={i}
              ref={(el) => {
                if (el) {
                  messageRefs.current.set(i, el);
                } else {
                  messageRefs.current.delete(i);
                }
              }}
              className={`flex gap-4 items-start group ${alignRight ? "flex-row-reverse" : ""} transition-all duration-500 ${isHighlighted
                  ? "animate-in fade-in slide-in-from-bottom-2 duration-500"
                  : ""
                }`}
            >
              {/* Avatar */}
              <div
                className={`w-10 h-10 rounded-full bg-gradient-to-br ${avatarGradient} flex items-center justify-center text-xs font-bold shadow-glow mt-1 flex-shrink-0`}
              >
                {avatarInitial}
              </div>

              {/* Message bubble */}
              <div
                className={`bg-white/10 border p-5 rounded-2xl backdrop-blur-sm group-hover:bg-white/15 transition-all ${alignRight ? "rounded-tr-none text-right" : "rounded-tl-none"
                  } ${isHighlighted
                    ? "border-cyan-400/60 bg-cyan-500/10 shadow-[0_0_30px_rgba(34,211,238,0.4)] ring-2 ring-cyan-400/30 scale-[1.02]"
                    : "border-white/5"
                  } max-w-2xl`}
              >
                <div
                  className={`flex justify-between items-baseline mb-2 ${alignRight ? "flex-row-reverse" : ""
                    }`}
                >
                  <span className={`${roleColor} font-medium text-sm`}>
                    {msg.role} Agent
                  </span>
                  <span className="text-[10px] text-white/30">
                    {i === messages.length - 1 ? "Just now" : `${messages.length - i - 1}s ago`}
                  </span>
                </div>

                {parsed ? (
                  <div className="text-white/90">{formatStructuredMessage(parsed, msg.role, msg.model_key)}</div>
                ) : (
                  <p className="text-lg font-light leading-relaxed text-white/90">
                    {msg.content}
                  </p>
                )}
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
