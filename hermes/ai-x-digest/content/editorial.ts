import type { Source } from "./parser.ts"

export type NumericQualifier = "exact" | "approximate" | "greater-than" | "at-least"
export type ChartPoint = { label: string; value: number; qualifier: NumericQualifier }
type VisualSource = { caption: string; source: Source }
export type ImageVisual = VisualSource & {
  kind: "image"
  src: string
  width: number
  height: number
  alt: string
  credit: string
}
export type BarVisual = VisualSource & {
  kind: "bar"
  title: string
  unit: string
  points: ChartPoint[]
}
export type StoryVisual = ImageVisual | BarVisual
export type StoryEditorial = { section: string; deck: string | null; visual: StoryVisual | null }

function isObject(value: unknown): value is Record<string, unknown> {
  return typeof value === "object" && value !== null && !Array.isArray(value)
}

function object(value: unknown, field: string): Record<string, unknown> {
  if (!isObject(value)) throw new Error(`editorial metadata: ${field} must be an object`)
  return value
}

function fields(value: Record<string, unknown>, allowed: string[], context: string): void {
  for (const key of Object.keys(value))
    if (!allowed.includes(key))
      throw new Error(`editorial metadata: unknown ${context} field ${key}`)
}

function text(value: unknown, field: string): string {
  if (typeof value !== "string" || !value.trim())
    throw new Error(`editorial metadata: ${field} requires nonempty text`)
  return value.trim()
}

function imageUrl(value: unknown): string {
  if (typeof value !== "string" || /[\u0000-\u0020\u007f\\]/.test(value))
    throw new Error("editorial metadata: unsafe image URL")
  const src = text(value, "image src")
  let url: URL
  try {
    url = new URL(src)
  } catch {
    throw new Error("editorial metadata: invalid image URL")
  }
  if (url.protocol !== "https:" || url.username || url.password)
    throw new Error("editorial metadata: image src must be HTTPS without credentials")
  return url.href
}

function dimension(value: unknown, field: string): number {
  if (typeof value !== "number" || !Number.isSafeInteger(value) || value <= 0)
    throw new Error(`editorial metadata: image ${field} must be a positive integer`)
  return value
}

function qualifier(value: unknown): NumericQualifier {
  if (
    value === "exact" ||
    value === "approximate" ||
    value === "greater-than" ||
    value === "at-least"
  )
    return value
  throw new Error("editorial metadata: unsupported numeric qualifier")
}

function visual(value: unknown, sources: Source[]): StoryVisual {
  const data = object(value, "visual")
  const sourceUrl = text(data.source_url, "visual source_url")
  const source = sources.find((candidate) => candidate.url === sourceUrl)
  if (!source)
    throw new Error("editorial metadata: visual source_url must cite this story's adjacent source")
  const shared = { caption: text(data.caption, "visual caption"), source }
  if (data.kind === "image") {
    fields(
      data,
      ["kind", "src", "width", "height", "alt", "caption", "credit", "source_url"],
      "image",
    )
    return {
      ...shared,
      kind: "image",
      src: imageUrl(data.src),
      width: dimension(data.width, "width"),
      height: dimension(data.height, "height"),
      alt: text(data.alt, "image alt"),
      credit: text(data.credit, "image credit"),
    }
  }
  if (data.kind === "bar") {
    fields(data, ["kind", "title", "unit", "caption", "source_url", "points"], "bar")
    if (!Array.isArray(data.points) || data.points.length < 2 || data.points.length > 4)
      throw new Error("editorial metadata: a bar visual needs 2 to 4 comparable points")
    const points = data.points.map((item: unknown) => {
      const point = object(item, "chart point")
      fields(point, ["label", "value", "qualifier"], "chart point")
      if (typeof point.value !== "number" || !Number.isFinite(point.value) || point.value < 0)
        throw new Error("editorial metadata: chart values must be finite and nonnegative")
      return {
        label: text(point.label, "point label"),
        value: point.value,
        qualifier: qualifier(point.qualifier),
      }
    })
    if (!points.some((point) => point.value > 0))
      throw new Error("editorial metadata: chart needs at least one positive value")
    return {
      ...shared,
      kind: "bar",
      title: text(data.title, "chart title"),
      unit: text(data.unit, "chart unit"),
      points,
    }
  }
  throw new Error("editorial metadata: visual kind must be image or bar")
}

export function parseStoryMetadata(
  value: unknown,
  stories: { id: string; sources: Source[] }[],
): Map<string, StoryEditorial> {
  const parsed = new Map<string, StoryEditorial>()
  if (value === undefined) return parsed
  const entries = object(value, "story_metadata")
  for (const [id, entry] of Object.entries(entries)) {
    const story = stories.find((candidate) => candidate.id === id)
    if (!story) throw new Error(`editorial metadata: unknown story ID ${id}`)
    const data = object(entry, id)
    fields(data, ["section", "deck", "visual"], "story")
    parsed.set(id, {
      section: text(data.section, "section"),
      deck: data.deck === undefined ? null : text(data.deck, "deck"),
      visual: data.visual === undefined ? null : visual(data.visual, story.sources),
    })
  }
  return parsed
}
