import assert from "node:assert/strict"
import { readFileSync } from "node:fs"
import test from "node:test"
import { parseEdition } from "../src/lib/digests.ts"
import { renderEditionHtml, renderVisual } from "../src/components/visuals.ts"
import type { BarVisual, ImageVisual } from "../src/lib/editorial.ts"

const source = { label: 'Source <report> "quoted"', url: "https://example.com/report?a=1&b=2" }
const image: ImageVisual = {
  kind: "image",
  src: "https://example.com/image.jpg?a=1&b=2",
  width: 1200,
  height: 675,
  alt: '<img onerror="bad">',
  caption: "Caption <script>bad</script>",
  credit: "A & B",
  source,
}
const chart: BarVisual = {
  kind: "bar",
  title: "Reported <merges>",
  unit: "merges per day",
  caption: "Two reported figures",
  source,
  points: [
    { label: "May", value: 2500, qualifier: "approximate" },
    { label: "September", value: 30000, qualifier: "greater-than" },
  ],
}

test("source images keep dimensions and escape every authored string", () => {
  const html = renderVisual(image)
  assert.match(html, /<figure[^>]+data-story-visual="image"/)
  assert.match(html, /src="https:\/\/example.com\/image.jpg\?a=1&amp;b=2"/)
  assert.match(html, /width="1200" height="675"/)
  assert.match(html, /alt="&lt;img onerror=&quot;bad&quot;&gt;"/)
  assert.match(html, /Caption &lt;script&gt;bad&lt;\/script&gt;/)
  assert.match(html, /A &amp; B/)
  assert.match(html, /Source &lt;report&gt; &quot;quoted&quot;/)
  assert.doesNotMatch(html, /<script|onerror="bad"/)
})

test("bar figures preserve the stated bounds and readable facts without CSS", () => {
  const html = renderVisual(chart)
  assert.match(html, /data-story-visual="bar"/)
  assert.match(html, /~2,500/)
  assert.match(html, /&gt;30,000/)
  assert.match(html, /May/)
  assert.match(html, /September/)
  assert.match(html, /merges per day/)
  assert.match(html, /Reported &lt;merges&gt;/)
  const four = renderVisual({
    ...chart,
    points: [
      { label: "Zero", value: 0, qualifier: "exact" },
      { label: "One", value: 1, qualifier: "at-least" },
      { label: "Two", value: 2, qualifier: "exact" },
      { label: "Three", value: 3, qualifier: "approximate" },
    ],
  })
  assert.match(four, /≥1/)
  assert.doesNotMatch(four, /NaN|Infinity/)
  assert.match(four, /data-chart-value="0"/)
})

test("chart labels preserve small finite measurements", () => {
  const html = renderVisual({
    ...chart,
    points: [
      { label: "Small", value: 1e-25, qualifier: "exact" },
      { label: "Large", value: 1, qualifier: "exact" },
    ],
  })
  assert.match(html, /class="bar-value">1e-25<\/strong>/)
})

test("edition rendering retains original markup when no illustration exists", () => {
  const text = readFileSync(
    new URL("./fixtures/editorial-v2-four-stories.md", import.meta.url),
    "utf8",
  )
  const edition = parseEdition({ filename: "x-ai-2026-10-15.md", text })
  assert.equal(renderEditionHtml(edition), edition.html)
  assert.equal(edition.kind, "identified")
  if (edition.kind !== "identified") return
  edition.lead.editorial = { section: "Engineering", deck: "A reported increase", visual: chart }
  const html = renderEditionHtml(edition)
  for (const story of edition.activeStories) assert.ok(html.includes(story.html))
  assert.match(html, /A reported increase/)
  assert.equal((html.match(/data-story-visual="bar"/g) ?? []).length, 1)
  assert.ok(html.includes(renderVisual(chart)))
})

test("validated image URLs resolve identically in web pages and external readers", () => {
  const text = readFileSync(
    new URL("./fixtures/editorial-v2-four-stories.md", import.meta.url),
    "utf8",
  )
  for (const src of [
    "https:images.example.com/figure.png",
    "https:/images.example.com/figure.png",
  ]) {
    const candidate = text.replace(
      "digest_format: editorial-v2\n",
      `digest_format: editorial-v2
story_metadata:
  gloss-x-import:
    section: Reading
    visual:
      kind: image
      src: ${src}
      width: 1200
      height: 675
      alt: A source image
      caption: The inspected source image.
      credit: The source author
      source_url: https://x.com/nutlope/status/2110385721391366263
`,
    )
    const edition = parseEdition({ filename: "x-ai-2026-10-15.md", text: candidate })
    if (edition.kind !== "identified") return assert.fail("expected identified edition")
    const visual = edition.stories.find((story) => story.id === "gloss-x-import")?.editorial?.visual
    if (visual?.kind !== "image") return assert.fail("expected image")
    assert.equal(
      new URL(visual.src, "https://daily.nishantkhurana.me/editions/2026-10-15/").href,
      new URL(visual.src).href,
    )
    assert.equal(visual.src, "https://images.example.com/figure.png")
    assert.match(renderVisual(visual), /src="https:\/\/images\.example\.com\/figure\.png"/)
  }
})
