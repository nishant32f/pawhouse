import type { WireEdition } from "./wire.ts"
import type { StoryVisual } from "./editorial.ts"
import { proseHtml } from "./prose.ts"
import { pointValue, xmlEscape as escapeXml } from "./format.ts"

export function visualHtml(visual: StoryVisual): string {
  const citation = `<a href="${escapeXml(visual.source.url)}">${escapeXml(visual.source.label)}</a>`
  const caption = `${escapeXml(visual.caption)} Source: ${citation}.`
  if (visual.kind === "image")
    return `<figure><img src="${escapeXml(visual.src)}" width="${visual.width}" height="${visual.height}" alt="${escapeXml(visual.alt)}"><figcaption>${caption} Image: ${escapeXml(visual.credit)}.</figcaption></figure>`
  return `<figure><table><caption>${escapeXml(visual.title)} (${escapeXml(visual.unit)})</caption><thead><tr><th scope="col">Label</th><th scope="col">Value</th></tr></thead><tbody>${visual.points.map((p) => `<tr><th scope="row">${escapeXml(p.label)}</th><td>${escapeXml(pointValue(p))}</td></tr>`).join("")}</tbody></table><figcaption>${caption}</figcaption></figure>`
}
export function editionFeedHtml(edition: WireEdition): string {
  if (
    edition.kind === "legacy" ||
    !edition.stories.some((s) => s.kind !== "archived" && s.editorial)
  )
    return proseHtml(edition.prose)
  let inBrief = false
  return edition.stories
    .filter((s) => s.kind !== "archived")
    .map((story) => {
      const brief = story.kind === "brief" && !inBrief ? "<h2>In brief</h2>" : ""
      if (story.kind === "brief") inBrief = true
      const level = story.kind === "brief" ? "h3" : "h2"
      const meta = story.editorial
      return `${brief}<section>${meta ? `<p>${escapeXml(meta.section)}</p>` : ""}<${level}>${escapeXml(story.headline)}</${level}>${meta?.deck ? `<p>${escapeXml(meta.deck)}</p>` : ""}${meta?.visual ? visualHtml(meta.visual) : ""}${proseHtml(story.prose)}</section>`
    })
    .join("\n")
}
export function serializeRss(
  editions: WireEdition[],
  site = "https://daily.nishantkhurana.me/",
): string {
  const absolute = (path: string) => new URL(path, site).href
  const items = editions
    .map((edition) => {
      const link = escapeXml(absolute(edition.path))
      const title = new Intl.DateTimeFormat("en-GB", {
        weekday: "long",
        day: "numeric",
        month: "long",
        year: "numeric",
        timeZone: "Asia/Kolkata",
      }).format(new Date(edition.publishedAt))
      return `<item><title>${escapeXml(title)}</title><link>${link}</link><guid isPermaLink="true">${link}</guid><pubDate>${new Date(edition.publishedAt).toUTCString()}</pubDate><description>${escapeXml(editionFeedHtml(edition))}</description></item>`
    })
    .join("")
  return `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>Machine Herald</title><link>${escapeXml(absolute("/"))}</link><description>Nishant&apos;s daily AI digest, with full editions and original sources.</description><language>en</language><atom:link href="${escapeXml(absolute("/rss.xml"))}" rel="self" type="application/rss+xml"/>${items}</channel></rss>`
}
