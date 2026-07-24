import type { ReleaseDecision } from "@/lib/types";
import { cn } from "@/lib/utils";

const styles: Record<ReleaseDecision, string> = {
  SHIP: "bg-success/15 text-success",
  SHIP_WITH_WARNING: "bg-warning/15 text-warning",
  REQUIRE_HUMAN_REVIEW: "bg-warning/15 text-warning",
  BLOCK: "bg-destructive/15 text-destructive",
};

interface DecisionBadgeProps {
  decision: ReleaseDecision | string | null | undefined;
  className?: string;
}

export function DecisionBadge({ decision, className }: DecisionBadgeProps) {
  if (!decision) {
    return (
      <span className={cn("rounded-full bg-muted px-2.5 py-1 text-xs font-medium text-muted-foreground", className)}>
        Pending
      </span>
    );
  }

  const tone = styles[decision as ReleaseDecision] ?? "bg-muted text-muted-foreground";

  return (
    <span className={cn("rounded-full px-2.5 py-1 text-xs font-semibold tracking-wide", tone, className)}>
      {decision}
    </span>
  );
}
