import type { APIRoute } from "astro"
import { renderEditionHtml } from "../components/visuals"
import { loadEditions } from "../lib/digests"
import { editionDate, xmlEscape } from "../components/format"

export const GET: APIRoute = async ({ site }) => {
  const editions = await loadEditions()
  const absolute = (path: string) => new URL(path, site).href
  const items = editions
    .map((edition) => {
      const link = xmlEscape(absolute(edition.path))
      return `<item><title>${xmlEscape(editionDate(edition.date))}</title><link>${link}</link><guid isPermaLink="true">${link}</guid><pubDate>${new Date(edition.publishedAt).toUTCString()}</pubDate><description>${xmlEscape(renderEditionHtml(edition))}</description></item>`
    })
    .join("")
  const xml = `<?xml version="1.0" encoding="UTF-8"?><rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom"><channel><title>The AI daily</title><link>${xmlEscape(absolute("/"))}</link><description>Nishant's daily AI digest, with full editions and original sources.</description><language>en</language><atom:link href="${xmlEscape(absolute("/rss.xml"))}" rel="self" type="application/rss+xml"/>${items}</channel></rss>`
  return new Response(xml, { headers: { "Content-Type": "application/rss+xml; charset=utf-8" } })
}
