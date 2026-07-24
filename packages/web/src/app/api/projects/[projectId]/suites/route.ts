import { NextResponse } from "next/server";

import { startSuite } from "@/lib/api";

interface RouteContext {
  params: Promise<{ projectId: string }>;
}

export async function POST(_request: Request, context: RouteContext): Promise<NextResponse> {
  const { projectId } = await context.params;

  try {
    const suite = await startSuite(projectId);
    return NextResponse.json(suite, { status: 202 });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Failed to start suite";
    return NextResponse.json({ detail: message }, { status: 500 });
  }
}
