import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"
import { compileEdition, compileRepository } from "../compiler.ts"
import { editionFeedHtml } from "../syndication.ts"
import { decodeEdition, materializeEdition } from "../wire.ts"
import { parseEdition, validateRevision } from "../parser.ts"

const fixture = (name: string, date: string) => ({
  filename: `x-ai-${date}.md`,
  text: readFileSync(
    new URL(`../../../../apps/daily/tests/fixtures/${name}`, import.meta.url),
    "utf8",
  ),
})
const inputs = [
  fixture("editorial-v2-four-stories.md", "2026-10-15"),
  fixture("editorial-v2-brief-archive.md", "2026-10-16"),
  fixture("legacy-unversioned.md", "2026-05-10"),
  fixture("editorial-v1.md", "2026-10-15"),
]

test("safe wire round trips accepted prose, identity, dates, archives and source associations", () => {
  for (const input of inputs) {
    const before = parseEdition(input)
    const wire = compileEdition(input)
    const after = materializeEdition(decodeEdition(JSON.parse(JSON.stringify(wire))))
    for (const key of [
      "date",
      "title",
      "publishedAt",
      "path",
      "readPath",
      "sourceSha256",
      "html",
      "text",
      "sources",
    ] as const)
      assert.deepEqual(
        key === "html" ? String(after[key]).replace(/ id="[^"]*"/g, "") : after[key],
        before[key],
        key,
      )
    const json = JSON.stringify(wire)
    assert.doesNotMatch(
      json,
      /"(?:html|markdown|bodyMarkdown|originalMarkdown|sourcePath|position)":/,
    )
    if (before.kind === "identified" && after.kind === "identified") {
      assert.deepEqual(
        after.stories.map((s) => [
          s.id,
          s.path,
          s.html.replace(/ id="[^"]*"/g, ""),
          s.text,
          s.sources,
        ]),
        before.stories.map((s) => [s.id, s.path, s.html, s.text, s.sources]),
      )
    }
  }
})

test("wire rejects unknown versions, fields, unsafe URLs and raw HTML before export", () => {
  const wire = compileEdition(inputs[0]!)
  for (const mutation of [
    { ...wire, schemaVersion: 99 },
    { ...wire, html: "bad" },
    { ...wire, sourcePath: "/private/vault" },
    { ...wire, prose: [{ type: "html", value: "<script>bad()</script>" }] },
    { ...wire, sources: [{ label: "bad", url: "javascript:bad()" }] },
  ])
    assert.throws(() => decodeEdition(mutation))
  assert.throws(
    () =>
      compileEdition({
        ...inputs[0]!,
        text: inputs[0]!.text.replace(
          "The company reports",
          "<script>bad()</script>\n\nThe company reports",
        ),
      }),
    /HTML/,
  )
})

test("complete frozen exports have deterministic bytes, immutable keys and stable feed identity", () => {
  const frozen = inputs.slice(0, 3)
  const first = compileRepository(frozen, { compilerRevision: "test-revision" })
  assert.deepEqual(
    compileRepository([...frozen].reverse(), { compilerRevision: "test-revision" }),
    first,
  )
  assert.ok(first.objects.every((o) => o.key.includes(o.sha256)))
  assert.equal(first.head.schemaVersion, 1)
  assert.ok(first.objects.some((o) => o.key === first.head.manifest.key))
  const rss = first.objects.find((o) => o.contentType.startsWith("application/rss+xml"))!.bytes
  assert.equal((rss.match(/<item>/g) ?? []).length, 3)
  const corrected = compileRepository(
    frozen.map((i) => ({
      ...i,
      text: i.text.replace("The company reports", "The company now reports"),
    })),
    { compilerRevision: "test-revision" },
  )
  const correctedRss = corrected.objects.find((o) =>
    o.contentType.startsWith("application/rss+xml"),
  )!.bytes
  assert.deepEqual(
    rss.match(/<(?:guid|pubDate)[^>]*>[^<]+/g),
    correctedRss.match(/<(?:guid|pubDate)[^>]*>[^<]+/g),
  )
})

test("references resolve once and private comments and review metadata are absent from wire records", () => {
  const original = inputs[0]
  assert.ok(original)
  const text =
    original.text
      .replace(
        "[Anthropic's migration announcement](https://x.com/AnthropicAI/status/2110047081414987957)",
        "[Anthropic's migration announcement][announcement]",
      )
      .replace(
        "digest_format: editorial-v2",
        "digest_format: editorial-v2\nprivate_review: secret review from /private/vault",
      )
      .replace("The company reports", "<!-- private review comment -->\n\nThe company reports") +
    "\n[announcement]: https://example.com/announcement\n"
  const edition = compileEdition({ ...original, text })
  assert.equal(edition.sources[0]?.url, "https://example.com/announcement")
  const json = JSON.stringify(edition)
  assert.doesNotMatch(
    json,
    /private review|secret review|private_review|\/private\/vault|linkReference|definition/,
  )
  assert.match(materializeEdition(edition).html, /href="https:\/\/example.com\/announcement"/)
})

test("legacy heading fragments and duplicate collisions match Quartz's rehype-slug rule", () => {
  const edition = compileEdition({
    filename: "x-ai-2026-10-15.md",
    text: "---\ntitle: Anchors\ndate: 2026-10-15\n---\n## Repeated heading\n\nFirst.\n\n## Repeated heading\n\nSecond.\n\n## Repeated heading-1\n\nThird.\n",
  })
  assert.deepEqual(edition.anchors, [
    "repeated-heading",
    "repeated-heading-1",
    "repeated-heading-1-1",
  ])
  const html = materializeEdition(edition).html
  for (const anchor of edition.anchors) assert.ok(html.includes(`id="${anchor}"`))
  const identified = compileEdition(inputs[0]!)
  assert.equal(identified.kind, "identified")
  if (identified.kind === "identified")
    assert.equal(
      identified.stories[0]?.legacyAnchor,
      "anthropic-says-it-migrated-its-monorepo-from-git",
    )
})

test("neutral RSS keeps image attribution and all chart values and numeric qualifiers", () => {
  const original = inputs[0]!
  const metadata = `story_metadata:
  anthropic-monorepo:
    section: Engineering
    deck: Reported figures.
    visual:
      kind: bar
      title: All qualifiers
      unit: merges per day
      caption: Four reported values.
      source_url: https://x.com/AnthropicAI/status/2110047081414987957
      points:
        - { label: Exact, value: 0, qualifier: exact }
        - { label: Approximate, value: 2500, qualifier: approximate }
        - { label: Greater, value: 30000, qualifier: greater-than }
        - { label: Minimum, value: 1, qualifier: at-least }
  gloss-x-import:
    section: Reading
    visual:
      kind: image
      src: https://images.example.com/gloss.png
      width: 1200
      height: 800
      alt: A saved article
      caption: The launch demo.
      credit: Hassan
      source_url: https://x.com/nutlope/status/2110385721391366263
`
  const edition = compileEdition({
    ...original,
    text: original.text.replace(
      "digest_format: editorial-v2\n",
      "digest_format: editorial-v2\n" + metadata,
    ),
  })
  if (edition.kind !== "identified") return assert.fail("expected identified")
  const materialized = materializeEdition(decodeEdition(JSON.parse(JSON.stringify(edition))))
  if (materialized.kind !== "identified") return assert.fail("expected materialized identified")
  assert.deepEqual(
    materialized.stories.map((s) => s.editorial),
    edition.stories.map((s) => s.editorial),
  )
  const html = editionFeedHtml(edition)
  for (const literal of [
    "<table>",
    'scope="col"',
    'scope="row"',
    "All qualifiers",
    "merges per day",
    "Exact",
    "Approximate",
    "Greater",
    "Minimum",
    "~2,500",
    "&gt;30,000",
    "≥1",
    "Four reported values.",
    "The launch demo.",
    "Image: Hassan.",
    'alt="A saved article"',
    "https://x.com/nutlope/status/2110385721391366263",
  ])
    assert.ok(html.includes(literal), literal)
  assert.doesNotMatch(html, /<svg|class=|style=/)
})

test("corrections cannot lose identified stories or change retained archived prose or sources", () => {
  const input = fixture("editorial-v2-brief-archive.md", "2026-10-16")
  const previous = parseEdition(input)
  validateRevision(previous, parseEdition(input))
  if (previous.kind !== "identified") return assert.fail("expected identified")
  const withoutArchive = {
    ...previous,
    stories: previous.stories.filter((s) => s.kind !== "archived"),
  }
  assert.throws(() => validateRevision(previous, withoutArchive), /lost a story ID/)
  const alteredSources = {
    ...previous,
    stories: previous.stories.map((s) =>
      s.kind === "archived"
        ? { ...s, sources: [{ label: "Different", url: "https://example.com/different" }] }
        : s,
    ),
  }
  assert.throws(() => validateRevision(previous, alteredSources), /archived sources/)
  const alteredProse = {
    ...previous,
    stories: previous.stories.map((s) =>
      s.kind === "archived" ? { ...s, markdown: "Replacement prose" } : s,
    ),
  }
  assert.throws(() => validateRevision(previous, alteredProse), /archived prose/)
})
