import {
  decodeHead,
  decodeManifest,
  type ObjectRef,
} from "../../../../hermes/ai-x-digest/content/storage.ts"
import {
  decodeCatalog,
  decodeRoutes,
  decodeSearch,
} from "../../../../hermes/ai-x-digest/content/discovery.ts"
import { decodeEdition, materializeEdition } from "../../../../hermes/ai-x-digest/content/wire.ts"

export interface ReadObject {
  size: number
  body: ReadableStream<Uint8Array>
  arrayBuffer(): Promise<ArrayBuffer>
}
// The application exposes reads only. Native R2 bindings themselves also permit writes.
export interface ReadBucket {
  get(key: string): Promise<ReadObject | null>
}
export class PublicationUnavailable extends Error {
  constructor() {
    super("Published content is temporarily unavailable")
  }
}
async function available<T>(read: () => Promise<T>): Promise<T> {
  try {
    return await read()
  } catch {
    throw new PublicationUnavailable()
  }
}
async function referenced(bucket: ReadBucket, ref: ObjectRef): Promise<ReadObject> {
  const object = await bucket.get(ref.key)
  if (!object || object.size !== ref.byteLength) throw new PublicationUnavailable()
  return object
}
async function json(bucket: ReadBucket, ref: ObjectRef): Promise<unknown> {
  const bytes = await (await referenced(bucket, ref)).arrayBuffer()
  const hash = Array.from(new Uint8Array(await crypto.subtle.digest("SHA-256", bytes)), (byte) =>
    byte.toString(16).padStart(2, "0"),
  ).join("")
  if (bytes.byteLength !== ref.byteLength || hash !== ref.sha256) throw new PublicationUnavailable()
  return JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(bytes))
}
export async function selectPublication(bucket: ReadBucket) {
  return available(async () => {
    const object = await bucket.get("v1/head.json")
    if (!object) throw new PublicationUnavailable()
    const head = decodeHead(
      JSON.parse(new TextDecoder("utf-8", { fatal: true }).decode(await object.arrayBuffer())),
    )
    const manifest = decodeManifest(await json(bucket, head.manifest))
    return {
      publicationRevision: head.manifest.sha256,
      compilerRevision: manifest.compilerRevision,
      manifest,
      catalog: () =>
        available(async () => {
          const catalog = decodeCatalog(await json(bucket, manifest.catalog))
          if (
            catalog.editions.length !== manifest.editions.length ||
            catalog.editions.some(
              (edition, index) => edition.date !== manifest.editions[index]?.date,
            )
          )
            throw new PublicationUnavailable()
          return catalog
        }),
      routes: () => available(async () => decodeRoutes(await json(bucket, manifest.routes))),
      search: () => available(async () => decodeSearch(await json(bucket, manifest.search))),
      edition: (date = manifest.editions[0]?.date) =>
        available(async () => {
          const entry = manifest.editions.find((edition) => edition.date === date)
          if (!entry) return undefined
          const edition = decodeEdition(await json(bucket, entry.object))
          if (edition.date !== entry.date || edition.sourceSha256 !== entry.sourceSha256)
            throw new PublicationUnavailable()
          return materializeEdition(edition)
        }),
      rss: () =>
        available(async () => {
          const object = await referenced(bucket, manifest.rss)
          return new Response(object.body, {
            headers: {
              "Content-Type": manifest.rss.contentType,
              "Content-Length": String(manifest.rss.byteLength),
              "Cache-Control": "no-store",
            },
          })
        }),
    }
  })
}
export type Publication = Awaited<ReturnType<typeof selectPublication>>
