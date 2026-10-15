import type { APIRoute } from "astro"
import { loadDigestRepository } from "../lib/digests"

export const GET: APIRoute = async () => {
  const { sourceRevision, editions } = await loadDigestRepository()
  const manifest = {
    sourceRevision,
    routes: [
      "/",
      "/archive/",
      "/search/",
      "/rss.xml",
      "/sitemap.xml",
      "/404.html",
      ...editions.flatMap((edition) => [
        edition.path,
        edition.readPath,
        ...(edition.kind === "identified" ? edition.stories.map((story) => story.path) : []),
      ]),
    ],
    editions: editions.map((edition) => ({
      date: edition.date,
      sourcePath: edition.sourcePath,
      sourceSha256: edition.sourceSha256,
      path: edition.path,
      readPath: edition.readPath,
      stories: edition.kind === "identified" ? edition.stories.map((story) => story.path) : [],
    })),
  }
  return new Response(JSON.stringify(manifest), { headers: { "Content-Type": "application/json" } })
}
