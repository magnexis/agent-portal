import test from "node:test";
import assert from "node:assert/strict";
import path from "node:path";
import {
  AgentPortalRuntime,
  BrowserSession,
  createDefaultWorkspace,
  resolveWorkspaceFileUrl
} from "../packages/core/dist/index.js";

const root = process.cwd();

test("runtime launches browser, executes workflow, captures report, and shuts down", async () => {
  const workspace = createDefaultWorkspace("test-project");
  const runtime = new AgentPortalRuntime({
    workspace,
    workspaceBasePath: root,
    agents: [{ id: "qa", role: "qa", status: "idle" }]
  });
  const session = new BrowserSession(runtime, {
    headless: true,
    basePath: root
  });

  await session.launch();
  await session.open(
    resolveWorkspaceFileUrl(root, "apps/desktop/fixtures/local-workflow.html")
  );
  await session.waitForSelector("#name");
  await session.type("#name", "Runtime Test");
  await session.click("#generate-report");
  const text = await session.readText("#result");
  const capture = await session.capture({ label: "runtime-test" });
  const reportPath = await runtime.writeSessionReport();
  await session.shutdownGracefully();

  assert.match(text.text ?? "", /Runtime Test/);
  assert.equal(capture.snapshot.detectedElements.length > 0, true);
  assert.match(reportPath, /session-/);
  assert.equal(runtime.getOverview().browserStatus, "closed");
});
