import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import { test } from "node:test"
import { parseEdition } from "../../../hermes/ai-x-digest/content/parser.ts"

const producer = readFileSync(
  new URL(
    "../../../hermes/ai-x-digest/runtime/skills/note-taking/ai-x-digest/SKILL.md",
    import.meta.url,
  ),
  "utf8",
)

test("the producer's documented media data passes the publication parser", () => {
  const metadata = producer.match(/```yaml\n(story_metadata:[\s\S]*?)\n```/)?.[1]
  assert.ok(metadata)
  const original = readFileSync(
    new URL("./fixtures/editorial-v2-four-stories.md", import.meta.url),
    "utf8",
  )
  const edition = parseEdition({
    filename: "x-ai-2026-10-15.md",
    text: original.replace(
      "digest_format: editorial-v2\n",
      `digest_format: editorial-v2\n${metadata}\n`,
    ),
  })
  if (edition.kind !== "identified") return assert.fail("expected identified edition")
  assert.equal(edition.lead.editorial?.visual?.kind, "bar")
  assert.equal(
    edition.stories.find((story) => story.id === "gloss-x-import")?.editorial?.visual?.kind,
    "image",
  )
})

test("the producer's complete edition example passes the publication parser", () => {
  const example = producer.match(/```markdown\n(---\n[\s\S]*?)\n```/)?.[1]
  assert.ok(example)
  const text = example
    .replaceAll("YYYY-MM-DD", "2026-10-15")
    .replaceAll("YYYY-MM", "2026-10")
    .replaceAll("YYYY", "2026")
  const edition = parseEdition({ filename: "x-ai-2026-10-15.md", text })
  if (edition.kind !== "identified") return assert.fail("expected identified edition")
  assert.deepEqual(
    edition.activeStories.map((story) => story.id),
    ["concrete-lead-event", "supporting-event", "brief-event"],
  )
  assert.equal(edition.lead.editorial?.section, "Engineering")
})
