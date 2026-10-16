import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"
import { parseEdition, parseEditions } from "../../../hermes/ai-x-digest/content/parser.ts"

const fixture = (name: string) =>
  readFileSync(new URL(`./fixtures/${name}`, import.meta.url), "utf8")
const actual = fixture("editorial-v2-four-stories.md")
const input = (text = actual, date = "2026-10-15") => ({ filename: `x-ai-${date}.md`, text })

test("actual accepted edition becomes four ordered stories with its real sources", () => {
  const edition = parseEdition(input())
  assert.equal(edition.kind, "identified")
  if (edition.kind !== "identified") return
  assert.deepEqual(
    edition.stories.map((story) => story.id),
    ["anthropic-monorepo", "cloud-computers", "gloss-x-import", "claude-code-hooks"],
  )
  assert.equal(edition.lead.id, "anthropic-monorepo")
  assert.equal(edition.stories[2]?.sources.length, 3)
  assert.match(edition.stories[0]?.summary ?? "", /^Anthropic said/)
  assert.match(edition.stories[0]?.bodyMarkdown ?? "", /^The company reports/)
  assert.match(edition.html, /https:\/\/x.com\/AnthropicAI\/status/)
  assert.doesNotMatch(edition.html, /story-id|Backlinks|Navigation/)
  assert.equal(edition.originalMarkdown, actual)
  assert.equal(edition.publishedAt, "2026-10-15T00:00:00+05:30")
  assert.match(edition.sourceSha256, /^[a-f0-9]{64}$/)
})

test("legacy versions remain whole editions without inferred story routes", () => {
  for (const [name, date] of [
    ["editorial-v1.md", "2026-10-15"],
    ["legacy-unversioned.md", "2026-05-10"],
  ]) {
    const text = fixture(name ?? "")
    const edition = parseEdition(input(text, date))
    assert.equal(edition.kind, "legacy")
    assert.equal(edition.originalMarkdown, text)
    assert.ok(edition.sources.length > 0)
    assert.doesNotMatch(edition.html, /Backlinks|Navigation/)
    if (name === "legacy-unversioned.md")
      assert.match(edition.html, /Original imported wording remains intact/)
  }
})

test("briefs navigate as active stories, archives retain their routes and corrections", () => {
  const edition = parseEdition(input(fixture("editorial-v2-brief-archive.md"), "2026-10-16"))
  assert.equal(edition.kind, "identified")
  if (edition.kind !== "identified") return
  assert.deepEqual(
    edition.activeStories.map((story) => story.kind),
    ["story", "brief"],
  )
  assert.equal(edition.archivedStories[0]?.path, "/editions/2026-10-16/stories/vendor-benchmark/")
  assert.match(edition.archivedStories[0]?.html ?? "", /Correction: The vendor withdrew/)
  assert.doesNotMatch(edition.html, /benchmark|withdrew/)
})

test("date, version, identity, membership and source violations reject the edition", () => {
  const cases = [
    actual.replace("editorial-v2", "editorial-v99"),
    actual.replace("story-id: cloud-computers", "story-id: anthropic-monorepo"),
    actual.replace("story-id: cloud-computers", "story-id: ../escape"),
    actual.replace("<!-- story-id: cloud-computers -->", "\n<!-- story-id: cloud-computers -->"),
    actual.replace("## Navigation", "## Navigation\n<!-- story-id: furniture -->"),
    actual.replace("## Navigation", "## navigation"),
    actual.replace("## Hang Huang", "### Hang Huang"),
    actual.replace("date: 2026-10-15", "date: 2026-02-30"),
    actual.replace("date: 2026-10-15", "date: 2026-10-14"),
    actual.replace("date: 2026-10-15", "date: 2026-10-15\ndate: 2026-10-15"),
    actual.replace(
      "https://x.com/AnthropicAI/status/2110047081414987957",
      "javascript:alert%281%29",
    ),
    actual.replace(
      "Source: [Anthropic's migration announcement](https://x.com/AnthropicAI/status/2110047081414987957).",
      "Source missing.",
    ),
  ]
  for (const text of cases) assert.throws(() => parseEdition(input(text)))
  assert.throws(() => parseEdition({ filename: "../x-ai-2026-10-15.md", text: actual }))
  assert.throws(() => parseEditions([input(), input()]), /duplicate.*date/i)
  assert.throws(() => parseEdition(input(fixture("no-news.txt"))))
  assert.throws(() => parseEdition(input(fixture("collection-error.txt"))))
})

test("stable IDs keep URLs after headline changes and repeated parsing is deterministic", () => {
  const original = parseEdition(input())
  const renamed = parseEdition(
    input(actual.replace("Anthropic says it migrated its monorepo from Git", "Changed headline")),
  )
  assert.deepEqual(parseEdition(input()), original)
  if (original.kind === "identified" && renamed.kind === "identified") {
    assert.equal(original.lead.path, renamed.lead.path)
  } else assert.fail("expected identified editions")
  assert.equal(original.path, "/editions/2026-10-15/")
  assert.equal(original.readPath, "/editions/2026-10-15/read/")
})

test("AST rendering escapes raw HTML, ignores fenced markers and preserves useful knowledge links", () => {
  const text = actual.replace(
    "The company reports",
    '<script>alert("bad")</script>\n\n```md\n## Fake heading\n<!-- story-id: fake-id -->\n```\n\nSee [[wisdom/example|a knowledge note]].\n\nThe company reports',
  )
  const edition = parseEdition(input(text))
  assert.match(edition.html, /&lt;script>/)
  assert.doesNotMatch(edition.html, /<script>/)
  assert.match(edition.html, /href="https:\/\/nishantkhurana.me\/wisdom\/example"/)
  assert.equal(edition.sources.length, 7)
  if (edition.kind === "identified") assert.equal(edition.stories.length, 4)
})

test("reference links belong to their own story and cannot hide unsafe URLs", () => {
  const text =
    actual.replace(
      "[Anthropic's migration announcement](https://x.com/AnthropicAI/status/2110047081414987957)",
      "[Anthropic's migration announcement][migration]",
    ) + "\n[migration]: https://example.com/migration\n"
  const edition = parseEdition(input(text))
  assert.equal(edition.sources[0]?.url, "https://example.com/migration")
  assert.throws(() =>
    parseEdition(input(text.replace("https://example.com/migration", "data:text/html,boom"))),
  )
})

test("images, inline code, fenced code and comments cannot supply another story's sources", () => {
  const original =
    "Source: [Anthropic's migration announcement](https://x.com/AnthropicAI/status/2110047081414987957)."
  for (const replacement of [
    "![Image report](https://example.com/image)",
    "`[Code report](https://example.com/code)`",
    "```md\n[Example report](https://example.com/example)\n```",
    "<!-- [Hidden report](https://example.com/hidden) -->",
    "[[wisdom/example|Knowledge note]]",
  ])
    assert.throws(
      () => parseEdition(input(actual.replace(original, replacement))),
      /missing adjacent HTTPS source/,
    )
})

test("the calendar rejects impossible dates and accepts leap day", () => {
  const template = fixture("legacy-unversioned.md")
  for (const date of ["2026-02-29", "2026-04-31", "2026-13-01", "2026-00-10"]) {
    assert.throws(
      () => parseEdition(input(template.replaceAll("2026-05-10", date), date)),
      /invalid edition date/,
    )
  }
  assert.equal(
    parseEdition(input(template.replaceAll("2026-05-10", "2024-02-29"), "2024-02-29")).date,
    "2024-02-29",
  )
})

test("unsafe links reject across images, definitions and encoded schemes", () => {
  for (const link of [
    "[bad](java&#x73;cript:alert%281%29)",
    "![bad](file:///private/file)",
    "[bad](//untrusted.example/path)",
    "[bad](https://user:pass@example.com/path)",
  ]) {
    assert.throws(
      () =>
        parseEdition(
          input(actual.replace("The company reports", `${link}\n\nThe company reports`)),
        ),
      /unsafe URL/,
    )
  }
})

test("legacy relative knowledge links resolve to the main site without becoming invented sources", () => {
  const text = fixture("legacy-unversioned.md").replace(
    "Original imported wording remains intact.",
    "Original imported wording remains intact. See [note](../wisdom/example) and [[wisdom/other|other note]].",
  )
  const edition = parseEdition(input(text, "2026-05-10"))
  assert.match(edition.html, /href="https:\/\/nishantkhurana.me\/wisdom\/example"/)
  assert.equal(edition.sources.length, 1)
  assert.equal(edition.sources[0]?.url, "https://example.com/original")
})
