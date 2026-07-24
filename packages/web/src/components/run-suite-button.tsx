"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { Button } from "@/components/ui/button";

interface RunSuiteButtonProps {
  projectId: string;
}

export function RunSuiteButton({ projectId }: RunSuiteButtonProps) {
  const router = useRouter();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleClick() {
    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`/api/projects/${projectId}/suites`, {
        method: "POST",
      });

      if (!response.ok) {
        const detail = await response.text();
        throw new Error(detail || "Failed to start suite");
      }

      const suite = (await response.json()) as { id: string };
      router.push(`/suites/${suite.id}`);
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to start suite");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-2">
      <Button disabled={loading} onClick={handleClick}>
        {loading ? "Starting…" : "Run suite"}
      </Button>
      {error ? <p className="text-sm text-destructive">{error}</p> : null}
    </div>
  );
}
