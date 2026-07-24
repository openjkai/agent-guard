export type ReleaseDecision =
  | "SHIP"
  | "SHIP_WITH_WARNING"
  | "REQUIRE_HUMAN_REVIEW"
  | "BLOCK";

export interface Project {
  id: string;
  name: string;
  description: string | null;
  agent_module_path: string;
  scenarios_path: string;
  config_json: Record<string, unknown>;
  created_at: string;
}

export interface Suite {
  id: string;
  project_id: string;
  status: string;
  pass_rate: number | null;
  release_decision: ReleaseDecision | null;
  progress_completed: number;
  progress_total: number;
  error: string | null;
  created_at: string;
  finished_at: string | null;
}

export interface RunSummary {
  id: string;
  suite_id: string;
  scenario_id: string;
  status: string;
  agent_output: string | null;
  latency_ms: number;
  cost_usd: number;
  passed: boolean;
  created_at: string;
}

export interface EvalResult {
  passed: boolean;
  severity: string;
  reason: string;
  score?: number | null;
  evaluator?: string;
}

export interface TraceStep {
  step_id: string;
  type: string;
  latency_ms: number;
  input: Record<string, unknown>;
  output: Record<string, unknown>;
  usage?: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  } | null;
  cost?: {
    input_usd: number;
    output_usd: number;
    total_usd: number;
  } | null;
  error?: string | null;
}

export interface TraceRun {
  run_id: string;
  scenario_id: string;
  status: string;
  agent_output: string | null;
  steps: TraceStep[];
  usage: {
    input_tokens: number;
    output_tokens: number;
    total_tokens: number;
  };
  cost: {
    input_usd: number;
    output_usd: number;
    total_usd: number;
  };
  latency_ms: number;
  error?: string | null;
}

export interface RunDetail extends RunSummary {
  trace_json: TraceRun;
  evaluations_json: {
    results?: EvalResult[];
  };
}

export interface GateMetrics {
  pass_rate: number;
  avg_cost_usd: number;
  avg_latency_ms: number;
  p95_latency_ms: number;
  critical_failure_count: number;
  major_failure_count: number;
  regression_vs_baseline?: number | null;
}

export interface GateReport {
  suite_id: string;
  decision: ReleaseDecision;
  pass_rate: number | null;
  report: {
    decision: ReleaseDecision;
    suite_id: string;
    metrics: GateMetrics;
    critical_failures: EvalResult[];
    warnings: string[];
    recommended_actions: string[];
    summary: string;
  };
}

export interface ProgressEvent {
  suite_id: string;
  status: string;
  completed: number;
  total: number;
  scenario_id?: string;
  message?: string;
}
