import type { APIRoute } from "astro"

export const GET: APIRoute = async ({ locals }) => {
  const publication = locals.publication
  const { editions } = await publication.catalog()
  const { routes } = await publication.routes()
  const provenance = {
    codeRevision: __DAILY_CODE_REVISION__,
    publicationRevision: publication.publicationRevision,
    compilerRevision: publication.compilerRevision,
    routes: [
      "/",
      "/archive/",
      "/search/",
      "/rss.xml",
      "/sitemap.xml",
      "/deployment.json",
      ...routes.map((route) => route.path),
    ],
    editions: editions.map((edition, index) => {
      const entry = publication.manifest.editions[index]
      return {
        date: edition.date,
        sourceSha256: entry?.sourceSha256,
        contentSha256: entry?.object.sha256,
        path: edition.path,
        readPath: edition.readPath,
        stories: edition.stories.map((story) => story.path),
      }
    }),
  }
  return new Response(JSON.stringify(provenance), {
    headers: { "Content-Type": "application/json; charset=utf-8" },
  })
}
