import type { GateReport, Project, RunDetail, RunSummary, Suite } from "@/lib/types";

const DEFAULT_API_URL = "http://localhost:8000";

export function getApiBaseUrl(): string {
  return process.env.AGENTGUARD_API_URL ?? DEFAULT_API_URL;
}

export function getApiKey(): string {
  return process.env.AGENTGUARD_API_KEY ?? "dev-change-me";
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    cache: "no-store",
  });

  if (!response.ok) {
    const detail = await response.text();
    throw new Error(`API ${response.status}: ${detail || response.statusText}`);
  }

  return response.json() as Promise<T>;
}

export async function listProjects(): Promise<Project[]> {
  return fetchJson<Project[]>("/api/v1/projects");
}

export async function getProject(projectId: string): Promise<Project> {
  return fetchJson<Project>(`/api/v1/projects/${projectId}`);
}

export async function listProjectSuites(projectId: string): Promise<Suite[]> {
  return fetchJson<Suite[]>(`/api/v1/projects/${projectId}/suites`);
}

export async function getSuite(suiteId: string): Promise<Suite> {
  return fetchJson<Suite>(`/api/v1/suites/${suiteId}`);
}

export async function listSuiteRuns(suiteId: string): Promise<RunSummary[]> {
  return fetchJson<RunSummary[]>(`/api/v1/suites/${suiteId}/runs`);
}

export async function getRun(runId: string): Promise<RunDetail> {
  return fetchJson<RunDetail>(`/api/v1/runs/${runId}`);
}

export async function getSuiteReport(suiteId: string): Promise<GateReport> {
  return fetchJson<GateReport>(`/api/v1/suites/${suiteId}/report`);
}

export async function startSuite(projectId: string): Promise<Suite> {
  return fetchJson<Suite>(`/api/v1/projects/${projectId}/suites`, {
    method: "POST",
    headers: {
      "X-API-Key": getApiKey(),
    },
    body: "{}",
  });
}
