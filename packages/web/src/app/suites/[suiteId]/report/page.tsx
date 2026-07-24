import Link from "next/link";
import { notFound } from "next/navigation";

import { DecisionBadge } from "@/components/decision-badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { getSuiteReport } from "@/lib/api";
import { formatMs, formatPercent } from "@/lib/utils";

interface ReportPageProps {
  params: Promise<{ suiteId: string }>;
}

export default async function ReportPage({ params }: ReportPageProps) {
  const { suiteId } = await params;

  let report;

  try {
    report = await getSuiteReport(suiteId);
  } catch {
    notFound();
  }

  const { metrics } = report.report;

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Release report</p>
          <h1 className="text-3xl font-semibold tracking-tight">Suite {suiteId.slice(0, 8)}…</h1>
          <div className="mt-3">
            <DecisionBadge decision={report.decision} />
          </div>
        </div>
        <Link href={`/suites/${suiteId}`} className="text-sm text-primary hover:underline">
          Back to suite
        </Link>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Summary</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <p>{report.report.summary}</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <Metric label="Pass rate" value={formatPercent(report.pass_rate)} />
            <Metric label="Avg latency" value={formatMs(metrics.avg_latency_ms)} />
            <Metric label="P95 latency" value={formatMs(metrics.p95_latency_ms)} />
            <Metric label="Critical failures" value={String(metrics.critical_failure_count)} />
          </div>
        </CardContent>
      </Card>

      {report.report.warnings.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Warnings</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-5 text-sm">
              {report.report.warnings.map((warning) => (
                <li key={warning}>{warning}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}

      {report.report.critical_failures.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Critical failures</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {report.report.critical_failures.map((failure, index) => (
              <div key={`${failure.reason}-${index}`} className="rounded-md border border-border p-3 text-sm">
                <p className="font-medium">{failure.evaluator ?? "Evaluator"}</p>
                <p className="text-muted-foreground">{failure.reason}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      ) : null}

      {report.report.recommended_actions.length > 0 ? (
        <Card>
          <CardHeader>
            <CardTitle>Recommended actions</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc space-y-2 pl-5 text-sm">
              {report.report.recommended_actions.map((action) => (
                <li key={action}>{action}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      ) : null}
    </div>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-muted/30 px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}
