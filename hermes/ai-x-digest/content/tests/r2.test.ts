import assert from "node:assert/strict"
import { createServer } from "node:http"
import { chmod, mkdtemp, mkdir, readFile, realpath, rm, symlink, writeFile } from "node:fs/promises"
import { tmpdir } from "node:os"
import { dirname, join } from "node:path"
import { spawnSync } from "node:child_process"
import test, { type TestContext } from "node:test"
import { S3Client } from "@aws-sdk/client-s3"
import { compileRepository, jsonBytes } from "../compiler.ts"
import { inspect, publishBundle, S3Store, verifyBundleObjects } from "../r2.ts"

async function fixture(t: TestContext) {
  const directory = await mkdtemp(join(tmpdir(), "daily-r2-"))
  const text = await readFile(
    new URL("../../../../apps/daily/tests/fixtures/editorial-v2-four-stories.md", import.meta.url),
    "utf8",
  )
  const compiled = compileRepository([{ filename: "x-ai-2026-10-15.md", text }], {
    compilerRevision: "test-compiler",
  })
  for (const object of compiled.objects) {
    await mkdir(dirname(join(directory, object.key)), { recursive: true })
    await writeFile(join(directory, object.key), object.bytes)
  }
  await writeFile(join(directory, "v1/head.json"), jsonBytes(compiled.head))
  await writeFile(
    join(directory, "bundle.json"),
    jsonBytes({ ...compiled, objects: compiled.objects.map(({ bytes: _bytes, ...ref }) => ref) }),
  )
  const objects = new Map<string, { bytes: Buffer; etag: string }>()
  const writes: { key: string; match: string | undefined; absent: string | undefined }[] = []
  let generation = 0
  const faults = { lostObject: false, lostHead: false, corruptObject: false }
  const server = createServer((request, response) => {
    void (async () => {
      const key = decodeURIComponent(
        new URL(request.url ?? "/", "http://127.0.0.1").pathname.replace(/^\/fixture\//, ""),
      )
      if (request.method === "GET") {
        const object = objects.get(key)
        if (!object) {
          response.writeHead(404, { "content-type": "application/xml" })
          response.end("<Error><Code>NoSuchKey</Code></Error>")
          return
        }
        response.writeHead(200, { ETag: object.etag })
        response.end(faults.corruptObject && key !== "v1/head.json" ? "corrupt" : object.bytes)
        return
      }
      const chunks: Buffer[] = []
      for await (const chunk of request) chunks.push(Buffer.from(chunk))
      const match = request.headers["if-match"]
      const absent = request.headers["if-none-match"]
      if (Array.isArray(match) || Array.isArray(absent)) throw new Error("duplicate condition")
      writes.push({ key, match, absent })
      const old = objects.get(key)
      if ((absent === "*" && old) || (match !== undefined && old?.etag !== match)) {
        response.writeHead(412, { "content-type": "application/xml" })
        response.end("<Error><Code>PreconditionFailed</Code></Error>")
        return
      }
      const object = { bytes: Buffer.concat(chunks), etag: `"opaque-${++generation}"` }
      objects.set(key, object)
      if (
        (key === "v1/head.json" && faults.lostHead) ||
        (key !== "v1/head.json" && faults.lostObject)
      ) {
        faults.lostHead = false
        faults.lostObject = false
        response.destroy()
        return
      }
      response.writeHead(200, { ETag: object.etag })
      response.end()
    })().catch((error: unknown) => {
      response.destroy(error instanceof Error ? error : undefined)
    })
  })
  await new Promise<void>((resolve) => server.listen(0, "127.0.0.1", resolve))
  const address = server.address()
  if (!address || typeof address === "string") throw new Error("missing fixture address")
  const client = new S3Client({
    region: "auto",
    endpoint: `http://127.0.0.1:${address.port}`,
    forcePathStyle: true,
    credentials: { accessKeyId: "fixture", secretAccessKey: "fixture" },
    maxAttempts: 1,
    requestChecksumCalculation: "WHEN_REQUIRED",
    responseChecksumValidation: "WHEN_REQUIRED",
  })
  t.after(async () => {
    client.destroy()
    await new Promise<void>((resolve) => server.close(() => resolve()))
    await rm(directory, { recursive: true, force: true })
  })
  return { directory, compiled, objects, writes, faults, store: new S3Store(client, "fixture") }
}
const absent = { manifestSha256: null, etag: null }

test("the pinned SDK creates immutable objects and writes head last with atomic absence", async (t) => {
  const f = await fixture(t)
  await verifyBundleObjects(f.store, f.directory, absent)
  assert.equal(f.objects.has("v1/head.json"), false)
  await publishBundle(f.store, f.directory, absent)
  assert.equal(f.writes.at(-1)?.key, "v1/head.json")
  assert.ok(f.writes.every((write) => write.absent === "*" && write.match === undefined))
  const selected = await inspect(f.store)
  assert.equal(selected.head?.manifest.sha256, f.compiled.head.manifest.sha256)
  assert.ok(selected.etag?.startsWith('"opaque-'))
  const count = f.writes.length
  await publishBundle(f.store, f.directory, absent)
  assert.equal(f.writes.length, count)
})

test("lost immutable and head responses reconcile by exact readback", async (t) => {
  const f = await fixture(t)
  f.faults.lostObject = true
  f.faults.lostHead = true
  const selected = await publishBundle(f.store, f.directory, absent)
  assert.equal(selected.head?.manifest.sha256, f.compiled.head.manifest.sha256)
})

test("head CAS uses its opaque predecessor ETag", async (t) => {
  const f = await fixture(t)
  const other = compileRepository(
    [
      {
        filename: "x-ai-2026-10-15.md",
        text: await readFile(
          new URL("../../../../apps/daily/tests/fixtures/editorial-v1.md", import.meta.url),
          "utf8",
        ),
      },
    ],
    { compilerRevision: "old" },
  )
  for (const object of other.objects)
    f.objects.set(object.key, { bytes: Buffer.from(object.bytes), etag: '"immutable"' })
  f.objects.set("v1/head.json", {
    bytes: Buffer.from(jsonBytes(other.head)),
    etag: '"predecessor"',
  })
  await publishBundle(f.store, f.directory, {
    manifestSha256: other.head.manifest.sha256,
    etag: '"predecessor"',
  })
  assert.equal(f.writes.at(-1)?.match, '"predecessor"')
  assert.equal(f.writes.at(-1)?.absent, undefined)
})

test("an unexpected newer head blocks every write", async (t) => {
  const f = await fixture(t)
  const newer = compileRepository(
    [
      {
        filename: "x-ai-2026-10-15.md",
        text: await readFile(
          new URL("../../../../apps/daily/tests/fixtures/editorial-v1.md", import.meta.url),
          "utf8",
        ),
      },
    ],
    { compilerRevision: "newer" },
  )
  for (const object of newer.objects)
    f.objects.set(object.key, { bytes: Buffer.from(object.bytes), etag: '"immutable"' })
  f.objects.set("v1/head.json", { bytes: Buffer.from(jsonBytes(newer.head)), etag: '"newer-head"' })
  await assert.rejects(publishBundle(f.store, f.directory, absent), /conflict/)
  assert.equal(f.writes.length, 0)
  assert.equal((await inspect(f.store)).head?.manifest.sha256, newer.head.manifest.sha256)
})

test("corrupt immutable readback leaves head absent", async (t) => {
  const f = await fixture(t)
  f.faults.corruptObject = true
  await assert.rejects(publishBundle(f.store, f.directory, absent), /readback mismatch/)
  assert.equal(f.objects.has("v1/head.json"), false)
})

test("the transport CLI rejects public permissions and symlinks without echoing malformed credential bytes", async (t) => {
  const directory = await realpath(await mkdtemp(join(tmpdir(), "daily-r2-config-")))
  t.after(() => rm(directory, { recursive: true, force: true }))
  const config = join(directory, "s3.json")
  await writeFile(config, '{"secretAccessKey":"fixture-secret-that-must-never-appear", broken')
  const invoke = (path: string) =>
    spawnSync(process.execPath, ["--import", "tsx", "r2-cli.ts", "inspect"], {
      cwd: new URL("..", import.meta.url),
      env: { ...process.env, PUBLISH_R2_CONFIG: path },
      encoding: "utf8",
    })
  for (const mode of [0o644, 0o600]) {
    await chmod(config, mode)
    const result = invoke(config)
    assert.equal(result.status, 1)
    assert.match(result.stderr, /R2 operation failed/)
    assert.doesNotMatch(result.stderr, /fixture-secret|secretAccessKey|SyntaxError/)
    assert.equal(result.stdout, "")
  }
  const alias = join(directory, "alias.json")
  await symlink(config, alias)
  assert.equal(invoke(alias).status, 1)
})
