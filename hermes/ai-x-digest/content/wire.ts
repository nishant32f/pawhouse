import type {
  ActiveStory,
  ArchivedStory,
  Edition,
  LegacyEdition,
  IdentifiedEdition,
  Source,
  Story,
} from "./parser.ts"
import { parseStoryMetadata, type StoryEditorial } from "./editorial.ts"
import { decodeProse, fields, object, proseHtml, proseText, safeUrl, string } from "./prose.ts"

type WireStoryFields = Pick<
  Story,
  | "id"
  | "legacyAnchor"
  | "anchors"
  | "headline"
  | "path"
  | "editionPath"
  | "sources"
  | "editorial"
  | "prose"
  | "summaryProse"
>
export type WireStory = WireStoryFields &
  ({ kind: "story" | "brief" } | { kind: "archived"; correction: string })
type WireEditionFields = Pick<
  Edition,
  | "date"
  | "title"
  | "publishedAt"
  | "path"
  | "readPath"
  | "sourceSha256"
  | "sources"
  | "prose"
  | "anchors"
> & { schemaVersion: 1 }
export type WireEdition = WireEditionFields &
  (
    | { kind: "legacy"; format: "editorial-v1" | null }
    | { kind: "identified"; format: "editorial-v2"; stories: WireStory[] }
  )

function anchors(value: unknown): string[] {
  if (!Array.isArray(value)) throw new Error("anchors must be an array")
  return value.map((value) => {
    const id = string(value)
    if (/[\s\u0000-\u001f\"<>]/.test(id)) throw new Error("unsafe heading anchor")
    return id
  })
}
function sources(value: unknown): Source[] {
  if (!Array.isArray(value)) throw new Error("sources must be an array")
  return value.map((item) => {
    const data = object(item)
    fields(data, ["label", "url"])
    const url = safeUrl(data.url)
    if (!url.startsWith("https://")) throw new Error("source must use HTTPS")
    return { label: string(data.label), url }
  })
}
function editorial(value: unknown, id: string, citations: Source[]): StoryEditorial | null {
  if (value === null) return null
  const data = object(value)
  fields(data, ["section", "deck", "visual"])
  const authored: Record<string, unknown> = { section: data.section }
  if (data.deck !== null) authored.deck = data.deck
  if (data.visual !== null) {
    const visual = object(data.visual)
    const common = ["kind", "caption", "source"]
    fields(visual, [
      ...common,
      ...(visual.kind === "image"
        ? ["src", "width", "height", "alt", "credit"]
        : ["title", "unit", "points"]),
    ])
    const source = sources([visual.source])[0]
    if (
      !source ||
      !citations.some((item) => item.url === source.url && item.label === source.label)
    )
      throw new Error("visual source must belong to its story")
    const { source: _source, ...rest } = visual
    authored.visual = { ...rest, source_url: source.url }
  }
  return parseStoryMetadata({ [id]: authored }, [{ id, sources: citations }]).get(id) ?? null
}
function story(value: unknown, editionPath: string): WireStory {
  const data = object(value)
  fields(data, [
    "kind",
    "id",
    "legacyAnchor",
    "anchors",
    "headline",
    "path",
    "editionPath",
    "sources",
    "editorial",
    "prose",
    "summaryProse",
    ...(data.kind === "archived" ? ["correction"] : []),
  ])
  const id = string(data.id)
  if (
    !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id) ||
    data.path !== `${editionPath}stories/${id}/` ||
    data.editionPath !== editionPath
  )
    throw new Error("invalid story identity")
  const citations = sources(data.sources)
  if (!citations.length) throw new Error("story requires adjacent source")
  const common = {
    id,
    legacyAnchor: anchors([data.legacyAnchor])[0] ?? "",
    anchors: anchors(data.anchors),
    headline: string(data.headline),
    path: `${editionPath}stories/${id}/`,
    editionPath,
    sources: citations,
    editorial: editorial(data.editorial, id, citations),
    prose: decodeProse(data.prose),
    summaryProse: decodeProse(data.summaryProse),
  }
  if (data.kind === "archived") {
    const correction = string(data.correction)
    if (!correction.trim()) throw new Error("archived story needs a correction")
    return { ...common, kind: "archived", correction }
  }
  if (data.kind !== "story" && data.kind !== "brief") throw new Error("unknown story kind")
  return { ...common, kind: data.kind }
}

export function decodeEdition(value: unknown): WireEdition {
  const data = object(value)
  fields(data, [
    "schemaVersion",
    "kind",
    "format",
    "date",
    "title",
    "publishedAt",
    "path",
    "readPath",
    "sourceSha256",
    "sources",
    "prose",
    "anchors",
    ...(data.kind === "identified" ? ["stories"] : []),
  ])
  if (data.schemaVersion !== 1) throw new Error("unsupported edition schemaVersion")
  const date = string(data.date)
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
    new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) !== date
  )
    throw new Error("invalid edition date")
  const path = `/editions/${date}/`
  if (
    data.path !== path ||
    data.readPath !== `${path}read/` ||
    data.publishedAt !== `${date}T00:00:00+05:30`
  )
    throw new Error("invalid edition paths or publication date")
  const hash = string(data.sourceSha256)
  if (!/^[a-f0-9]{64}$/.test(hash)) throw new Error("invalid source hash")
  const common: WireEditionFields = {
    schemaVersion: 1,
    anchors: anchors(data.anchors),
    date,
    title: string(data.title),
    publishedAt: `${date}T00:00:00+05:30`,
    path,
    readPath: `${path}read/`,
    sourceSha256: hash,
    sources: sources(data.sources),
    prose: decodeProse(data.prose),
  }
  if (data.kind === "legacy" && (data.format === null || data.format === "editorial-v1"))
    return { ...common, kind: "legacy", format: data.format }
  if (data.kind !== "identified" || data.format !== "editorial-v2" || !Array.isArray(data.stories))
    throw new Error("invalid edition format")
  const stories = data.stories.map((item) => story(item, path))
  if (stories[0]?.kind !== "story" || new Set(stories.map((s) => s.id)).size !== stories.length)
    throw new Error("invalid lead or duplicate story IDs")
  if (
    JSON.stringify(common.sources) !==
    JSON.stringify(stories.filter((s) => s.kind !== "archived").flatMap((s) => s.sources))
  )
    throw new Error("edition sources differ from active story sources")
  return { ...common, kind: "identified", format: "editorial-v2", stories }
}

export type ReadActiveStory = Omit<ActiveStory, "markdown" | "bodyMarkdown">
export type ReadArchivedStory = Omit<ArchivedStory, "markdown" | "bodyMarkdown">
export type ReadStory = ReadActiveStory | ReadArchivedStory
export type ReadEdition =
  | Omit<LegacyEdition, "sourcePath" | "originalMarkdown" | "hasRawHtml">
  | (Omit<
      IdentifiedEdition,
      | "sourcePath"
      | "originalMarkdown"
      | "hasRawHtml"
      | "stories"
      | "activeStories"
      | "archivedStories"
      | "lead"
    > & {
      stories: ReadStory[]
      activeStories: ReadActiveStory[]
      archivedStories: ReadArchivedStory[]
      lead: ReadActiveStory
    })
function materializeStory(story: WireStory): ReadStory {
  const common = {
    ...story,
    html: proseHtml(story.prose, story.anchors),
    text: proseText(story.prose),
    summaryHtml: proseHtml(story.summaryProse),
    summary: proseText(story.summaryProse),
  }
  if (story.kind === "archived")
    return { ...common, kind: "archived", correction: story.correction }
  return { ...common, kind: story.kind }
}
export function materializeEdition(edition: WireEdition): ReadEdition {
  const common = {
    ...edition,
    html: proseHtml(edition.prose, edition.anchors),
    text: proseText(edition.prose),
  }
  if (edition.kind === "legacy") return { ...common, kind: "legacy", format: edition.format }
  const stories = edition.stories.map(materializeStory)
  const activeStories = stories.filter((s): s is ReadActiveStory => s.kind !== "archived")
  const archivedStories = stories.filter((s): s is ReadArchivedStory => s.kind === "archived")
  const lead = activeStories[0]
  if (!lead) throw new Error("missing lead")
  return {
    ...common,
    kind: "identified",
    format: "editorial-v2",
    stories,
    activeStories,
    archivedStories,
    lead,
  }
}
