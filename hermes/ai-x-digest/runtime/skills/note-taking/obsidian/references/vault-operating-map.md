# Nishant's Obsidian vault operating map

Current convention for Nishant's vault:

- Vault path: `/Users/skypawalker/Dropbox/Obsidian`
- Hosted content root for Quartz/Pawhouse: `/Users/skypawalker/Dropbox/Obsidian/public`
- The vault's own `AGENTS.md` holds the full note conventions. Read it before editing notes.

## Public areas

- `public/index.md` is the homepage, titled `127.0.0.1`; visible copy calls the site `Mindscape`. `public/about.md` is the About page.
- `public/notes/` holds idea notes. Each note makes one claim and its title states that claim.
- `public/maps/` holds one map per theme: action, meaning, resilience, self-worth, relationships, social psychology, startups and AI, readings, practices and prompts. Maps are edited by hand.
- `public/readings/` holds poems, letters, a speech and short texts.
- `public/practices/` holds protocols, question lists and scripts.
- `public/prompts/` holds AI prompts, including Copilot prompts in `public/prompts/copilot-custom-prompts/`.
- Do not create other top-level folders in `public/`.

## Private areas

- `sources/` holds summaries of interviews, videos, newsletters and files, named `source-<slug>.md`. Quartz does not publish them, so do not link to them from `public/`.
- `digests/` holds accepted digest sources and year/month indexes. Use the shared R2 publisher from `ai-x-digest`; never publish digest content through broad notes sync.
- `.graphify/` holds generated graph outputs. It is not hosted.

## Naming, tags and links

- Filenames are lowercase kebab-case and unique across the vault. `title:` values and H1s stay readable.
- Link notes with `[[filename|Title]]`.
- Pages other than idea notes start their tags with one type tag: `poetry`, `letter`, `speech`, `prose`, `practice`, `prompt` or `map`. Add up to four topic tags after it. Reuse a topic tag that already exists before adding a new one.
- Idea notes end with a `## Related` list, with one sentence after each link, and a last line `Map: [[map-name|Map title]]`.
- Add each new idea note to a map. When a note's title or description changes, update its line on the map.
- `author` names the real author, or `Unknown` when the original names nobody. Do not add lines about how a note was collected, copied or edited.

## Link capture

Karakeep is the only bookmark store. Use `bookmark-capture` and `karakeep` when Nishant explicitly asks to save, bookmark, keep, or remember a URL. A bare link in another workflow is context, not a save request.

Keep bookmark URLs and bookmark-specific notes in Karakeep. Do not create a bookmark inbox in Obsidian or publish bookmarks through Pawhouse. Summary requests write to `sources/`. New idea notes belong in `public/notes/` and on a map.

After writing or updating public notes, publish from the Pawhouse repository's `main` branch with `npm run publish -- "Update notes"`. Summaries in `sources/` and bookmark captures do not trigger website publication.

## Graphify vault graph

Graphify is set up for this vault with generated artifacts under `.graphify/`:

- `.graphify/graph.json`
- `.graphify/graph.html`
- `.graphify/graph.svg`
- `.graphify/GRAPH_REPORT.md`
- `.graphify/obsidian/graph.canvas`

The dashboard note is private at the vault root as `graphify-vault-dashboard.md`; do not publish Graphify dashboard or concept artifacts. The rebuild script is `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh`. A daily cron job named `rebuild-obsidian-graphify-graph` runs after the daily digest job. For the reusable Graphify/Obsidian pattern, use the `graphify` skill reference `references/obsidian-vaults.md`.
