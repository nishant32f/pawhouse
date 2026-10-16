import { defineMiddleware } from "astro:middleware"
import { env } from "cloudflare:workers"
import { PublicationUnavailable, selectPublication } from "./lib/publication"

export const onRequest = defineMiddleware(async (context, next) => {
  const path = context.url.pathname
  const readsContent =
    ["/", "/archive/", "/search/", "/rss.xml", "/sitemap.xml", "/deployment.json"].includes(path) ||
    path.startsWith("/editions/")
  if (!readsContent) return next()
  try {
    context.locals.publication = await selectPublication(env.DAILY_CONTENT)
    const response = await next()
    response.headers.set("Cache-Control", "no-store")
    return response
  } catch (error) {
    if (!(error instanceof PublicationUnavailable)) throw error
    return new Response("Published content is temporarily unavailable. Please try again later.", {
      status: 503,
      headers: { "Content-Type": "text/plain; charset=utf-8", "Cache-Control": "no-store" },
    })
  }
})
