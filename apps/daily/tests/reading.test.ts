import assert from "node:assert/strict"
import { execFileSync } from "node:child_process"
import {
  mkdirSync,
  mkdtempSync,
  readFileSync,
  rmSync,
  writeFileSync,
  existsSync,
  readdirSync,
} from "node:fs"
import { tmpdir } from "node:os"
import { dirname, join, resolve } from "node:path"
import { after, before, test } from "node:test"
import { Miniflare, type WorkerOptions } from "miniflare"
import { decodeEdition } from "../../../hermes/ai-x-digest/content/wire.ts"
import { compileRepository } from "../../../hermes/ai-x-digest/content/compiler.ts"

const app = resolve(import.meta.dirname, "..")
const fixtureRoot = mkdtempSync(join(tmpdir(), "daily-reading-"))
const output = join(fixtureRoot, "responses")
const read = (path: string) => readFileSync(join(output, path), "utf8")
const run = (command: string, args: string[], cwd = app) =>
  execFileSync(command, args, { cwd, encoding: "utf8", stdio: "pipe" })
let worker: Miniflare
let bucket: Awaited<ReturnType<Miniflare["getR2Bucket"]>>
const headers = new Map<string, Headers>()
const inputs = [
  ["editorial-v2-four-stories.md", "2026-10-15"],
  ["editorial-v2-brief-archive.md", "2026-10-16"],
  ["editorial-v2-single-story.md", "2026-10-14"],
  ["legacy-unversioned.md", "2026-05-10"],
].map(([file, date]) => ({
  filename: `x-ai-${date}.md`,
  text: readFileSync(join(app, "tests/fixtures", file ?? ""), "utf8"),
}))
const illustrated = inputs[0]
assert.ok(illustrated)
illustrated.text = illustrated.text.replace(
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
)
const publication = () =>
  compileRepository(inputs, { compilerRevision: "reading-fixture-compiler" })
async function publish(compiled = publication()) {
  for (const object of compiled.objects)
    await bucket.put(object.key, object.bytes, {
      httpMetadata: { contentType: object.contentType },
    })
  await bucket.put("v1/head.json", JSON.stringify(compiled.head))
  return compiled
}
async function provenance() {
  const value: unknown = await (await fetchPath("/deployment.json")).json()
  assert.ok(
    value &&
      typeof value === "object" &&
      "codeRevision" in value &&
      typeof value.codeRevision === "string" &&
      "publicationRevision" in value &&
      typeof value.publicationRevision === "string",
  )
  return { codeRevision: value.codeRevision, publicationRevision: value.publicationRevision }
}
async function fetchPath(path: string) {
  return worker.dispatchFetch(`https://daily.nishantkhurana.me${path}`)
}
before(
  async () => {
    // This build is invoked by the test runner, never against a production binding.
    run(process.execPath, [join(app, "node_modules/astro/bin/astro.mjs"), "build"])
    const server = join(app, "dist/server")
    const config = JSON.parse(readFileSync(join(server, "wrangler.json"), "utf8"))
    const modules: NonNullable<WorkerOptions["config"]["manifest"]>["modules"] = {}
    for (const file of readdirSync(server, { recursive: true, encoding: "utf8" })) {
      if (file.endsWith(".mjs") || file.endsWith(".js"))
        modules[file] = { type: "esm", contents: readFileSync(join(server, file), "utf8") }
    }
    worker = new Miniflare({
      workers: [
        {
          config: {
            name: "daily-reading-fixture",
            compatibilityDate: config.compatibility_date,
            compatibilityFlags: config.compatibility_flags,
            manifest: { mainModule: config.main, modulesRoot: server, modules },
            env: {
              DAILY_CONTENT: { type: "r2", name: "daily-reading-fixture", dev: { remote: false } },
              ASSETS: { type: "assets" },
            },
            assets: {
              directory: resolve(server, config.assets.directory),
              notFoundHandling: "404-page",
              hasUserWorker: true,
            },
          },
        },
      ],
    })
    bucket = await worker.getR2Bucket("DAILY_CONTENT")
    await publish()
    const provenance: unknown = await (await fetchPath("/deployment.json")).json()
    assert.ok(
      provenance &&
        typeof provenance === "object" &&
        "routes" in provenance &&
        Array.isArray(provenance.routes),
    )
    assert.ok(provenance.routes.every((path): path is string => typeof path === "string"))
    for (const path of [...provenance.routes, "/404.html"]) {
      const response = await fetchPath(path)
      headers.set(path, new Headers([...response.headers.entries()]))
      const file = path.endsWith("/") ? `${path.slice(1)}index.html` : path.slice(1)
      const destination = join(output, file)
      mkdirSync(dirname(destination), { recursive: true })
      writeFileSync(destination, await response.text())
    }
  },
  { timeout: 120000 },
)
after(async () => {
  await worker?.dispose()
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
  assert.match(front, /Machine Herald/)
  assert.doesNotMatch(front, /data-print|print-edition|A daily paper on artificial intelligence/)
})

test("request-time article routes contain complete prose, adjacent sources and active navigation", () => {
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
    assert.match(html, /href="\/editions\/2026-10-16\/stories\/vendor-benchmark\/"/)
    assert.doesNotMatch(html, /The vendor reported a faster benchmark|The vendor withdrew/)
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

test("RSS has full sanitized editions, stable date identity, real citations and deterministic output", async () => {
  const xml = read("rss.xml")
  assert.match(xml, /<channel><title>Machine Herald<\/title>/)
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
  assert.equal(headers.get("/rss.xml")?.get("content-type"), "application/rss+xml; charset=utf-8")
  assert.equal(await (await fetchPath("/rss.xml")).text(), xml)
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
    // The neutral feed keeps the facts in accessible markup, independent of newspaper CSS.
    const story = figure.includes('data-story-visual="bar"')
      ? "anthropic-monorepo"
      : "gloss-x-import"
    assert.ok(read(`editions/2026-10-15/stories/${story}/index.html`).includes(figure))
  }
  assert.match(rssBody, /~2,500/)
  assert.match(rssBody, /&gt;30,000/)
  assert.match(rssBody, /https:\/\/example.com\/launch.jpg\?a=1&amp;b=2/)
  assert.match(rssBody, /Two company-reported merge figures/)
  assert.match(rssBody, /<table>/)
  assert.match(rssBody, /Reported code merges/)
  assert.match(rssBody, /merges per day/)
  assert.doesNotMatch(rssBody, /bar-track|bar-fill|<svg/)
  assert.match(rssBody, /Saved article in the launch demonstration/)
  assert.match(rssBody, /A source image with an adjacent citation/)
  assert.match(rssBody, /Hassan/)
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

test("one built Worker follows publication B across every mutable reading route", async () => {
  const before = await provenance()
  const original = illustrated.text
  try {
    illustrated.text = original.replace(
      "Anthropic says it migrated",
      "Anthropic confirms it migrated",
    )
    const latest = inputs.find((input) => input.filename === "x-ai-2026-10-16.md")
    assert.ok(latest)
    const latestOriginal = latest.text
    latest.text = latest.text.replace(
      "A developer publishes a reproducible test",
      "A developer confirms a reproducible test",
    )
    const b = await publish()
    latest.text = latestOriginal
    const after = await provenance()
    assert.equal(after.codeRevision, before.codeRevision)
    assert.equal(after.publicationRevision, b.head.manifest.sha256)
    assert.notEqual(after.publicationRevision, before.publicationRevision)
    for (const path of [
      "/",
      "/archive/",
      "/search/",
      "/editions/2026-10-15/stories/anthropic-monorepo/",
      "/sitemap.xml",
      "/rss.xml",
    ]) {
      const response = await fetchPath(path)
      assert.equal(response.status, 200, path)
      assert.equal(response.headers.get("cache-control"), "no-store", path)
      const text = await response.text()
      if (path === "/") assert.match(text, /A developer confirms/)
      if (
        [
          "/archive/",
          "/search/",
          "/editions/2026-10-15/stories/anthropic-monorepo/",
          "/rss.xml",
        ].includes(path)
      )
        assert.match(text, /Anthropic confirms/)
    }
    for (const path of [
      "/editions/2026-10-17/",
      "/editions/2026-10-15/stories/absent/",
      "/_astro/missing.css",
    ])
      assert.equal((await fetchPath(path)).status, 404, path)
    const search = await (await fetchPath("/search/?q=vendor")).text()
    assert.match(search, /vendor-benchmark/)
    assert.match(search, /The vendor reported a faster benchmark/)
    const emptySearch = await (await fetchPath("/search/?q=zzznomatches")).text()
    assert.match(emptySearch, /id="search-status">0 matches/)
    assert.match(emptySearch, /<p id="no-matches">No matches/)
    const newest = b.manifest.editions[0]
    assert.ok(newest)
    await bucket.delete(newest.object.key)
    assert.equal((await fetchPath("/")).status, 503)
    await bucket.put("v1/head.json", '{"schemaVersion":2}')
    assert.equal((await fetchPath("/archive/")).status, 503)
  } finally {
    illustrated.text = original
    await publish()
  }
})

test("the retained accepted twelve-story edition keeps complete reading and original source links", async () => {
  const accepted = compileRepository(
    [
      {
        filename: "x-ai-2026-10-16.md",
        text: readFileSync(
          join(app, "tests/fixtures/accepted-2026-10-16-twelve-stories.md"),
          "utf8",
        ),
      },
    ],
    { compilerRevision: "reading-fixture-compiler" },
  )
  try {
    await publish(accepted)
    const edition = decodeEdition(
      JSON.parse(
        accepted.objects.find((object) => object.key === accepted.manifest.editions[0]?.object.key)
          ?.bytes ?? "null",
      ),
    )
    assert.equal(edition.kind, "identified")
    if (edition.kind !== "identified") return
    assert.equal(edition.stories.length, 12)
    const home = await (await fetchPath("/")).text()
    assert.equal((home.match(/<article\b[^>]*class="newspaper-story/g) ?? []).length, 12)
    const full = await (await fetchPath("/editions/2026-10-16/read/")).text()
    for (const story of edition.stories) {
      const article = await fetchPath(story.path)
      assert.equal(article.status, 200)
      const body = await article.text()
      assert.ok(full.includes(story.id))
      for (const source of story.sources)
        assert.ok(body.includes(source.url.replaceAll("&", "&amp;")))
    }
  } finally {
    await publish()
  }
})

test("old story, brief and archived heading fragments lead to retained content", () => {
  const compiled = publication()
  const entry = compiled.manifest.editions.find((edition) => edition.date === "2026-10-16")
  const object = compiled.objects.find((object) => object.key === entry?.object.key)
  assert.ok(object)
  const edition = decodeEdition(JSON.parse(object.bytes))
  assert.equal(edition.kind, "identified")
  if (edition.kind !== "identified") return
  for (const file of ["editions/2026-10-16/index.html", "editions/2026-10-16/read/index.html"]) {
    const html = read(file)
    assert.match(html, /id="in-brief"/)
    assert.match(html, /id="archived-stories"/)
    for (const story of edition.stories) {
      assert.ok(html.includes(`id="${story.id}"`))
      assert.ok(html.includes(`id="${story.legacyAnchor}"`))
      if (story.kind === "archived") assert.ok(html.includes(`href="${story.path}"`))
    }
  }
})


test("search retains one copy of full text and native title queries", async () => {
  const search = read("search/index.html")
  assert.equal(search.split("Original imported wording remains intact.").length - 1, 1)
  const response = await fetchPath("/search/?q=X-AI-2026-05-10")
  assert.equal(response.status, 200)
  const html = await response.text()
  const result = [...html.matchAll(/<li\b[^>]*>[\s\S]*?<\/li>/g)].find((match) =>
    match[0].includes('href="/editions/2026-05-10/"'),
  )
  assert.ok(result)
  assert.doesNotMatch(result[0].split(">")[0] ?? "", /\bhidden/)
})
