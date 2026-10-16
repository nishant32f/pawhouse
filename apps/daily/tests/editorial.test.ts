import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { test } from "node:test"
import { stringify } from "yaml"
import { parseEdition } from "../../../hermes/ai-x-digest/content/parser.ts"

const actual = readFileSync(
  new URL("./fixtures/editorial-v2-four-stories.md", import.meta.url),
  "utf8",
)
const leadSource = "https://x.com/AnthropicAI/status/2110047081414987957"
const glossSource = "https://x.com/nutlope/status/2110385721391366263"
const image = {
  kind: "image",
  src: "https://images.example.com/gloss.png",
  width: 1200,
  height: 800,
  alt: "A saved article in Gloss",
  caption: "A saved article from the launch demo.",
  credit: "Hassan",
  source_url: glossSource,
}
const bar = {
  kind: "bar",
  title: "Reported code merges per day",
  unit: "merges per day",
  caption: "Two figures reported by Anthropic.",
  source_url: leadSource,
  points: [
    { label: "May", value: 2500, qualifier: "approximate" },
    { label: "September", value: 30000, qualifier: "greater-than" },
  ],
}
const input = (editorial?: unknown) => ({
  filename: "x-ai-2026-10-15.md",
  text:
    editorial === undefined
      ? actual
      : actual.replace(
          "digest_format: editorial-v2\n",
          `digest_format: editorial-v2\n${stringify({ story_metadata: editorial })}`,
        ),
})

test("validated figures add sourced editorial without changing accepted body or story identity", () => {
  const before = parseEdition(input())
  const after = parseEdition(
    input({
      "anthropic-monorepo": {
        section: "Engineering",
        deck: "Anthropic reports increased daily merges.",
        visual: bar,
      },
      "gloss-x-import": { section: "Reading", visual: image },
    }),
  )
  assert.equal(before.kind, "identified")
  assert.equal(after.kind, "identified")
  if (before.kind !== "identified" || after.kind !== "identified") return
  assert.deepEqual(
    after.stories.map((s) => s.path),
    before.stories.map((s) => s.path),
  )
  assert.deepEqual(
    after.stories.map((s) => s.html),
    before.stories.map((s) => s.html),
  )
  assert.equal(after.lead.editorial?.section, "Engineering")
  assert.equal(after.lead.editorial?.visual?.kind, "bar")
  assert.equal(after.html, before.html)
  assert.match(after.html, /more than 30,000 per day/)
  assert.match(after.html, /https:\/\/raw.githubusercontent.com\/Nutlope\/gloss\/main\/lib\/mcp.ts/)
})

test("missing editorial leaves identified and legacy editions readable", () => {
  const edition = parseEdition(input())
  if (edition.kind !== "identified") return assert.fail("expected identified edition")
  assert.equal(edition.lead.editorial, null)
  assert.doesNotMatch(edition.html, /<figure /)
  const legacy = actual.replace("editorial-v2", "editorial-v1")
  assert.equal(parseEdition({ filename: input().filename, text: legacy }).kind, "legacy")
  assert.throws(
    () =>
      parseEdition({
        ...input({ "anthropic-monorepo": { section: "Engineering" } }),
        text: input({ "anthropic-monorepo": { section: "Engineering" } }).text.replace(
          "editorial-v2",
          "editorial-v1",
        ),
      }),
    /editorial/,
  )
})

test("editorial rejects unknown IDs, unknown fields and malformed variants", () => {
  for (const editorial of [
    { "invented-story": { section: "Reading" } },
    { "anthropic-monorepo": { section: "" } },
    { "anthropic-monorepo": { section: "Engineering", deck: {} } },
    { "anthropic-monorepo": { section: "Engineering", html: "<script>bad()</script>" } },
    { "anthropic-monorepo": { section: "Engineering", visual: { ...bar, kind: "pie" } } },
    [],
    "not metadata",
  ])
    assert.throws(() => parseEdition(input(editorial)), /editorial|visual|section|deck/)
})

test("image validation rejects unsafe URLs, missing attribution and invalid dimensions", () => {
  for (const change of [
    { src: "javascript:alert(1)" },
    { src: "data:image/svg+xml,bad" },
    { src: "//images.example.com/picture.png" },
    { src: "https://user:pass@example.com/picture.png" },
    { src: "https://example.com/\npicture.png" },
    { alt: "" },
    { credit: "" },
    { width: 0 },
    { height: 1.5 },
    { caption: "" },
    { source_url: leadSource },
    { source_url: "https://unrelated.example.com/" },
    { onerror: "alert(1)" },
  ])
    assert.throws(() =>
      parseEdition(
        input({ "gloss-x-import": { section: "Reading", visual: { ...image, ...change } } }),
      ),
    )
})

test("chart validation rejects unsupported numbers and retains explicit numeric qualifiers", () => {
  for (const change of [
    { points: [{ label: "May", value: 2500, qualifier: "exact" }] },
    {
      points: Array.from({ length: 5 }, (_, i) => ({
        label: `Point ${i}`,
        value: i + 1,
        qualifier: "exact",
      })),
    },
    { points: [{ label: "May", value: -1, qualifier: "exact" }, bar.points[1]] },
    { points: [{ label: "May", value: NaN, qualifier: "exact" }, bar.points[1]] },
    { points: [{ label: "May", value: Infinity, qualifier: "exact" }, bar.points[1]] },
    {
      points: [
        { label: "May", value: 0, qualifier: "exact" },
        { label: "June", value: 0, qualifier: "exact" },
      ],
    },
    { points: [{ label: "May", value: 2500, qualifier: "roughly maybe" }, bar.points[1]] },
    { unit: "" },
    { source_url: glossSource },
  ])
    assert.throws(() =>
      parseEdition(
        input({ "anthropic-monorepo": { section: "Engineering", visual: { ...bar, ...change } } }),
      ),
    )
  const edition = parseEdition(
    input({
      "anthropic-monorepo": {
        section: "Engineering",
        visual: {
          ...bar,
          points: [
            { label: "May", value: 2500, qualifier: "exact" },
            { label: "September", value: 30000, qualifier: "at-least" },
          ],
        },
      },
    }),
  )
  if (edition.kind !== "identified") return assert.fail("expected identified edition")
  assert.equal(edition.lead.editorial?.visual?.kind, "bar")
})

test("editorial data preserves literal captions and alt text for the view to escape", () => {
  const caption = "<script>bad()</script>"
  const alt = '\" onload=\"alert(1)'
  const edition = parseEdition(
    input({ "gloss-x-import": { section: "Reading", visual: { ...image, alt, caption } } }),
  )
  if (edition.kind !== "identified") return assert.fail("expected identified edition")
  const visual = edition.stories.find((s) => s.id === "gloss-x-import")?.editorial?.visual
  if (visual?.kind !== "image") return assert.fail("expected image data")
  assert.equal(visual.alt, alt)
  assert.equal(visual.caption, caption)
  assert.doesNotMatch(edition.html, /<script/)
})
