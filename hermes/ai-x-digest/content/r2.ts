import { createHash } from "node:crypto"
import { readFile } from "node:fs/promises"
import { join } from "node:path"
import { S3Client, GetObjectCommand, PutObjectCommand } from "@aws-sdk/client-s3"
import { decodeHead, decodeManifest, type Head, type ObjectRef } from "./storage.ts"

export type StoredObject = { bytes: Uint8Array; etag: string }
export interface ObjectStore {
  get(key: string): Promise<StoredObject | null>
  put(
    key: string,
    bytes: Uint8Array,
    contentType: string,
    condition: { etag: string } | { absent: true },
  ): Promise<void>
}
export type Expected = { manifestSha256: string | null; etag: string | null }
export type Bundle = { head: Head; objects: ObjectRef[] }
const hash = (bytes: Uint8Array) => createHash("sha256").update(bytes).digest("hex")
const parse = (bytes: Uint8Array): unknown => JSON.parse(Buffer.from(bytes).toString("utf8"))
function verify(bytes: Uint8Array, ref: ObjectRef): void {
  if (hash(bytes) !== ref.sha256 || bytes.byteLength !== ref.byteLength)
    throw new Error(`object readback mismatch: ${ref.key}`)
}
export async function inspect(store: ObjectStore) {
  const stored = await store.get("v1/head.json")
  if (!stored) return { head: null, manifest: null, etag: null }
  const head = decodeHead(parse(stored.bytes))
  const manifestObject = await store.get(head.manifest.key)
  if (!manifestObject) throw new Error("published manifest is missing")
  verify(manifestObject.bytes, head.manifest)
  return { head, manifest: decodeManifest(parse(manifestObject.bytes)), etag: stored.etag }
}
function predecessor(current: Awaited<ReturnType<typeof inspect>>, expected: Expected): boolean {
  return (
    (current.head?.manifest.sha256 ?? null) === expected.manifestSha256 &&
    current.etag === expected.etag
  )
}
async function operateBundle(
  store: ObjectStore,
  bundleDir: string,
  expected: Expected,
  commitHead: boolean,
) {
  const metadata: unknown = JSON.parse(await readFile(join(bundleDir, "bundle.json"), "utf8"))
  if (
    !metadata ||
    typeof metadata !== "object" ||
    !("head" in metadata) ||
    !("objects" in metadata) ||
    !Array.isArray(metadata.objects)
  )
    throw new Error("invalid frozen bundle")
  const { decodeObjectRef } = await import("./storage.ts")
  const bundle: Bundle = {
    head: decodeHead(metadata.head),
    objects: metadata.objects.map(decodeObjectRef),
  }
  const headBytes = await readFile(join(bundleDir, "v1/head.json"))
  if (JSON.stringify(decodeHead(parse(headBytes))) !== JSON.stringify(bundle.head))
    throw new Error("frozen head changed")
  const manifestBytes = await readFile(join(bundleDir, bundle.head.manifest.key))
  verify(manifestBytes, bundle.head.manifest)
  const manifest = decodeManifest(parse(manifestBytes))
  const refs = [
    bundle.head.manifest,
    ...manifest.editions.map((edition) => edition.object),
    manifest.catalog,
    manifest.routes,
    manifest.search,
    manifest.rss,
  ]
  if (
    refs.some(
      (ref) => !bundle.objects.some((object) => JSON.stringify(object) === JSON.stringify(ref)),
    )
  )
    throw new Error("frozen bundle is incomplete")
  let current = await inspect(store)
  if (current.head?.manifest.sha256 === bundle.head.manifest.sha256) return current
  if (!predecessor(current, expected))
    throw new Error("unexpected published head; publication conflict")
  for (const ref of bundle.objects) {
    const bytes = await readFile(join(bundleDir, ref.key))
    verify(bytes, ref)
    const existing = await store.get(ref.key)
    if (existing) {
      verify(existing.bytes, ref)
      continue
    }
    try {
      await store.put(ref.key, bytes, ref.contentType, { absent: true })
    } catch (error) {
      const stored = await store.get(ref.key)
      if (!stored) throw error
      verify(stored.bytes, ref)
    }
    const stored = await store.get(ref.key)
    if (!stored) throw new Error(`object readback missing: ${ref.key}`)
    verify(stored.bytes, ref)
  }
  if (!commitHead) return current
  try {
    await store.put(
      "v1/head.json",
      headBytes,
      "application/json; charset=utf-8",
      expected.etag === null ? { absent: true } : { etag: expected.etag },
    )
  } catch (error) {
    current = await inspect(store)
    if (current.head?.manifest.sha256 === bundle.head.manifest.sha256) return current
    if (!predecessor(current, expected))
      throw new Error("unexpected published head; publication conflict")
    throw error
  }
  current = await inspect(store)
  if (current.head?.manifest.sha256 !== bundle.head.manifest.sha256)
    throw new Error("head readback mismatch")
  return current
}
export async function verifyBundleObjects(
  store: ObjectStore,
  bundleDir: string,
  expected: Expected,
) {
  return operateBundle(store, bundleDir, expected, false)
}
export async function publishBundle(store: ObjectStore, bundleDir: string, expected: Expected) {
  return operateBundle(store, bundleDir, expected, true)
}
export class S3Store implements ObjectStore {
  constructor(
    private client: S3Client,
    private bucket: string,
  ) {}
  async get(key: string): Promise<StoredObject | null> {
    try {
      const response = await this.client.send(
        new GetObjectCommand({ Bucket: this.bucket, Key: key }),
      )
      if (!response.Body || !response.ETag) throw new Error("incomplete S3 read response")
      return { bytes: await response.Body.transformToByteArray(), etag: response.ETag }
    } catch (error) {
      if (error instanceof Error && (error.name === "NoSuchKey" || error.name === "NotFound"))
        return null
      throw error
    }
  }
  async put(
    key: string,
    bytes: Uint8Array,
    contentType: string,
    condition: { etag: string } | { absent: true },
  ) {
    await this.client.send(
      new PutObjectCommand({
        Bucket: this.bucket,
        Key: key,
        Body: bytes,
        ContentType: contentType,
        ...(key === "v1/head.json" ? { CacheControl: "no-store" } : {}),
        ...("etag" in condition ? { IfMatch: condition.etag } : { IfNoneMatch: "*" }),
      }),
    )
  }
}
