# Nishant's Obsidian vault operating map

Current durable convention for Nishant's vault:

- Vault path: `/Users/skypawalker/Dropbox/Obsidian`
- Hosted content root for Quartz/Pawhouse: `/Users/skypawalker/Dropbox/Obsidian/public`
- Public operating areas:
  - `public/index.md` — public homepage titled `127.0.0.1`; visible copy calls the site `Mindscape`.
  - `public/wisdom/` — curated wisdom library.
  - `public/summaries/` — full summaries created only when Nishant explicitly asks to summarize a URL, image, video, or file.
- Private/runtime state stays outside `public/`; `.graphify/` is not hosted.

## Current naming and organization conventions

- Public Markdown filenames and folder names are lowercase kebab-case (`action-over-preparation.md`, `business-and-startups/`).
- Wisdom notes use human-readable frontmatter titles and H1s while keeping the filename slug lowercase kebab-case.
- Top-level hosted folders should remain only `wisdom/` and `summaries/` plus `index.md`.
- Current wisdom taxonomy:
  - `wisdom/business-and-startups/operating-principles/`
  - `wisdom/business-and-startups/strategy-and-career/`
  - `wisdom/health-and-protocols/`
  - `wisdom/personal-growth/action-and-discipline/`
  - `wisdom/personal-growth/presence-and-happiness/`
  - `wisdom/personal-growth/resilience-and-mental-health/`
  - `wisdom/personal-growth/self-worth-and-identity/`
  - `wisdom/prompt-wallet/`
  - `wisdom/readings-and-poems/`
  - `wisdom/relationships-and-friendship/`
  - `wisdom/society-and-psychology/cognitive-biases-and-belief/`
  - `wisdom/society-and-psychology/group-psychology/`
  - `wisdom/society-and-psychology/truth-and-social-pressure/`
- Do not recreate old wisdom section names such as `deep`, `modern-wisdom`, `life-lessons`, `mental-health`, `startups`, `tech`, or `interesting-reads`.

## Link capture

Karakeep is the only bookmark store. Use `bookmark-capture` and `karakeep` when Nishant explicitly asks to save, bookmark, keep, or remember a URL. A bare link in another workflow is context, not a save request.

Keep bookmark URLs and bookmark-specific notes in Karakeep. Do not create a bookmark inbox in Obsidian or publish bookmarks through Pawhouse. Summary requests still write to `public/summaries/`; curated wisdom belongs in `public/wisdom/`.

Accepted digest sources and year/month indexes live at `<vault>/digests/`, outside the hosted root. Use the shared R2 publisher from `ai-x-digest`; never publish digest content through broad notes sync.

After writing or updating public wisdom or summaries, publish from `/Users/skypawalker/Dev/pawhouse` with `npm run publish -- "Update notes"`. Bookmark captures do not trigger website publication.

## Wisdom migration / cleanup pattern

For future digital-garden migrations or cleanup from `/Users/skypawalker/Dev/dg-gatsby/content/garden`:

1. Use old TOC files only as source clues; write final notes into the current wisdom taxonomy above.
2. Convert `.mdx` notes into normal Markdown `.md` notes with lowercase kebab-case filenames.
3. Preserve readable `title:` and H1 values in Title Case / sentence case.
4. Do not recreate public `Index.md`/TOC notes for every section unless Nishant explicitly asks; prefer Quartz folder listings and the homepage/year/month indexes that already exist.
5. Wikilinks may use human note titles (`[[Action Over Preparation]]`) even when filenames are kebab-case; tools should resolve by path stem, title, alias, and slug.
6. Verify links with the updated wisdom linkage scan helper before large repairs.

## Historical state from the first migration

The initial migration created:

- `public/index.md` as the public home/value-map backlink target
- `public/wisdom/Index.md`
- Section indexes for deep, health, interesting-reads, life-lessons, mental-health, modern-wisdom, prompt-wallet, startups, and tech.
- The initial import normalized historical digests from `~/Dev/digest/_digests` into daily notes. This is a historical record, not an instruction to rewrite accepted editions. Preserve exact accepted sources during the private-source migration.

`Graphify Vault Dashboard.md` was later moved out of `public/` to the private vault root; do not publish Graphify dashboard/concept artifacts.

## Graphify vault graph

Graphify is set up for this vault with generated artifacts under `.graphify/`:

- `.graphify/graph.json`
- `.graphify/graph.html`
- `.graphify/graph.svg`
- `.graphify/GRAPH_REPORT.md`
- `.graphify/obsidian/graph.canvas`

The rebuild script is `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh`. A daily cron job named `rebuild-obsidian-graphify-graph` runs after the daily digest job. For the reusable Graphify/Obsidian pattern, use the `graphify` skill reference `references/obsidian-vaults.md`.
