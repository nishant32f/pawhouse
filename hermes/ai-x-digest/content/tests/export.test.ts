import assert from "node:assert/strict"
import { createHash } from "node:crypto"
import { execFileSync } from "node:child_process"
import { mkdtempSync, mkdirSync, readFileSync, rmSync, writeFileSync } from "node:fs"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import test from "node:test"
import { compileRepository, jsonBytes } from "../compiler.ts"
import { decodeHead, decodeManifest, decodeObjectRef } from "../storage.ts"
import { decodeCatalog, decodeRoutes, decodeSearch } from "../discovery.ts"
import { decodeEdition, materializeEdition } from "../wire.ts"
import { parseEdition } from "../parser.ts"

const contentRoot = resolve(import.meta.dirname, "..")
const fixtureRoot = resolve(contentRoot, "../../../apps/daily/tests/fixtures")
const inputs = [
  { filename: "x-ai-2026-05-10.md", fixture: "legacy-unversioned.md" },
  { filename: "x-ai-2026-10-15.md", fixture: "editorial-v2-four-stories.md" },
  { filename: "x-ai-2026-10-16.md", fixture: "editorial-v2-brief-archive.md" },
].map(({ filename, fixture }) => ({
  filename,
  text: readFileSync(join(fixtureRoot, fixture), "utf8"),
}))

test("the accepted fixtures preserve every source hash, feed identity, article and archived route", () => {
  assert.equal(inputs.length, 3)
  const exported = compileRepository(inputs, { compilerRevision: "frozen-test-revision" })
  assert.deepEqual(
    compileRepository([...inputs].reverse(), { compilerRevision: "frozen-test-revision" }),
    exported,
  )
  const rss = exported.objects.find((o) => o.key === exported.manifest.rss.key)?.bytes
  assert.ok(rss)
  assert.equal((rss.match(/<item>/g) ?? []).length, inputs.length)
  const routes = JSON.parse(
    exported.objects.find((o) => o.key === exported.manifest.routes.key)?.bytes ?? "{}",
  ).routes
  const search = JSON.parse(
    exported.objects.find((o) => o.key === exported.manifest.search.key)?.bytes ?? "{}",
  ).documents
  for (const input of inputs) {
    const before = parseEdition(input)
    const ref = exported.manifest.editions.find((e) => e.date === before.date)
    assert.ok(ref)
    assert.equal(ref.sourceSha256, createHash("sha256").update(input.text).digest("hex"))
    const object = exported.objects.find((o) => o.key === ref.object.key)
    assert.ok(object)
    const after = materializeEdition(decodeEdition(JSON.parse(object.bytes)))
    assert.equal(after.text, before.text)
    assert.equal(after.html.replace(/ id="[^"]*"/g, ""), before.html)
    assert.ok(
      rss.includes(`<guid isPermaLink="true">https://daily.nishantkhurana.me${before.path}</guid>`),
    )
    assert.ok(rss.includes(`<pubDate>${new Date(before.publishedAt).toUTCString()}</pubDate>`))
    assert.ok(routes.some((r: { path: string }) => r.path === before.readPath))
    if (before.kind === "identified")
      for (const story of before.stories) {
        assert.ok(routes.some((r: { path: string }) => r.path === story.path))
        assert.ok(
          search.some(
            (r: { path: string; text: string }) => r.path === story.path && r.text === story.text,
          ),
        )
      }
  }
  for (const object of exported.objects) {
    assert.equal(object.sha256, createHash("sha256").update(object.bytes).digest("hex"))
    assert.equal(object.byteLength, Buffer.byteLength(object.bytes))
  }
})

test("CLI writes only the deterministic complete object set and head, without source indexes", () => {
  const folder = mkdtempSync(join(tmpdir(), "daily-content-cli-"))
  const output = join(folder, "objects")
  const archive = join(folder, "accepted")
  mkdirSync(archive)
  for (const input of inputs) writeFileSync(join(archive, input.filename), input.text)
  writeFileSync(join(archive, "2026-10.md"), "Private source index, not an edition")
  try {
    const result = JSON.parse(
      execFileSync(
        process.execPath,
        [
          "--import",
          "tsx",
          "cli.ts",
          "--input-dir",
          archive,
          "--output-dir",
          output,
          "--compiler-revision",
          "cli-test",
        ],
        { cwd: contentRoot, encoding: "utf8" },
      ),
    )
    const head = decodeHead(JSON.parse(readFileSync(join(output, "v1/head.json"), "utf8")))
    assert.deepEqual(head, result.head)
    const manifest = decodeManifest(
      JSON.parse(readFileSync(join(output, head.manifest.key), "utf8")),
    )
    assert.equal(manifest.editions.length, inputs.length)
    for (const rawRef of result.objects) {
      const ref = decodeObjectRef(rawRef)
      const bytes = readFileSync(join(output, ref.key))
      assert.equal(bytes.byteLength, ref.byteLength)
      assert.equal(createHash("sha256").update(bytes).digest("hex"), ref.sha256)
    }
    assert.equal(readFileSync(join(output, "v1/head.json"), "utf8"), jsonBytes(head))
    assert.ok(result.objects.every((ref: { key: string }) => !ref.key.includes("source")))
  } finally {
    rmSync(folder, { recursive: true, force: true })
  }
})

test("storage records reject versions, unknown fields, mutable keys and invalid lengths", () => {
  const exported = compileRepository(inputs.slice(0, 1), { compilerRevision: "test" })
  assert.deepEqual(decodeManifest(JSON.parse(JSON.stringify(exported.manifest))), exported.manifest)
  for (const change of [{ schemaVersion: 99 }, { privatePath: "/vault" }, { compilerRevision: "" }])
    assert.throws(() => decodeManifest({ ...exported.manifest, ...change }))
  for (const change of [
    { key: "v1/head.json" },
    { byteLength: -1 },
    { byteLength: 0 },
    { sha256: "invalid" },
    { html: "bad" },
  ])
    assert.throws(() => decodeObjectRef({ ...exported.head.manifest, ...change }))
  assert.throws(() => decodeHead({ ...exported.head, schemaVersion: 0 }))
})

test("discovery decoders reject unknown fields and unsafe route identities", () => {
  const exported = compileRepository(inputs, { compilerRevision: "test" })
  const get = (key: string) =>
    JSON.parse(exported.objects.find((o) => o.key === key)?.bytes ?? "{}")
  const catalog = get(exported.manifest.catalog.key)
  const routes = get(exported.manifest.routes.key)
  const search = get(exported.manifest.search.key)
  assert.deepEqual(decodeCatalog(catalog), catalog)
  assert.deepEqual(decodeRoutes(routes), routes)
  assert.deepEqual(decodeSearch(search), search)
  assert.throws(() => decodeCatalog({ ...catalog, html: "bad" }))
  assert.throws(() => decodeRoutes({ ...routes, schemaVersion: 99 }))
  assert.throws(() =>
    decodeSearch({ ...search, documents: [{ ...search.documents[0], path: "javascript:bad()" }] }),
  )
  const nextCompiler = compileRepository(inputs, { compilerRevision: "next-revision" })
  assert.deepEqual(nextCompiler.manifest.editions, exported.manifest.editions)
  assert.deepEqual(nextCompiler.manifest.rss, exported.manifest.rss)
  assert.notEqual(nextCompiler.head.manifest.sha256, exported.head.manifest.sha256)
})
