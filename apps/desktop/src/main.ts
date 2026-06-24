import path from "node:path";
import {
  AgentPortalRuntime,
  BrowserSession,
  GoalPlanner,
  PortalGraph,
  VisionCore,
  createDefaultWorkspace,
  resolveWorkspaceFileUrl
} from "@agent-portal/core";

async function main(): Promise<void> {
  const repoRoot = path.resolve(process.cwd(), "../..");
  const workspace = createDefaultWorkspace("demo-project");
  const vision = new VisionCore();
  const planner = new GoalPlanner();
  const graph = new PortalGraph();
  const runtime = new AgentPortalRuntime({
    workspace,
    workspaceBasePath: repoRoot,
    agents: [
      { id: "frontend", role: "frontend", status: "idle" },
      { id: "qa", role: "qa", status: "idle" }
    ]
  });

  runtime.record({
    type: "session.started",
    at: new Date().toISOString(),
    detail: `Workspace ${workspace.name} initialized`
  });
  runtime.startAgent("frontend");
  runtime.startAgent("qa");

  const browser = new BrowserSession(runtime, {
    headless: true,
    basePath: repoRoot
  });

  try {
    await browser.launch();
    const localWorkflowUrl = resolveWorkspaceFileUrl(
      repoRoot,
      "apps/desktop/fixtures/local-workflow.html"
    );

    await browser.open(localWorkflowUrl);
    await browser.waitForSelector("#name");
    await browser.hover("#name");
    await browser.type("#name", "Portal Runner");
    await browser.click("#generate-report");
    await browser.scroll({ selector: "#evidence-panel" });
    const result = await browser.readText("#result");
    const capture = await browser.capture({
      label: "local-workflow",
      includeAccessibilityTree: true
    });
    const understanding = vision.analyze({
      snapshot: capture.snapshot,
      goal: "Test the signup flow"
    });
    const goalPlan = planner.createPlan(
      {
        id: "goal-signup-test",
        title: "Test the signup flow"
      },
      understanding
    );
    runtime.addGraphNode(graph.fromSnapshot(capture.snapshot, understanding));
    const projectAwareness = await runtime.detectProjectAwareness(repoRoot);
    await runtime.writeMemoryRecord({
      id: `page-understanding-${Date.now()}`,
      kind: "page-understanding",
      createdAt: new Date().toISOString(),
      summary: understanding.summary,
      payload: {
        understanding,
        goalPlan,
        projectAwareness
      }
    });
    runtime.completeAgent("frontend");
    runtime.completeAgent("qa");
    const reportPath = await runtime.writeSessionReport();
    const overview = runtime.getOverview();

    console.log("Agent Portal browser vertical slice");
    console.log(
      JSON.stringify(
        {
          title: capture.title,
          url: capture.url,
          resultText: result.text,
          pageCategory: understanding.pageCategory,
          understandingSummary: understanding.summary,
          goalSteps: goalPlan.steps.map((step) => step.title),
          projectAwareness: projectAwareness.summary,
          screenshotPath: capture.screenshotPath,
          detectedElements: capture.snapshot.detectedElements.length,
          reportPath,
          events: overview.sessionEvents.length,
          memoryRecords: overview.memoryRecords.length,
          graphNodes: overview.graph.length
        },
        null,
        2
      )
    );
  } finally {
    await browser.close();
  }
}

main().catch((error: unknown) => {
  console.error("Failed to start Agent Portal", error);
  process.exitCode = 1;
});
