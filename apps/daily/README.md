# Daily reader

Machine Herald reads a selected private R2 publication at request time. Code releases and content publications have separate revisions. Quartz keeps its own package, Node version, build and deployment.

Use Node 22.23.3. The app pins Astro 7.3.8, `@astrojs/cloudflare` 14.3.3 and Wrangler 4.151.0. The adapter uses the Worker entrypoint, disables sessions and passes images through unchanged. It adds no KV or Images dependency.

```sh
cd apps/daily
mise exec node@22.23.3 -- npm ci
mise exec node@22.23.3 -- npm run check
mise exec node@22.23.3 -- npm test
mise exec node@22.23.3 -- npm run build
mise exec node@22.23.3 -- npm run preview
```

These commands run locally. `remoteBindings: false` and the binding's `remote: false` keep normal development disconnected from production R2. An empty local bucket returns 503 until a complete local publication exists. They never sync the vault, publish content or deploy a Worker.

The adapter writes the Worker to `dist/server/entry.mjs`, deployment configuration to `dist/server/wrangler.json`, and static assets to `dist/client/`. Use the generated server configuration for a code release. Build output and `.astro/` are ignored.

## Request-time content

`src/middleware.ts` selects `v1/head.json` once for each reading request. `src/lib/publication.ts` exposes only `get` through its application binding wrapper. Cloudflare's native R2 binding also permits writes; this wrapper is not an IAM permission restriction. The reader contains no write endpoint or publisher credential.

Head selects an immutable manifest by SHA-256. Every later read uses that manifest's object references. There is no module-level latest-content promise. JSON reads verify byte length, SHA-256, wire schema and edition identity. Missing or invalid referenced content returns a controlled 503. Valid missing dates and stories return 404. Mutable reading responses use `Cache-Control: no-store`; hashed fonts, styles and scripts remain static assets.

| Method on the selected publication | Reads                                                                         |
| ---------------------------------- | ----------------------------------------------------------------------------- |
| `edition(date?)`                   | One edition, defaulting to the newest manifest date.                          |
| `catalog()`                        | Dates, story headlines and routes, without edition bodies.                    |
| `routes()`                         | Published native routes, including archived stories.                          |
| `search()`                         | Published full text for editions and every story, including archived stories. |
| `rss()`                            | Streams the pinned RSS artifact after checking its stored size.               |

RSS bytes come from the neutral publisher. The reader streams the immutable artifact without loading or rendering the archive. JSON integrity checks read complete objects; RSS streaming relies on the publisher's immutable content-addressed object contract.

The browser-safe neutral wire module supplies `decodeEdition` and `materializeEdition`. `src/lib/digests.ts` exports view types only. It does not import the Markdown parser, compiler, S3 client, filesystem or Git runtime loader. Parser tests import the neutral parser directly.

Read records contain rendered HTML, plain text, persistent identities, heading anchors, sources and editorial metadata. They omit authored Markdown and private source paths. Existing story and edition templates retain newspaper rendering. Both persistent story IDs and their old heading aliases remain targets on front and full-edition pages. The first brief keeps the old In brief target. Archived heading targets lead to retained articles through a small archived-links section, without presenting archived prose as active news.

## Reading and discovery

| Route                        | Content                                                                                                                       |
| ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------- |
| `/`                          | Latest actual edition, with its dated canonical URL.                                                                          |
| `/editions/DATE/`            | Newspaper front or complete legacy edition.                                                                                   |
| `/editions/DATE/read/`       | Complete active edition or complete legacy edition.                                                                           |
| `/editions/DATE/stories/ID/` | Complete story, adjacent sources and active previous/next links. Archived stories keep their corrections and original bodies. |
| `/archive/`                  | Catalog dates and active story links, newest first.                                                                           |
| `/search/`                   | Full-text search with server-rendered query results and optional browser filtering.                                           |
| `/rss.xml`                   | Complete active editions from the neutral RSS artifact.                                                                       |
| `/sitemap.xml`               | Native catalog routes, including retained archived stories.                                                                   |
| `/deployment.json`           | Public code and content provenance.                                                                                           |

Reading, sources, navigation and search work without JavaScript. System dark mode uses CSS. JavaScript adds theme, text size and immediate search filtering. The reader has no Print control.

The app retains Old Standard TT for masthead and headlines, Newsreader for reading, and Arial for controls and captions. Fontsource pins and licenses remain unchanged. `src/components/visuals.ts` owns page images and chart drawing. The neutral RSS serializer uses accessible tables for charts and preserves titles, units, qualifiers, values, image descriptions, captions, credits and citations.

RSS keeps each edition's dated URL as its GUID and link. Corrections update that item. `pubDate` remains midnight IST for the edition date. Canonical, RSS and sitemap URLs use Astro's configured `site`.

## Provenance and verification

`deployment.json` exposes `codeRevision`, `publicationRevision` and `compilerRevision` separately. The publication revision is the selected manifest SHA-256. Edition entries contain their date, `sourceSha256`, `contentSha256`, edition/read paths and story paths. It exposes neither source Markdown nor private source paths. These fields support verification; they do not replace checking rendered prose and live responses.

`tests/runtime-loader.test.ts` checks selection once, immutable reads after head changes, independent publication selection, bounded edition reads, metadata-only discovery, missing dates and broken references. `tests/reading.test.ts` builds the actual Worker once, seeds Miniflare's local R2 binding from retained accepted fixtures, then requests real rendered routes. It publishes A and B under the same built code and checks provenance, reading, discovery, RSS, sources, charts, legacy editions, archived bodies, missing assets and 503 responses. The twelve-story accepted fixture lives under `tests/fixtures/` and survives website digest removal.

The remaining parser, editorial, producer-contract and visual tests retain their existing assertions. Set `DAILY_KEEP_READING_FIXTURE=1` to retain captured local Worker responses after the reading test. This does not keep a running Worker.

Production resources, credentials and deployment remain outside this app's test workflow. The checked-in configuration preserves account `1688bfec49a43a217df10ed33b86e300`, Worker `pawhouse-daily`, custom domain `daily.nishantkhurana.me`, and disabled workers.dev and preview URLs. Creating or deploying those resources requires the user's deployment instruction.
