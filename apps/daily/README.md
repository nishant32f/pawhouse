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

## Accepted publication

Human operators and Hermes use the same scoped publisher. Keep the accepted Markdown, affected indexes, request, and receipts outside both the Git checkout and the public vault. The publisher requires a clean `main` checkout. Its shared host lock also covers ordinary `npm run publish` and standalone vault sync.

Prepare a private JSON request with this shape. Paths in `files` are relative to the public vault. `before_sha256` is `null` only for a new file. Hash the exact accepted bytes.

```json
{
  "date": "2026-10-16",
  "expected_head": "FULL_40_CHARACTER_ACCEPTED_BASE_COMMIT",
  "files": {
    "digests/x-ai-2026-10-16.md": {
      "staged": "/private/staging/x-ai-2026-10-16.md",
      "before_sha256": null,
      "staged_sha256": "SHA256_OF_ACCEPTED_MARKDOWN"
    }
  }
}
```

Declare the edition and each changed month/year index. For a new day, also stage the immediately previous daily edition with only its `Next` navigation link updated. The publisher permits these paths only. It checks the complete vault against committed content and every declared base/candidate hash before writing. It runs editorial, revision-identity, and reader AST validation privately. An unchanged index may also be declared.

Run these commands from the repository root. Commands that publish source commit and push `main`; use them only after accepting the private revision.

```sh
./scripts/publish-from-vault.sh --digest /private/staging/request.json
python3 scripts/daily-release.py build --commit ACCEPTED_COMMIT
python3 scripts/daily-release.py verify --artifact /private/state/artifacts/ACCEPTED_COMMIT --origin https://READER_ORIGIN --request /private/staging/request.json --version CLOUDFLARE_VERSION
```

The first command returns the private receipt as JSON. Repeating the same request returns its accepted commit and retries its push. It does not generate prose or create another content commit. A remote descendant already containing that commit also satisfies the push. The pinned reader build uses a separate private checkout and installs the app lockfile. A failed build never replaces an earlier complete artifact.

The default private state directory is `~/.local/state/pawhouse-publication`. `PUBLISH_REPO`, `PUBLISH_VAULT_PUBLIC`, and `PUBLISH_STATE_DIR` let isolated fixture tests supply their own directories. Production callers share the default lock/state. On entry, every publisher repairs an interrupted promotion before proceeding. It restores only the touched paths and owned temporary files. A manual edit after interruption stops recovery without overwriting that edit.

| Phase             | Meaning                                                                                                        |
| ----------------- | -------------------------------------------------------------------------------------------------------------- |
| `accepted`        | Private candidate passed the publication checks.                                                               |
| `promoted`        | Declared vault/content files match the candidate.                                                              |
| `committed`       | The accepted Git commit exists; push can retry.                                                                |
| `readerpending`   | Source push succeeded; dated delivery remains blocked.                                                         |
| `readerverified`  | Live home/discovery/dated/read/story pages, complete prose/sources, RSS MIME/full text, and a real 404 passed. |
| `deliverypending` | Delivery began; interruption requires explicit resolution.                                                     |
| `complete`        | Recorded delivery succeeded; ordinary reruns suppress delivery.                                                |

Main-site status is independent. Record it with `publication.py main-result --request REQUEST --status verified|failed|pending --reference EVIDENCE`. Reader verification accepts a descendant only when the accepted date and Markdown hash still match. It records the actual source revision, optional Cloudflare version, and tested routes privately.

Before sending the dated message, call `publication.py delivery-begin --request REQUEST`. After success, call `publication.py delivery-complete --request REQUEST --reference DELIVERY_ID`. An ambiguous result requires `delivery-resolve --request REQUEST --outcome delivered|not-delivered --reference OPERATOR_EVIDENCE`. The receipt does not promise exactly-once delivery. Before cutover, keep delivering the existing Quartz dated URL.

## Prepared deployment and cutover

`deploy-daily.yml` independently checks, tests, builds, and uploads the complete reader artifact from its exact checkout SHA. Quartz's workflow remains separate. Production defaults to disabled. Later activation requires verified Cloudflare authority, `DAILY_CLOUDFLARE_ACCOUNT_ID` and `DAILY_CLOUDFLARE_API_TOKEN` secrets, a `DAILY_ORIGIN` variable, the protected `daily-production` environment, and deliberate `DAILY_PRODUCTION_ENABLED=true`. No account, domain, or redirect binding is configured here.

The production job serializes deployments without cancellation. Before invoking Wrangler, `daily-release.py deploy` reads the live source revision and rejects an older or unrelated candidate. It also rejects removed published routes or missing candidate files. This protects historical URLs during ordinary note sync and a later code rollback. Explicit bootstrap accepts only an absent initial manifest/deployment. Authentication, network, and malformed responses remain failures.

After deployment, the workflow reads the Cloudflare version and verifies actual pages against the pinned artifact. `deployment.json` contains public Git identity, Markdown hashes, and native routes only. It cannot substitute for those page probes. A failed deployment or probe preserves the previous private release/map and blocks the accepted publication's delivery.

Successful full-artifact verification writes `verified-redirects.json` under private state with one exact old dated path per verified destination. The first release checks every published date. Later accepted-day verification extends this map. A failed release adds nothing. After success, the public workflow uploads only the sanitized map as `daily-verified-redirects-SHA` for the later activation consumer. Pluto keeps authoritative publication and delivery receipts privately. Cloudflare responses, failure details, and private receipts are never uploaded. There is no Cloudflare redirect write in these helpers.

At authorized cutover, bind the verified reader origin, connect that artifact consumer to the verified account's redirect capability, and apply only those exact mappings. Preserve old pages if that capability is unavailable. To reverse cutover, disable the external redirect consumer/rules and restore old-site delivery URLs. Keep the accepted Markdown and retained routes. Domain/redirect activation and cron changes require their later explicit request.
