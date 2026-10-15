import assert from "node:assert/strict"
import { execFileSync } from "node:child_process"
import {
  cpSync,
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  symlinkSync,
  writeFileSync,
  existsSync,
} from "node:fs"
import { tmpdir } from "node:os"
import { join, resolve } from "node:path"
import { after, before, test } from "node:test"

const app = resolve(import.meta.dirname, "..")
const fixtureRoot = mkdtempSync(join(tmpdir(), "daily-reading-"))
const fixtureApp = join(fixtureRoot, "apps/daily")
const output = join(fixtureApp, "dist")
const read = (path: string) => readFileSync(join(output, path), "utf8")
const run = (command: string, args: string[], cwd = fixtureRoot) =>
  execFileSync(command, args, { cwd, encoding: "utf8", stdio: "pipe" })

before(
  () => {
    mkdirSync(fixtureApp, { recursive: true })
    for (const name of ["src", "public", "astro.config.mjs", "tsconfig.json", "package.json"])
      if (existsSync(join(app, name)))
        cpSync(join(app, name), join(fixtureApp, name), { recursive: true })
    symlinkSync(join(app, "node_modules"), join(fixtureApp, "node_modules"), "dir")
    const content = join(fixtureRoot, "content/digests")
    mkdirSync(content, { recursive: true })
    for (const [file, date] of [
      ["editorial-v2-four-stories.md", "2026-10-15"],
      ["editorial-v2-brief-archive.md", "2026-10-16"],
      ["editorial-v2-single-story.md", "2026-10-14"],
      ["legacy-unversioned.md", "2026-05-10"],
    ]) {
      if (file && date) cpSync(join(app, "tests/fixtures", file), join(content, `x-ai-${date}.md`))
    }
    const illustrated = join(content, "x-ai-2026-10-15.md")
    writeFileSync(
      illustrated,
      readFileSync(illustrated, "utf8").replace(
        "digest_format: editorial-v2",
        `digest_format: editorial-v2
story_metadata:
  anthropic-monorepo:
    section: Engineering
    deck: Two company-reported merge figures.
    visual:
      kind: bar
      title: Reported code merges
      unit: merges per day
      caption: September exceeds the stated lower bound.
      source_url: https://x.com/AnthropicAI/status/2110047081414987957
      points:
        - { label: May, value: 2500, qualifier: approximate }
        - { label: September, value: 30000, qualifier: greater-than }
  gloss-x-import:
    section: Reading
    visual:
      kind: image
      src: https://example.com/launch.jpg?a=1&b=2
      width: 1200
      height: 675
      alt: Saved article in the launch demonstration
      caption: A source image with an adjacent citation.
      credit: Hassan
      source_url: https://x.com/nutlope/status/2110385721391366263`,
      ),
    )
    run("git", ["init", "-q"])
    run("git", ["add", "content"])
    run("git", [
      "-c",
      "user.name=Reader fixture",
      "-c",
      "user.email=reader@example.com",
      "commit",
      "-qm",
      "Accepted reading fixtures",
    ])
    run(process.execPath, [join(app, "node_modules/astro/bin/astro.mjs"), "build"], fixtureApp)
  },
  { timeout: 120000 },
)

after(() => {
  if (process.env.DAILY_KEEP_READING_FIXTURE)
    process.stderr.write(`Reader fixture: ${fixtureRoot}\n`)
  else rmSync(fixtureRoot, { recursive: true, force: true })
})

test("latest and dated front pages retain actual dates and story order", () => {
  const home = read("index.html")
  assert.match(home, /2026-10-16/)
  assert.match(home, /canonical[^>]+https:\/\/daily\.nishantkhurana\.me\/editions\/2026-10-16\//)
  const front = read("editions/2026-10-15/index.html")
  const headlines = ["Anthropic says", "Hang Huang announces", "Gloss requires", "tanelog reports"]
  const articles = [...front.matchAll(/<article\b[^>]*>[\s\S]*?<\/article>/g)]
  assert.equal(articles.length, headlines.length)
  for (const [index, headline] of headlines.entries()) {
    const article = articles[index]?.[0]
    assert.ok(article)
    assert.ok(article.includes(headline))
  }
  assert.match(front, /Read full edition/)
  assert.match(front, /The README says social posts/)
  assert.match(front, /more than 30,000 per day/)
  assert.doesNotMatch(front, /print-edition/)
})

test("static article routes contain complete prose, adjacent sources and active navigation", () => {
  const first = read("editions/2026-10-15/stories/anthropic-monorepo/index.html")
  assert.match(first, /more than 30,000 per day/)
  assert.match(first, /href="https:\/\/x.com\/AnthropicAI\/status\/2110047081414987957"/)
  assert.match(first, /rel="next"[^>]+cloud-computers/)
  assert.doesNotMatch(first, /rel="prev"/)
  assert.match(first, /Back to edition/)
  const last = read("editions/2026-10-15/stories/claude-code-hooks/index.html")
  assert.match(last, /rel="prev"[^>]+gloss-x-import/)
  assert.doesNotMatch(last, /rel="next"/)
  const archived = read("editions/2026-10-16/stories/vendor-benchmark/index.html")
  assert.match(archived, /Correction: The vendor withdrew/)
  assert.match(archived, /The vendor reported a faster benchmark/)
  assert.match(archived, /https:\/\/example.com\/benchmark/)
  assert.doesNotMatch(archived, /rel="(?:prev|next)"/)
  for (const file of ["editions/2026-10-16/index.html", "editions/2026-10-16/read/index.html"]) {
    const html = read(file)
    assert.doesNotMatch(html, /vendor-benchmark/)
    assert.match(html, /import-limit/)
  }
})

test("legacy editions remain whole; archive and search work without JavaScript", () => {
  const legacy = read("editions/2026-05-10/index.html")
  assert.match(legacy, /Original imported wording remains intact/)
  assert.match(legacy, /https:\/\/example.com\/original/)
  assert.equal(existsSync(join(output, "editions/2026-05-10/stories")), false)
  const full = read("editions/2026-10-15/read/index.html")
  assert.match(full, /The README says social posts/)
  assert.match(full, /https:\/\/raw.githubusercontent.com\/Nutlope\/gloss\/main\/lib\/mcp.ts/)
  const archive = read("archive/index.html")
  assert.ok(archive.indexOf("2026-10-16") < archive.indexOf("2026-05-10"))
  const search = read("search/index.html")
  assert.match(search, /<label[^>]*for="search-query"/)
  assert.match(search, /Search headlines and full text, or browse every edition below/)
  assert.match(search, /anthropic-monorepo/)
  assert.match(search, /2026-05-10/)
  assert.match(search, /No matches/)
  assert.ok(existsSync(join(output, "404.html")))
  assert.equal(existsSync(join(output, "editions/2026-10-17")), false)
})

test("RSS has full sanitized editions, stable date identity, real citations and deterministic output", () => {
  const xml = read("rss.xml")
  const outputData: unknown = JSON.parse(
    run("python3", [
      "-c",
      `import json,sys,xml.etree.ElementTree as E
r=E.parse(sys.argv[1]).getroot();c=r.find('channel');print(json.dumps([{'guid':i.findtext('guid'),'link':i.findtext('link'),'date':i.findtext('pubDate'),'body':i.findtext('description')} for i in c.findall('item')]))`,
      join(output, "rss.xml"),
    ]),
  )
  assert.ok(Array.isArray(outputData))
  const parsed = outputData.map((item: unknown) => {
    assert.ok(typeof item === "object" && item !== null)
    assert.ok("guid" in item && typeof item.guid === "string")
    assert.ok("link" in item && typeof item.link === "string")
    assert.ok("date" in item && typeof item.date === "string")
    assert.ok("body" in item && typeof item.body === "string")
    return { guid: item.guid, link: item.link, date: item.date, body: item.body }
  })
  assert.equal(parsed.length, 4)
  assert.deepEqual(
    parsed.map((item) => item.guid),
    [
      "https://daily.nishantkhurana.me/editions/2026-10-16/",
      "https://daily.nishantkhurana.me/editions/2026-10-15/",
      "https://daily.nishantkhurana.me/editions/2026-10-14/",
      "https://daily.nishantkhurana.me/editions/2026-05-10/",
    ],
  )
  const [latest, fourStories] = parsed
  assert.ok(latest && fourStories)
  assert.equal(fourStories.date, "Wed, 14 Oct 2026 18:30:00 GMT")
  assert.match(fourStories.body, /more than 30,000 per day/)
  assert.match(
    fourStories.body,
    /https:\/\/raw.githubusercontent.com\/Nutlope\/gloss\/main\/lib\/mcp.ts/,
  )
  assert.doesNotMatch(latest.body, /vendor-benchmark|benchmark setup/)
  assert.doesNotMatch(xml, /2026-10-17|<script/)
  for (const page of [
    "index.html",
    "search/index.html",
    "editions/2026-10-15/stories/gloss-x-import/index.html",
  ])
    assert.match(
      read(page),
      /rel="alternate"[^>]+type="application\/rss\+xml"[^>]+href="https:\/\/daily.nishantkhurana.me\/rss.xml"/,
    )
  assert.match(read("_headers"), /\/rss\.xml\s+Content-Type: application\/rss\+xml; charset=utf-8/)
  run(process.execPath, [join(app, "node_modules/astro/bin/astro.mjs"), "build"], fixtureApp)
  assert.equal(read("rss.xml"), xml)
  const source = join(fixtureRoot, "content/digests/x-ai-2026-10-15.md")
  writeFileSync(
    source,
    readFileSync(source, "utf8").replace(
      "Anthropic says it migrated",
      "Anthropic confirms it migrated",
    ),
  )
  run("git", ["add", "content"])
  run("git", [
    "-c",
    "user.name=Reader fixture",
    "-c",
    "user.email=reader@example.com",
    "commit",
    "-qm",
    "Correct headline",
  ])
  run(process.execPath, [join(app, "node_modules/astro/bin/astro.mjs"), "build"], fixtureApp)
  const revised = read("rss.xml")
  assert.equal((revised.match(/<item>/g) ?? []).length, 4)
  assert.match(revised, /Anthropic confirms/)
  assert.match(
    revised,
    /<guid isPermaLink="true">https:\/\/daily.nishantkhurana.me\/editions\/2026-10-15\/<\/guid>/,
  )
})

test("one shared source-backed figure appears on front, article, read view and full RSS", () => {
  const front = read("editions/2026-10-15/index.html")
  const figures =
    front.match(/<figure[^>]+data-story-visual="(?:bar|image)"[\s\S]*?<\/figure>/g) ?? []
  assert.equal(figures.length, 2)
  const full = read("editions/2026-10-15/read/index.html")
  const rssBody = run("python3", [
    "-c",
    "import sys,xml.etree.ElementTree as E; r=E.parse(sys.argv[1]); print(next(i.findtext('description') for i in r.findall('./channel/item') if '2026-10-15/' in i.findtext('guid')))",
    join(output, "rss.xml"),
  ])
  for (const figure of figures) {
    assert.ok(full.includes(figure))
    assert.ok(rssBody.includes(figure))
    const story = figure.includes('data-story-visual="bar"')
      ? "anthropic-monorepo"
      : "gloss-x-import"
    assert.ok(read(`editions/2026-10-15/stories/${story}/index.html`).includes(figure))
  }
  assert.match(rssBody, /~2,500/)
  assert.match(rssBody, /&gt;30,000/)
  assert.match(rssBody, /https:\/\/example.com\/launch.jpg\?a=1&amp;b=2/)
  assert.match(rssBody, /Two company-reported merge figures/)
})

test("sitemap contains actual native routes including retained archive articles", () => {
  const xml = read("sitemap.xml")
  run("python3", [
    "-c",
    "import sys,xml.etree.ElementTree as E; E.parse(sys.argv[1])",
    join(output, "sitemap.xml"),
  ])
  assert.match(
    xml,
    /https:\/\/daily.nishantkhurana.me\/editions\/2026-10-16\/stories\/vendor-benchmark\//,
  )
  assert.match(xml, /https:\/\/daily.nishantkhurana.me\/archive\//)
  assert.doesNotMatch(xml, /2026-10-17|404|2026-05-10\/stories/)
})

test("a quiet edition renders one complete story without supporting placeholders", () => {
  const front = read("editions/2026-10-14/index.html")
  assert.equal([...front.matchAll(/<article\b/g)].length, 1)
  assert.equal([...front.matchAll(/href="#reproducible-fix"/g)].length, 1)
  assert.match(front, /front-grid single-story/)
  assert.doesNotMatch(front, /lower-stories|side-story/)
  assert.match(front, /The report covers one tool version/)
  assert.match(front, /https:\/\/example\.com\/fix/)
  const story = read("editions/2026-10-14/stories/reproducible-fix/index.html")
  assert.match(story, /The report covers one tool version/)
  assert.doesNotMatch(story, /rel="(?:prev|next)"/)
})
