"use client";

import { useState, useEffect, useCallback } from "react";
import { api } from "@/lib/api";
import type { RunInfo, RunSummary } from "@/lib/types";

/**
 * Polls run info + summary every few seconds until the run is done.
 */
export function useRunData(runId: string | null) {
  const [run, setRun] = useState<RunInfo | null>(null);
  const [summary, setSummary] = useState<RunSummary | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    if (!runId) return;
    try {
      const [r, s] = await Promise.all([
        api.getRun(runId),
        api.getRunSummary(runId),
      ]);
      setRun(r);
      setSummary(s);
    } catch {
      // run may not exist yet
    } finally {
      setLoading(false);
    }
  }, [runId]);

  useEffect(() => {
    refresh();
    const timer = setInterval(refresh, 3000);
    return () => clearInterval(timer);
  }, [refresh]);

  return { run, summary, loading, refresh };
}
