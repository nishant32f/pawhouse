import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"
import { compileRepository } from "../../../hermes/ai-x-digest/content/compiler.ts"
import {
  selectPublication,
  PublicationUnavailable,
  type ReadBucket,
} from "../src/lib/publication.ts"

const fixture = readFileSync(
  new URL("./fixtures/editorial-v2-four-stories.md", import.meta.url),
  "utf8",
)
const compile = (text = fixture) =>
  compileRepository([{ filename: "x-ai-2026-10-15.md", text }], {
    compilerRevision: "fixture-compiler",
  })
function binding(publication = compile()) {
  const objects = new Map(publication.objects.map((object) => [object.key, object.bytes]))
  objects.set("v1/head.json", JSON.stringify(publication.head))
  const gets: string[] = []
  const bucket: ReadBucket = {
    async get(key) {
      gets.push(key)
      const bytes = objects.get(key)
      if (!bytes) return null
      const body = new Response(bytes).body
      assert.ok(body)
      return {
        size: new TextEncoder().encode(bytes).byteLength,
        body,
        arrayBuffer: () => new Response(bytes).arrayBuffer(),
      }
    },
  }
  return { bucket, gets, objects }
}

test("one selected head pins subsequent catalog and edition reads", async () => {
  const a = compile()
  const b = compile(fixture.replace("Anthropic says it migrated", "Anthropic confirms it migrated"))
  const { bucket, gets, objects } = binding(a)
  const selected = await selectPublication(bucket)
  for (const object of b.objects) objects.set(object.key, object.bytes)
  objects.set("v1/head.json", JSON.stringify(b.head))
  assert.equal((await selected.catalog()).editions[0]?.date, "2026-10-15")
  assert.match((await selected.edition("2026-10-15"))?.text ?? "", /Anthropic says/)
  assert.equal(gets.filter((key) => key === "v1/head.json").length, 1)
  const next = await selectPublication(bucket)
  assert.notEqual(next.publicationRevision, selected.publicationRevision)
  assert.match((await next.edition("2026-10-15"))?.text ?? "", /Anthropic confirms/)
})

test("home materializes one edition; discovery and RSS never read edition bodies", async () => {
  const publication = compile()
  const { bucket, gets } = binding(publication)
  const selected = await selectPublication(bucket)
  await selected.catalog()
  await selected.routes()
  await selected.search()
  const rss = await selected.rss()
  assert.equal(rss.status, 200)
  assert.ok(publication.manifest.editions.every((entry) => !gets.includes(entry.object.key)))
  await selected.edition()
  assert.equal(gets.filter((key) => key === publication.manifest.editions[0]?.object.key).length, 1)
  assert.equal(await selected.edition("2026-10-17"), undefined)
})

test("missing, malformed, unsupported and corrupt referenced content fails closed", async () => {
  for (const bytes of [undefined, "{}", '{"schemaVersion":2}', "corrupt"]) {
    const publication = compile()
    const { bucket, objects } = binding(publication)
    if (bytes === undefined) objects.delete(publication.manifest.catalog.key)
    else objects.set(publication.manifest.catalog.key, bytes)
    const selected = await selectPublication(bucket)
    await assert.rejects(selected.catalog(), PublicationUnavailable)
  }
})
