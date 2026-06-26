import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";

const root = process.cwd();

test("VS Code extension package exposes required commands and sidebar", async () => {
  const raw = await fs.readFile(
    path.join(root, "apps", "vscode-extension", "package.json"),
    "utf8"
  );
  const manifest = JSON.parse(raw);
  const commands = manifest.contributes.commands.map((command) => command.command);

  assert.ok(commands.includes("agentPortal.startRuntime"));
  assert.ok(commands.includes("agentPortal.pauseAgent"));
  assert.ok(commands.includes("agentPortal.resumeAgent"));
  assert.ok(commands.includes("agentPortal.approveNextAction"));
  assert.ok(commands.includes("agentPortal.rejectNextAction"));
  assert.ok(manifest.contributes.views.agentPortal.length > 0);
});
