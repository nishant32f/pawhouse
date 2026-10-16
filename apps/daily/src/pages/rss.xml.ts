import type { APIRoute } from "astro"
export const GET: APIRoute = ({ locals }) => locals.publication.rss()
