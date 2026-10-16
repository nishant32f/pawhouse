import { fields, object, string } from "./prose.ts"

export type ObjectRef = { key: string; sha256: string; contentType: string; byteLength: number }
export type Manifest = {
  schemaVersion: 1
  compilerRevision: string
  editions: { date: string; sourceSha256: string; object: ObjectRef }[]
  catalog: ObjectRef
  routes: ObjectRef
  search: ObjectRef
  rss: ObjectRef
}
export type Head = { schemaVersion: 1; manifest: ObjectRef }
export function decodeObjectRef(value: unknown): ObjectRef {
  const data = object(value)
  fields(data, ["key", "sha256", "contentType", "byteLength"])
  const sha256 = string(data.sha256)
  if (!/^[a-f0-9]{64}$/.test(sha256)) throw new Error("invalid object hash")
  const key = string(data.key)
  const contentType = string(data.contentType)
  if (
    contentType !== "application/json; charset=utf-8" &&
    contentType !== "application/rss+xml; charset=utf-8"
  )
    throw new Error("unsupported content type")
  const extension = contentType.startsWith("application/rss+xml") ? "xml" : "json"
  if (key !== `v1/objects/${sha256}.${extension}` && key !== `v1/manifests/${sha256}.json`)
    throw new Error("object key must address its hash")
  if (
    typeof data.byteLength !== "number" ||
    !Number.isSafeInteger(data.byteLength) ||
    data.byteLength <= 0
  )
    throw new Error("invalid object byte length")
  return { key, sha256, contentType, byteLength: data.byteLength }
}
export function decodeHead(value: unknown): Head {
  const data = object(value)
  fields(data, ["schemaVersion", "manifest"])
  if (data.schemaVersion !== 1) throw new Error("unsupported head schemaVersion")
  const manifest = decodeObjectRef(data.manifest)
  if (
    !manifest.key.startsWith("v1/manifests/") ||
    manifest.contentType !== "application/json; charset=utf-8"
  )
    throw new Error("head must reference a JSON manifest")
  return { schemaVersion: 1, manifest }
}
export function decodeManifest(value: unknown): Manifest {
  const data = object(value)
  fields(data, [
    "schemaVersion",
    "compilerRevision",
    "editions",
    "catalog",
    "routes",
    "search",
    "rss",
  ])
  if (data.schemaVersion !== 1) throw new Error("unsupported manifest schemaVersion")
  const compilerRevision = string(data.compilerRevision)
  if (!compilerRevision.trim()) throw new Error("compiler revision is required")
  if (!Array.isArray(data.editions)) throw new Error("manifest requires editions")
  const editions = data.editions.map((value) => {
    const entry = object(value)
    fields(entry, ["date", "sourceSha256", "object"])
    const date = string(entry.date)
    if (
      !/^\d{4}-\d{2}-\d{2}$/.test(date) ||
      new Date(`${date}T00:00:00Z`).toISOString().slice(0, 10) !== date
    )
      throw new Error("invalid manifest edition date")
    const sourceSha256 = string(entry.sourceSha256)
    if (!/^[a-f0-9]{64}$/.test(sourceSha256)) throw new Error("invalid edition source hash")
    const ref = decodeObjectRef(entry.object)
    if (!ref.key.startsWith("v1/objects/") || ref.contentType !== "application/json; charset=utf-8")
      throw new Error("edition must reference JSON content")
    return { date, sourceSha256, object: ref }
  })
  if (editions.some((entry, i) => i > 0 && entry.date >= (editions[i - 1]?.date ?? "")))
    throw new Error("manifest editions must have unique dates newest first")
  const catalog = decodeObjectRef(data.catalog)
  const routes = decodeObjectRef(data.routes)
  const search = decodeObjectRef(data.search)
  const rss = decodeObjectRef(data.rss)
  if (
    [catalog, routes, search].some(
      (ref) =>
        !ref.key.startsWith("v1/objects/") || ref.contentType !== "application/json; charset=utf-8",
    ) ||
    !rss.key.startsWith("v1/objects/") ||
    rss.contentType !== "application/rss+xml; charset=utf-8"
  )
    throw new Error("invalid manifest discovery object")
  return { schemaVersion: 1, compilerRevision, editions, catalog, routes, search, rss }
}
