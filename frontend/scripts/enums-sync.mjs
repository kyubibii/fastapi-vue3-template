import { existsSync } from "node:fs";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";
import { spawnSync } from "node:child_process";

const scriptDir = dirname(fileURLToPath(import.meta.url));
const frontendRoot = resolve(scriptDir, "..");
const backendRoot = resolve(frontendRoot, "../backend");
const backendEnumsPath = resolve(backendRoot, "app/constants/enums.py");
const backendExporter = resolve(backendRoot, "scripts/export_enums.py");
const outputPath = resolve(frontendRoot, "src/constants/generated/enums.gen.ts");

if (!existsSync(backendEnumsPath)) {
  console.log(`[enums:sync] backend enums not found at ${backendEnumsPath}, skip generation.`);
  process.exit(0);
}

if (!existsSync(backendExporter)) {
  console.error(`[enums:sync] backend exporter not found at ${backendExporter}`);
  process.exit(0);
}

const result = spawnSync(
  "uv",
  ["run", "python", "scripts/export_enums.py", "--out", outputPath],
  {
    cwd: backendRoot,
    stdio: "inherit",
    shell: process.platform === "win32",
  },
);

if (result.status !== 0) {
  process.exit(result.status ?? 1);
}
