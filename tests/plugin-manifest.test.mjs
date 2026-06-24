import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs/promises";
import path from "node:path";
import { validatePluginManifest } from "../packages/core/dist/index.js";

const root = process.cwd();

test("plugin manifests validate", async () => {
  const pluginDirs = [
    "agent-portal-vscode",
    "agent-portal-browser",
    "agent-portal-python",
    "agent-portal-skills"
  ];

  for (const pluginDir of pluginDirs) {
    const raw = await fs.readFile(
      path.join(root, "plugins", pluginDir, "plugin.json"),
      "utf8"
    );
    const manifest = JSON.parse(raw);
    const errors = validatePluginManifest(manifest);
    assert.equal(errors.length, 0, `${pluginDir} manifest failed validation`);
  }
});
