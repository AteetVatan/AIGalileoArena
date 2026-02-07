"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { api } from "@/lib/api";
import { CaseReplay } from "@/components/CaseReplay";

export default function CaseReplayPage() {
  const { runId, caseId } = useParams<{ runId: string; caseId: string }>();
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (runId && caseId) {
      api.getCaseReplay(runId, caseId).then(setData).catch(console.error);
    }
  }, [runId, caseId]);

  if (!data) return <div className="text-slate-400 py-10">Loading replay...</div>;

  return <CaseReplay data={data} />;
}
