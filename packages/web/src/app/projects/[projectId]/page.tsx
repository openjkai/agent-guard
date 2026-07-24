import Link from "next/link";
import { notFound } from "next/navigation";

import { DecisionBadge } from "@/components/decision-badge";
import { RunSuiteButton } from "@/components/run-suite-button";
import { StatusBadge, SuiteStats } from "@/components/status-badge";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { getProject, listProjectSuites } from "@/lib/api";
import { formatPercent } from "@/lib/utils";

interface ProjectPageProps {
  params: Promise<{ projectId: string }>;
}

export default async function ProjectPage({ params }: ProjectPageProps) {
  const { projectId } = await params;

  let project;
  let suites;

  try {
    [project, suites] = await Promise.all([getProject(projectId), listProjectSuites(projectId)]);
  } catch {
    notFound();
  }

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm text-muted-foreground">Project</p>
          <h1 className="text-3xl font-semibold tracking-tight">{project.name}</h1>
          <p className="mt-2 max-w-2xl text-muted-foreground">{project.description ?? "No description"}</p>
        </div>
        <RunSuiteButton projectId={project.id} />
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Configuration</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2 text-sm text-muted-foreground">
          <p>Agent: {project.agent_module_path}</p>
          <p>Scenarios: {project.scenarios_path}</p>
        </CardContent>
      </Card>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Suite runs</h2>
        {suites.length === 0 ? (
          <Card>
            <CardContent className="py-6 text-sm text-muted-foreground">No suite runs yet.</CardContent>
          </Card>
        ) : (
          <div className="grid gap-3">
            {suites.map((suite) => (
              <Link key={suite.id} href={`/suites/${suite.id}`}>
                <Card className="transition hover:border-primary/40">
                  <CardHeader className="flex-row items-center justify-between space-y-0">
                    <div>
                      <CardTitle className="text-base">{suite.id.slice(0, 8)}…</CardTitle>
                      <CardDescription>{new Date(suite.created_at).toLocaleString()}</CardDescription>
                    </div>
                    <div className="flex items-center gap-2">
                      <StatusBadge status={suite.status} />
                      <DecisionBadge decision={suite.release_decision} />
                    </div>
                  </CardHeader>
                  <CardContent>
                    <SuiteStats suite={suite} />
                    <p className="mt-2 text-sm text-muted-foreground">Pass rate: {formatPercent(suite.pass_rate)}</p>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
