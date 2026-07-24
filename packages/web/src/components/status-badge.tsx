import type { Suite } from "@/lib/types";
import { cn, formatPercent } from "@/lib/utils";

interface StatusBadgeProps {
  status: Suite["status"];
  className?: string;
}

const styles: Record<string, string> = {
  pending: "bg-muted text-muted-foreground",
  queued: "bg-secondary text-secondary-foreground",
  running: "bg-primary/15 text-primary",
  completed: "bg-success/15 text-success",
  failed: "bg-destructive/15 text-destructive",
};

export function StatusBadge({ status, className }: StatusBadgeProps) {
  return (
    <span className={cn("rounded-full px-2.5 py-1 text-xs font-medium capitalize", styles[status] ?? styles.pending, className)}>
      {status}
    </span>
  );
}

interface SuiteStatsProps {
  suite: Suite;
}

export function SuiteStats({ suite }: SuiteStatsProps) {
  return (
    <div className="flex flex-wrap gap-4 text-sm text-muted-foreground">
      <span>Progress: {suite.progress_completed}/{suite.progress_total}</span>
      <span>Pass rate: {formatPercent(suite.pass_rate)}</span>
    </div>
  );
}
