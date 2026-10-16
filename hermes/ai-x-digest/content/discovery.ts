import { fields, object, string } from "./prose.ts"

export type CatalogStory = {
  id: string
  headline: string
  path: string
  kind: "story" | "brief" | "archived"
}
export type CatalogEdition = {
  date: string
  title: string
  path: string
  readPath: string
  publishedAt: string
  kind: "legacy" | "identified"
  stories: CatalogStory[]
}
export type Catalog = { schemaVersion: 1; editions: CatalogEdition[] }
export type Route =
  | { path: string; date: string; kind: "edition" | "read" }
  | { path: string; date: string; kind: "story"; storyId: string }
export type Routes = { schemaVersion: 1; routes: Route[] }
export type SearchDocument = { path: string; date: string; title: string; text: string }
export type Search = { schemaVersion: 1; documents: SearchDocument[] }
function date(value: unknown): string {
  const valueString = string(value)
  if (
    !/^\d{4}-\d{2}-\d{2}$/.test(valueString) ||
    new Date(`${valueString}T00:00:00Z`).toISOString().slice(0, 10) !== valueString
  )
    throw new Error("invalid discovery date")
  return valueString
}
function id(value: unknown): string {
  const valueString = string(value)
  if (!/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(valueString)) throw new Error("invalid discovery story ID")
  return valueString
}
function envelope(value: unknown, field: string): unknown[] {
  const data = object(value)
  fields(data, ["schemaVersion", field])
  if (data.schemaVersion !== 1 || !Array.isArray(data[field]))
    throw new Error("unsupported discovery schema")
  return data[field]
}
export function decodeCatalog(value: unknown): Catalog {
  const editions = envelope(value, "editions").map((value): CatalogEdition => {
    const data = object(value)
    fields(data, ["date", "title", "path", "readPath", "publishedAt", "kind", "stories"])
    const day = date(data.date)
    const path = `/editions/${day}/`
    if (
      data.path !== path ||
      data.readPath !== `${path}read/` ||
      data.publishedAt !== `${day}T00:00:00+05:30` ||
      (data.kind !== "legacy" && data.kind !== "identified") ||
      !Array.isArray(data.stories)
    )
      throw new Error("invalid catalog edition")
    const stories = data.stories.map((value): CatalogStory => {
      const story = object(value)
      fields(story, ["id", "headline", "path", "kind"])
      const storyId = id(story.id)
      if (
        story.path !== `${path}stories/${storyId}/` ||
        (story.kind !== "story" && story.kind !== "brief" && story.kind !== "archived")
      )
        throw new Error("invalid catalog story")
      return {
        id: storyId,
        headline: string(story.headline),
        path: `${path}stories/${storyId}/`,
        kind: story.kind,
      }
    })
    if (
      (data.kind === "legacy" && stories.length) ||
      (data.kind === "identified" && stories[0]?.kind !== "story") ||
      new Set(stories.map((s) => s.id)).size !== stories.length
    )
      throw new Error("invalid catalog story membership")
    return {
      date: day,
      title: string(data.title),
      path,
      readPath: `${path}read/`,
      publishedAt: `${day}T00:00:00+05:30`,
      kind: data.kind,
      stories,
    }
  })
  if (editions.some((entry, i) => i > 0 && entry.date >= (editions[i - 1]?.date ?? "")))
    throw new Error("catalog editions must have unique dates newest first")
  return { schemaVersion: 1, editions }
}
export function decodeRoutes(value: unknown): Routes {
  const routes = envelope(value, "routes").map((value): Route => {
    const data = object(value)
    fields(data, ["path", "date", "kind", ...(data.kind === "story" ? ["storyId"] : [])])
    const day = date(data.date)
    const base = `/editions/${day}/`
    if (data.kind === "story") {
      const storyId = id(data.storyId)
      if (data.path !== `${base}stories/${storyId}/`) throw new Error("invalid story route")
      return { date: day, path: `${base}stories/${storyId}/`, kind: "story", storyId }
    }
    if (
      (data.kind !== "edition" && data.kind !== "read") ||
      data.path !== (data.kind === "edition" ? base : `${base}read/`)
    )
      throw new Error("invalid edition route")
    return { date: day, path: string(data.path), kind: data.kind }
  })
  if (new Set(routes.map((route) => route.path)).size !== routes.length)
    throw new Error("duplicate route")
  return { schemaVersion: 1, routes }
}
export function decodeSearch(value: unknown): Search {
  const documents = envelope(value, "documents").map((value) => {
    const data = object(value)
    fields(data, ["path", "date", "title", "text"])
    const day = date(data.date)
    const path = string(data.path)
    if (
      path !== `/editions/${day}/` &&
      !new RegExp(`^/editions/${day}/stories/[a-z0-9]+(?:-[a-z0-9]+)*/$`).test(path)
    )
      throw new Error("invalid search route")
    return { path, date: day, title: string(data.title), text: string(data.text) }
  })
  if (new Set(documents.map((document) => document.path)).size !== documents.length)
    throw new Error("duplicate search path")
  return { schemaVersion: 1, documents }
}
