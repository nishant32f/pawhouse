# Daily reader

This independent Astro app reads accepted digest Markdown from the Pawhouse Git commit. It builds static HTML for `daily.nishantkhurana.me`. Quartz keeps its own package, lockfile, Node version, build, and deployment.

Use Node 22.23.3 for this app. Astro 7.3.8 and its dependencies require at least Node 22.19. Quartz continues to use Node 22.16.0. The app has no server adapter.

```sh
cd apps/daily
mise exec node@22.23.3 -- npm ci
mise exec node@22.23.3 -- npm test
mise exec node@22.23.3 -- npm run check
mise exec node@22.23.3 -- npm run build
mise exec node@22.23.3 -- npm run preview
```

The app writes build output to `dist/` and generated types to `.astro/`. Both directories are ignored by Git. These commands do not sync the vault, publish source, or deploy the app.

## Content adapter

`src/lib/digests.ts` exports the following API.

| Export                             | Result                                                                 |
| ---------------------------------- | ---------------------------------------------------------------------- |
| `parseEdition({ filename, text })` | One validated legacy or identified edition. Throws on invalid content. |
| `parseEditions(inputs)`            | Validated editions, newest first. Rejects duplicate dates.             |
| `loadDigestRepository()`           | A cached promise containing `sourceRevision` and `editions`.           |
| `loadEditions()`                   | The same cached edition records for page generation.                   |

The loader pins `HEAD` once, lists exact `content/digests/x-ai-YYYY-MM-DD.md` paths in that Git tree, and reads their blobs. It does not read the working vault, uncommitted content, or a website. It passes Git arguments as an array. Builds in temporary fixture checkouts need a fixture commit before loading content.

Each edition exposes its date, title, production paths, original Markdown, source path, exact SHA-256 hash, rendered HTML, plain text, and actual source links. `publishedAt` represents the validated daily date at midnight IST, with the explicit `+05:30` offset. It does not change between builds. `sourceRevision` is the full Git commit ID that supplied every edition.

An edition has `kind: "legacy"` for an absent version or `editorial-v1`. It remains one whole edition. The adapter removes only Navigation and Backlinks furniture, preserves its authored prose and sources, and creates no inferred story routes.

An `editorial-v2` edition has `kind: "identified"`, ordered `stories`, `activeStories`, `archivedStories`, and a full-story `lead`. Each story has its persistent ID, headline, parent edition path, article path, opening summary, remaining `bodyMarkdown`, complete prose in `markdown`, HTML, text, and adjacent source links. Archived stories also have a correction. Their HTML includes the correction and retained prose. Edition HTML and sources contain only active stories.

The adapter validates dates, versions, headings, explicit IDs, parent membership, and visible HTTPS sources within each identified story. A source in another story cannot cover missing attribution. Images, code, and raw HTML cannot supply a source link. Markdown reference links resolve through definitions in the same edition.

The parser uses a Markdown AST. It consumes the one allowlisted ID comment as metadata, escapes other raw HTML, and rejects unsafe link schemes. Knowledge wikilinks point to `https://nishantkhurana.me/` and do not become invented source attribution. Every view can use the same generated records without client JavaScript.

Stable paths are `/editions/DATE/`, `/editions/DATE/read/`, and `/editions/DATE/stories/ID/`. A headline edit cannot change the article path. Archives retain their paths but do not enter active cards or previous/next navigation.

The producer's `hermes/ai-x-digest/story_identity.py` owns revision comparison. The reader validates one accepted input and cannot prove that a previous ID was retained or that archived prose matches history. The publisher must validate those revisions before committing source.

## Focused evidence

`tests/digests.test.ts` uses the shared fixtures from `hermes/ai-x-digest/contract.md`. It covers the accepted four-story edition, both legacy formats, briefs, archives, stable paths, deterministic output, source boundaries, raw HTML, dates, malformed IDs, and unsafe URLs. Run Python identity checks separately from the repository root when changing the shared identity contract.

## Reading and discovery

The home page shows the latest actual edition and its date. Identified editions use a lead and supporting stories. Legacy editions retain their complete original prose.

| Route                        | Content                                                                                            |
| ---------------------------- | -------------------------------------------------------------------------------------------------- |
| `/`                          | Latest edition, with the dated edition as its canonical URL.                                       |
| `/editions/DATE/`            | Newspaper front, or the complete legacy edition.                                                   |
| `/editions/DATE/stories/ID/` | Complete identified story, sources, correction when archived, and active previous/next navigation. |
| `/editions/DATE/read/`       | Complete active edition, or the complete legacy edition.                                           |
| `/archive/`                  | Every actual edition, newest first.                                                                |
| `/search/`                   | Browseable edition and story links. Optional JavaScript filters their full text.                   |
| `/rss.xml`                   | Public RSS 2.0 with complete active edition HTML and citations.                                    |
| `/sitemap.xml`               | Actual native routes, including retained archived articles.                                        |
| `/404.html`                  | Missing-page document for static hosting.                                                          |

Reading, sources, navigation, and search browsing work without JavaScript. System dark mode uses CSS. JavaScript adds theme, text size, print buttons, and search filtering. Browser print remains available without JavaScript. Printing a newspaper front includes the complete selected edition.

The app self-hosts Libre Baskerville and DM Sans through pinned Fontsource packages. Their OFL licenses ship under `public/fonts/`. The reader styles and build remain separate from Quartz.

RSS identifies one edition by its dated URL. A correction updates that same item. `pubDate` reflects midnight IST for the source date. Missing days create no routes or feed items. Canonical, RSS, and sitemap URLs use Astro's configured `site`. The default is the production reader origin. Astro's `--site` build option can set a local preview origin.

`public/_headers` supplies the RSS MIME type for Cloudflare static assets. A generated endpoint's Response headers alone do not persist in static build output. Deployment verification must check the served header.

`tests/reading.test.ts` builds the real Astro app in a temporary Git repository containing committed accepted fixtures. It checks complete generated HTML, sources, active navigation, retained archives, legacy prose, static search links, parsed RSS XML, deterministic rebuilds, correction identity, and sitemap XML. It leaves the canonical Git index untouched. Set `DAILY_KEEP_READING_FIXTURE=1` when running the test to retain its temporary repository for browser inspection.
