import type { TraceRun, TraceStep } from "@/lib/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { formatMs, formatUsd } from "@/lib/utils";

interface TraceViewerProps {
  trace: TraceRun;
}

function StepDetails({ step }: { step: TraceStep }) {
  const inputPreview =
    step.type === "tool"
      ? `${String(step.input.tool_name ?? "tool")}(${JSON.stringify(step.input.arguments ?? {})})`
      : step.type === "llm"
        ? String(step.input.prompt ?? step.input.messages ?? "LLM call")
        : step.type === "retrieval"
          ? String(step.input.query ?? "Retrieval")
          : JSON.stringify(step.input);

  return (
    <div className="rounded-md border border-border bg-muted/40 p-3">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <div className="flex items-center gap-2">
          <span className="rounded bg-background px-2 py-0.5 text-xs font-semibold uppercase tracking-wide">
            {step.type}
          </span>
          <span className="text-xs text-muted-foreground">{formatMs(step.latency_ms)}</span>
        </div>
        <div className="text-xs text-muted-foreground">
          {step.usage ? `${step.usage.total_tokens} tok` : null}
          {step.cost ? ` · ${formatUsd(step.cost.total_usd)}` : null}
        </div>
      </div>
      <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-xs text-foreground">{inputPreview}</pre>
      {step.output && Object.keys(step.output).length > 0 ? (
        <pre className="mt-2 overflow-x-auto whitespace-pre-wrap break-words text-xs text-muted-foreground">
          {JSON.stringify(step.output, null, 2)}
        </pre>
      ) : null}
      {step.error ? <p className="mt-2 text-xs text-destructive">{step.error}</p> : null}
    </div>
  );
}

export function TraceViewer({ trace }: TraceViewerProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Trace</CardTitle>
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="grid gap-3 sm:grid-cols-3">
          <Metric label="Latency" value={formatMs(trace.latency_ms)} />
          <Metric label="Tokens" value={String(trace.usage.total_tokens)} />
          <Metric label="Cost" value={formatUsd(trace.cost.total_usd)} />
        </div>
        <div className="space-y-3">
          {trace.steps.map((step) => (
            <StepDetails key={step.step_id} step={step} />
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-md border border-border bg-background px-3 py-2">
      <p className="text-xs text-muted-foreground">{label}</p>
      <p className="text-sm font-medium">{value}</p>
    </div>
  );
}
