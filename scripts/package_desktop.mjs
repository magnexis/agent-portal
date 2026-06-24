import { copyFile, mkdir, readdir, readFile, rm, stat, writeFile } from "node:fs/promises";
import path from "node:path";
import { execFile } from "node:child_process";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);

const repoRoot = process.cwd();
const desktopRoot = path.join(repoRoot, "apps", "desktop");
const stagingRoot = path.join(repoRoot, "releases", "desktop", "agent-portal-desktop");
const outputDir = path.join(repoRoot, "releases", "desktop");
const archivePath = path.join(outputDir, "agent-portal-desktop.zip");

async function main() {
  await ensureDesktopBuild();
  await rm(stagingRoot, { recursive: true, force: true });
  await mkdir(stagingRoot, { recursive: true });

  await copyTree(path.join(desktopRoot, "dist"), path.join(stagingRoot, "dist"));
  await copyTree(path.join(desktopRoot, "fixtures"), path.join(stagingRoot, "fixtures"));
  await copyTree(path.join(repoRoot, "assets", "branding"), path.join(stagingRoot, "assets", "branding"));
  await copyOptionalTree(
    path.join(repoRoot, "workspaces", "runtime"),
    path.join(stagingRoot, "runtime-workspaces")
  );
  await copyFile(path.join(repoRoot, "README.md"), path.join(stagingRoot, "README.md"));
  await writeLaunchScript();
  await writeReleaseNotes();
  await zipWithPowerShell(stagingRoot, archivePath);

  console.log(`Desktop release package written to ${archivePath}`);
}

async function ensureDesktopBuild() {
  await execFileAsync("npm", ["run", "build", "--workspace", "@agent-portal/desktop"], {
    cwd: repoRoot,
    shell: process.platform === "win32"
  });
}

async function copyOptionalTree(source, destination) {
  try {
    await stat(source);
    await copyTree(source, destination);
  } catch {
    return;
  }
}

async function copyTree(source, destination) {
  const sourceStats = await stat(source);
  if (!sourceStats.isDirectory()) {
    throw new Error(`Expected directory: ${source}`);
  }

  await mkdir(destination, { recursive: true });
  const entries = await readdir(source, { withFileTypes: true });

  for (const entry of entries) {
    const sourcePath = path.join(source, entry.name);
    const destinationPath = path.join(destination, entry.name);

    if (entry.isDirectory()) {
      await copyTree(sourcePath, destinationPath);
      continue;
    }

    await copyFile(sourcePath, destinationPath);
  }
}

async function writeLaunchScript() {
  const launchScript = `@echo off
setlocal
cd /d "%~dp0"
node dist\\main.js
`;
  await writeFile(path.join(stagingRoot, "launch-agent-portal.bat"), launchScript, "utf8");
}

async function writeReleaseNotes() {
  const desktopPackageJson = JSON.parse(
    await readFile(path.join(desktopRoot, "package.json"), "utf8")
  );
  const notes = `# Agent Portal Desktop Runtime Package

Version: ${desktopPackageJson.version}

Included:
- desktop runtime build output
- local workflow fixtures
- shared branding assets
- launch-agent-portal.bat helper

Usage:
1. Ensure Node.js is installed on the target machine.
2. Open a terminal in this package directory.
3. Run \`launch-agent-portal.bat\`.
`;
  await writeFile(path.join(stagingRoot, "RELEASE_NOTES.md"), notes, "utf8");
}

async function zipWithPowerShell(sourceDirectory, destinationZip) {
  await mkdir(path.dirname(destinationZip), { recursive: true });
  const command = [
    "-NoProfile",
    "-Command",
    `Compress-Archive -Path '${sourceDirectory}\\*' -DestinationPath '${destinationZip}' -Force`
  ];
  await execFileAsync("powershell", command, { cwd: repoRoot });
}

main().catch((error) => {
  console.error("Desktop release packaging failed.");
  console.error(error);
  process.exitCode = 1;
});
