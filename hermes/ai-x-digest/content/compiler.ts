import { createHash } from "node:crypto"
import { parseEdition, parseEditions, type EditionInput, type Story } from "./parser.ts"
import { decodeEdition, type WireEdition, type WireStory } from "./wire.ts"
import { serializeRss } from "./syndication.ts"
import { decodeCatalog, decodeRoutes, decodeSearch } from "./discovery.ts"
import { proseText } from "./prose.ts"

import { decodeHead, decodeManifest, type ObjectRef, type Manifest, type Head } from "./storage.ts"
export type { ObjectRef, Manifest, Head } from "./storage.ts"
export type ExportObject = ObjectRef & { bytes: string }
export type ExportOptions = { compilerRevision: string; site?: string }

function wireStory(story: Story): WireStory {
  const common = {
    id: story.id,
    legacyAnchor: story.legacyAnchor,
    anchors: story.anchors,
    headline: story.headline,
    path: story.path,
    editionPath: story.editionPath,
    sources: story.sources,
    editorial: story.editorial,
    prose: story.prose,
    summaryProse: story.summaryProse,
  }
  return story.kind === "archived"
    ? { ...common, kind: "archived", correction: story.correction }
    : { ...common, kind: story.kind }
}
function toWire(edition: ReturnType<typeof parseEdition>): WireEdition {
  if (edition.hasRawHtml) throw new Error("raw HTML is not allowed in published content")
  const common = {
    schemaVersion: 1,
    anchors: edition.anchors,
    date: edition.date,
    title: edition.title,
    publishedAt: edition.publishedAt,
    path: edition.path,
    readPath: edition.readPath,
    sourceSha256: edition.sourceSha256,
    sources: edition.sources,
    prose: edition.prose,
  }
  return decodeEdition(
    edition.kind === "legacy"
      ? { ...common, kind: edition.kind, format: edition.format }
      : {
          ...common,
          kind: edition.kind,
          format: edition.format,
          stories: edition.stories.map(wireStory),
        },
  )
}
export function compileEdition(input: EditionInput): WireEdition {
  return toWire(parseEdition(input))
}
export function jsonBytes(value: unknown): string {
  return JSON.stringify(value) + "\n"
}
export function compileRepository(inputs: EditionInput[], options: ExportOptions) {
  if (!options.compilerRevision.trim()) throw new Error("compilerRevision is required")
  const editions = parseEditions(inputs).map(toWire)
  const objects: ExportObject[] = []
  function add(bytes: string, contentType: string, manifest = false): ObjectRef {
    const sha256 = createHash("sha256").update(bytes).digest("hex")
    const key = `v1/${manifest ? "manifests" : "objects"}/${sha256}.${contentType.startsWith("application/rss+xml") ? "xml" : "json"}`
    const ref = { key, sha256, contentType, byteLength: Buffer.byteLength(bytes, "utf8") }
    if (!objects.some((o) => o.key === key)) objects.push({ ...ref, bytes })
    return ref
  }
  const entries = editions.map((edition) => ({
    date: edition.date,
    sourceSha256: edition.sourceSha256,
    object: add(jsonBytes(edition), "application/json; charset=utf-8"),
  }))
  const catalog = add(
    jsonBytes(
      decodeCatalog({
        schemaVersion: 1,
        editions: editions.map((edition) => ({
          date: edition.date,
          title: edition.title,
          path: edition.path,
          readPath: edition.readPath,
          publishedAt: edition.publishedAt,
          kind: edition.kind,
          stories:
            edition.kind === "identified"
              ? edition.stories.map((s) => ({
                  id: s.id,
                  headline: s.headline,
                  path: s.path,
                  kind: s.kind,
                }))
              : [],
        })),
      }),
    ),
    "application/json; charset=utf-8",
  )
  const routes = add(
    jsonBytes(
      decodeRoutes({
        schemaVersion: 1,
        routes: editions.flatMap((edition) => [
          { path: edition.path, kind: "edition", date: edition.date },
          { path: edition.readPath, kind: "read", date: edition.date },
          ...(edition.kind === "identified"
            ? edition.stories.map((s) => ({
                path: s.path,
                kind: "story",
                date: edition.date,
                storyId: s.id,
              }))
            : []),
        ]),
      }),
    ),
    "application/json; charset=utf-8",
  )
  const search = add(
    jsonBytes(
      decodeSearch({
        schemaVersion: 1,
        documents: editions.flatMap((edition) => [
          {
            path: edition.path,
            date: edition.date,
            title: edition.title,
            text: proseText(edition.prose),
          },
          ...(edition.kind === "identified"
            ? edition.stories.map((s) => ({
                path: s.path,
                date: edition.date,
                title: s.headline,
                text: proseText(s.prose),
              }))
            : []),
        ]),
      }),
    ),
    "application/json; charset=utf-8",
  )
  const rss = add(serializeRss(editions, options.site), "application/rss+xml; charset=utf-8")
  const manifest: Manifest = {
    schemaVersion: 1,
    compilerRevision: options.compilerRevision,
    editions: entries,
    catalog,
    routes,
    search,
    rss,
  }
  const head: Head = {
    schemaVersion: 1,
    manifest: add(jsonBytes(manifest), "application/json; charset=utf-8", true),
  }
  return { manifest: decodeManifest(manifest), head: decodeHead(head), objects }
}
