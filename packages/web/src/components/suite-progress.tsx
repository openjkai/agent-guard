"use client";

import { useEffect, useState } from "react";

import type { ProgressEvent } from "@/lib/types";
import { StatusBadge } from "@/components/status-badge";

interface SuiteProgressProps {
  suiteId: string;
  initialStatus: string;
  initialCompleted: number;
  initialTotal: number;
}

export function SuiteProgress({
  suiteId,
  initialStatus,
  initialCompleted,
  initialTotal,
}: SuiteProgressProps) {
  const [event, setEvent] = useState<ProgressEvent>({
    suite_id: suiteId,
    status: initialStatus,
    completed: initialCompleted,
    total: initialTotal,
    message: "",
  });

  useEffect(() => {
    if (initialStatus === "completed" || initialStatus === "failed") {
      return;
    }

    const apiUrl = process.env.NEXT_PUBLIC_AGENTGUARD_API_URL ?? "http://localhost:8000";
    const source = new EventSource(`${apiUrl}/api/v1/suites/${suiteId}/events`);

    source.onmessage = (message) => {
      try {
        const payload = JSON.parse(message.data) as ProgressEvent;
        setEvent(payload);
        if (payload.status === "completed" || payload.status === "failed") {
          source.close();
          window.location.reload();
        }
      } catch {
        // Ignore malformed SSE payloads.
      }
    };

    return () => {
      source.close();
    };
  }, [suiteId, initialStatus]);

  const percent = event.total > 0 ? Math.round((event.completed / event.total) * 100) : 0;

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-3">
        <StatusBadge status={event.status} />
        <span className="text-sm text-muted-foreground">
          {event.completed}/{event.total} scenarios ({percent}%)
        </span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-muted">
        <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${percent}%` }} />
      </div>
      {event.message ? <p className="text-sm text-muted-foreground">{event.message}</p> : null}
    </div>
  );
}
