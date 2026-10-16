import { readdir, readFile, mkdir, writeFile } from "node:fs/promises"
import { join, resolve, dirname } from "node:path"
import { compileRepository, jsonBytes } from "./compiler.ts"

const args = process.argv.slice(2)
const flags = new Map<string, string>()
for (let index = 0; index < args.length; index += 2) {
  const key = args[index]
  const value = args[index + 1]
  if (
    !key ||
    !["--input-dir", "--output-dir", "--compiler-revision", "--site"].includes(key) ||
    !value ||
    flags.has(key)
  )
    throw new Error(
      "usage: cli.ts --input-dir PATH --output-dir PATH --compiler-revision REV [--site URL]",
    )
  flags.set(key, value)
}
function required(key: string): string {
  const value = flags.get(key)
  if (!value) throw new Error(`${key} is required`)
  return value
}
const inputDir = resolve(required("--input-dir"))
const outputDir = resolve(required("--output-dir"))
if (
  outputDir === inputDir ||
  outputDir.startsWith(inputDir + "/") ||
  inputDir.startsWith(outputDir + "/")
)
  throw new Error("input and output directories must be separate")
const inputs = await Promise.all(
  (await readdir(inputDir))
    .filter((name) => /^x-ai-\d{4}-\d{2}-\d{2}\.md$/.test(name))
    .sort()
    .map(async (filename) => ({
      filename,
      text: await readFile(join(inputDir, filename), "utf8"),
    })),
)
if (!inputs.length) throw new Error("no accepted editions found")
const exported = compileRepository(inputs, {
  compilerRevision: required("--compiler-revision"),
  site: flags.get("--site"),
})
for (const object of exported.objects) {
  const path = join(outputDir, object.key)
  await mkdir(dirname(path), { recursive: true })
  await writeFile(path, object.bytes)
}
await mkdir(join(outputDir, "v1"), { recursive: true })
await writeFile(join(outputDir, "v1/head.json"), jsonBytes(exported.head))
process.stdout.write(
  jsonBytes({ ...exported, objects: exported.objects.map(({ bytes: _bytes, ...ref }) => ref) }),
)
