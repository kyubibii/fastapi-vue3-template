import { spawnSync } from "node:child_process";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");

const sync = spawnSync("pnpm", ["run", "enums:sync"], {
  cwd: frontendRoot,
  stdio: "inherit",
  shell: process.platform === "win32",
});

if (sync.status !== 0) {
  process.exit(sync.status ?? 1);
}

const diff = spawnSync("git", ["diff", "--exit-code", "--", "src/constants/generated/enums.gen.ts"], {
  cwd: frontendRoot,
  stdio: "inherit",
  shell: process.platform === "win32",
});

if (diff.status !== 0) {
  console.error("[enums:check] generated enums file is out of date. Please run pnpm run enums:sync and commit the result.");
  process.exit(diff.status ?? 1);
}

console.log("[enums:check] enums are in sync.");
