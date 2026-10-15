import assert from "node:assert/strict"
import { execFileSync } from "node:child_process"
import { mkdtempSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import { test } from "node:test"

const app = resolve(import.meta.dirname, "..")

test("private publisher validation accepts the shared v2 fixture and rejects an unsafe extra link", () => {
  const folder = mkdtempSync(join(tmpdir(), "daily-validation-"))
  try {
    const path = join(folder, "x-ai-2026-10-15.md")
    const accepted = readFileSync(join(app, "tests/fixtures/editorial-v2-four-stories.md"), "utf8")
    writeFileSync(path, accepted)
    const validate = () =>
      execFileSync(process.execPath, ["--import", "tsx", "scripts/validate-edition.ts", path], {
        cwd: app,
        stdio: "pipe",
      })
    assert.doesNotThrow(validate)
    writeFileSync(
      path,
      accepted.replace("Vendor claim.", "Vendor claim. [unsafe](javascript:alert(1))"),
    )
    assert.throws(validate)
  } finally {
    rmSync(folder, { recursive: true, force: true })
  }
})
