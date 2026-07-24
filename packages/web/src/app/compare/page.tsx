import { DecisionBadge } from "@/components/decision-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getSuiteReport } from "@/lib/api";
import { formatMs, formatPercent } from "@/lib/utils";

interface ComparePageProps {
  searchParams: Promise<{ left?: string; right?: string }>;
}

export default async function ComparePage({ searchParams }: ComparePageProps) {
  const { left, right } = await searchParams;

  if (!left || !right) {
    return (
      <div className="space-y-4">
        <h1 className="text-3xl font-semibold tracking-tight">Compare suites</h1>
        <Card>
          <CardHeader>
            <CardTitle>Provide two suite IDs</CardTitle>
            <CardDescription>Use query params: /compare?left=&lt;suite-id&gt;&amp;right=&lt;suite-id&gt;</CardDescription>
          </CardHeader>
        </Card>
      </div>
    );
  }

  let leftReport;
  let rightReport;

  try {
    [leftReport, rightReport] = await Promise.all([getSuiteReport(left), getSuiteReport(right)]);
  } catch {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Unable to load one or both suite reports</CardTitle>
          <CardDescription>Both suites must be completed before comparison.</CardDescription>
        </CardHeader>
      </Card>
    );
  }

  const rows = [
    {
      label: "Decision",
      left: <DecisionBadge decision={leftReport.decision} />,
      right: <DecisionBadge decision={rightReport.decision} />,
    },
    {
      label: "Pass rate",
      left: formatPercent(leftReport.pass_rate),
      right: formatPercent(rightReport.pass_rate),
    },
    {
      label: "Avg latency",
      left: formatMs(leftReport.report.metrics.avg_latency_ms),
      right: formatMs(rightReport.report.metrics.avg_latency_ms),
    },
    {
      label: "Critical failures",
      left: String(leftReport.report.metrics.critical_failure_count),
      right: String(rightReport.report.metrics.critical_failure_count),
    },
  ];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-semibold tracking-tight">Compare suites</h1>
        <p className="mt-2 text-muted-foreground">
          {left.slice(0, 8)}… vs {right.slice(0, 8)}…
        </p>
      </div>

      <Card>
        <CardContent className="overflow-x-auto pt-6">
          <table className="min-w-full text-left text-sm">
            <thead className="border-b border-border text-muted-foreground">
              <tr>
                <th className="px-3 py-2 font-medium">Metric</th>
                <th className="px-3 py-2 font-medium">Left</th>
                <th className="px-3 py-2 font-medium">Right</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((row) => (
                <tr key={row.label} className="border-b border-border/70">
                  <td className="px-3 py-2 font-medium">{row.label}</td>
                  <td className="px-3 py-2">{row.left}</td>
                  <td className="px-3 py-2">{row.right}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
