"use client";

import { useEffect, useRef, useCallback } from "react";
import type { SSEEvent } from "@/lib/types";

/**
 * Hook that connects to an SSE endpoint and dispatches parsed events.
 */
export function useSSE(
  url: string | null,
  onEvent: (event: SSEEvent) => void,
) {
  const cbRef = useRef(onEvent);
  cbRef.current = onEvent;

  useEffect(() => {
    if (!url) return;
    const es = new EventSource(url);

    es.onmessage = (e) => {
      try {
        const data: SSEEvent = JSON.parse(e.data);
        cbRef.current(data);
      } catch {
        // ignore heartbeats and malformed data
      }
    };

    es.onerror = () => {
      // browser auto-reconnects; we just log
      console.warn("SSE connection error, will reconnect...");
    };

    return () => es.close();
  }, [url]);
}
