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
