import Link from "next/link";
import { notFound } from "next/navigation";

import { DecisionBadge } from "@/components/decision-badge";
import { SuiteProgress } from "@/components/suite-progress";
import { StatusBadge } from "@/components/status-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getSuite, listSuiteRuns } from "@/lib/api";
import { formatMs, formatPercent, formatUsd } from "@/lib/utils";

interface SuitePageProps {
  params: Promise<{ suiteId: string }>;
}

export default async function SuitePage({ params }: SuitePageProps) {
  const { suiteId } = await params;

  let suite;
  let runs;

  try {
    [suite, runs] = await Promise.all([getSuite(suiteId), listSuiteRuns(suiteId)]);
  } catch {
    notFound();
  }

  const failures = runs.filter((run) => !run.passed);

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Suite</p>
          <h1 className="text-3xl font-semibold tracking-tight">{suiteId.slice(0, 8)}…</h1>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <StatusBadge status={suite.status} />
            <DecisionBadge decision={suite.release_decision} />
          </div>
        </div>
        <div className="flex gap-3 text-sm">
          <Link href={`/projects/${suite.project_id}`} className="text-primary hover:underline">
            Back to project
          </Link>
          {suite.status === "completed" ? (
            <Link href={`/suites/${suiteId}/report`} className="text-primary hover:underline">
              Release report
            </Link>
          ) : null}
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Progress</CardTitle>
        </CardHeader>
        <CardContent>
          <SuiteProgress
            suiteId={suite.id}
            initialStatus={suite.status}
            initialCompleted={suite.progress_completed}
            initialTotal={suite.progress_total}
          />
          <p className="mt-4 text-sm text-muted-foreground">Pass rate: {formatPercent(suite.pass_rate)}</p>
          {suite.error ? <p className="mt-2 text-sm text-destructive">{suite.error}</p> : null}
        </CardContent>
      </Card>

      {failures.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Failures ({failures.length})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2">
            {failures.map((run) => (
              <Link
                key={run.id}
                href={`/runs/${run.id}`}
                className="flex items-center justify-between rounded-md border border-border px-3 py-2 text-sm hover:border-destructive/40"
              >
                <span>{run.scenario_id}</span>
                <span className="text-muted-foreground">{formatMs(run.latency_ms)}</span>
              </Link>
            ))}
          </CardContent>
        </Card>
      ) : null}

      <Card>
        <CardHeader>
          <CardTitle>All runs ({runs.length})</CardTitle>
        </CardHeader>
        <CardContent className="overflow-x-auto">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border text-muted-foreground">
              <tr>
                <th className="px-2 py-2 font-medium">Scenario</th>
                <th className="px-2 py-2 font-medium">Result</th>
                <th className="px-2 py-2 font-medium">Latency</th>
                <th className="px-2 py-2 font-medium">Cost</th>
              </tr>
            </thead>
            <tbody>
              {runs.map((run) => (
                <tr key={run.id} className="border-b border-border/70">
                  <td className="px-2 py-2">
                    <Link href={`/runs/${run.id}`} className="text-primary hover:underline">
                      {run.scenario_id}
                    </Link>
                  </td>
                  <td className="px-2 py-2">{run.passed ? "Pass" : "Fail"}</td>
                  <td className="px-2 py-2">{formatMs(run.latency_ms)}</td>
                  <td className="px-2 py-2">{formatUsd(run.cost_usd)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
