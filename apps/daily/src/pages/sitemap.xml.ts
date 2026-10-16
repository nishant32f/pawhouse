import type { APIRoute } from "astro"
import { xmlEscape } from "../components/format"

export const GET: APIRoute = async ({ site, locals }) => {
  const { editions } = await locals.publication.catalog()
  const paths = [
    "/",
    "/archive/",
    "/search/",
    ...editions.flatMap((edition) => [
      edition.path,
      edition.readPath,
      ...edition.stories.map((story) => story.path),
    ]),
  ]
  const xml = `<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">${paths.map((path) => `<url><loc>${xmlEscape(new URL(path, site).href)}</loc></url>`).join("")}</urlset>`
  return new Response(xml, { headers: { "Content-Type": "application/xml; charset=utf-8" } })
}
