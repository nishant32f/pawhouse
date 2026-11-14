# Nishant Obsidian initial vault porting map

This is a record of the initial Obsidian vault migration. Its `public/summaries/` and `public/wisdom/` layout was retired on 14 November 2026. For the current layout, use `vault-operating-map.md`. Do not recreate the old folders.

## Target vault shape

Vault: `/Users/skypawalker/Dropbox/Obsidian`
Hosted content root: `/Users/skypawalker/Dropbox/Obsidian/public`

The current public areas are listed in `vault-operating-map.md`.

Private/runtime outputs such as `.graphify/`, reports, backups, dashboards, and generated concept maps stay outside `public/` unless Nishant explicitly asks to publish them.

## One-time source imports

### Digests

The initial migration imported and normalized legacy digests from `~/Dev/digest/`. That work is historical. Accepted sources now belong at `<vault>/digests/`, outside the hosted root, with their daily, month and year filenames unchanged. Preserve exact bytes and existing index notes. Use Pawhouse `scripts/daily-history.py` with an explicit full pinned legacy SHA for the one-time bootstrap. Do not repeat normalization or use broad notes publication. Ongoing editions follow `ai-x-digest` and the shared R2 publication lifecycle.

### Wisdom

Source: `~/Dev/dg-gatsby/content/garden/`

The first migration used that garden's TOC files to build `public/wisdom/`. Files outside the TOCs are context about Nishant; do not publish all of them as notes. The wisdom notes were later rewritten into `public/notes/`, `public/readings/`, `public/practices/` and `public/prompts/`, with maps in `public/maps/`. Keep generated graph reports and concept maps private under `.graphify/`.

## Bookmarks

The former Obsidian bookmark inbox is retired. Karakeep is the only bookmark store. Use `bookmark-capture` and `karakeep` on an explicit save/bookmark request; never recreate a bookmark area in the vault or website.

## Verification after migration or path changes

- Confirm the hosted root contains only the intended public areas plus expected Quartz-compatible files.
- Run the X-AI digest verifier when digests changed:
  `python /Users/skypawalker/.hermes/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py /Users/skypawalker/Dropbox/Obsidian`
- Rebuild the private Graphify vault graph:
  `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh`
- Publish Pawhouse from its `main` branch when public notes changed:
  `cd /Users/skypawalker/Dev/pawhouse && npm run publish -- "Update notes"`
