---
name: obsidian
description: Read, search, create, and edit notes in the Obsidian vault.
platforms: [linux, macos, windows]
---

# Obsidian Vault

Use this skill for filesystem-first Obsidian vault work: reading notes, listing notes, searching note files, creating notes, appending content, and adding wikilinks.

## Vault path

Use a known or resolved vault path before calling file tools.

The documented vault-path convention is the `OBSIDIAN_VAULT_PATH` environment variable, for example from `~/.hermes/.env`. If it is unset, use `~/Documents/Obsidian Vault`.

File tools do not expand shell variables. Do not pass paths containing `$OBSIDIAN_VAULT_PATH` to `read_file`, `write_file`, `patch`, or `search_files`; resolve the vault path first and pass a concrete absolute path. Vault paths may contain spaces, which is another reason to prefer file tools over shell commands.

If the vault path is unknown, `terminal` is acceptable for resolving `OBSIDIAN_VAULT_PATH` or checking whether the fallback path exists. Once the path is known, switch back to file tools.

## Read a note

Use `read_file` with the resolved absolute path to the note. Prefer this over `cat` because it provides line numbers and pagination.

## List notes

Use `search_files` with `target: "files"` and the resolved vault path. Prefer this over `find` or `ls`.

- To list all markdown notes, use `pattern: "*.md"` under the vault path.
- To list a subfolder, search under that subfolder's absolute path.

## Search

Use `search_files` for both filename and content searches. Prefer this over `grep`, `find`, or `ls`.

- For filenames, use `search_files` with `target: "files"` and a filename `pattern`.
- For note contents, use `search_files` with `target: "content"`, the content regex as `pattern`, and `file_glob: "*.md"` when you want to restrict matches to markdown notes.

## Create a note

Use `write_file` with the resolved absolute path and the full markdown content. Prefer this over shell heredocs or `echo` because it avoids shell quoting issues and returns structured results.

If the Obsidian CLI is enabled and the user specifically asks to use it, create notes with:

```bash
obsidian create path="relative/folder/Note.md" content="Markdown content"
```

For large or multiline generated notes, filesystem writes are usually safer: resolve the vault path, write the `.md` file directly, then optionally use `obsidian open path="relative/folder/Note.md"` if the note should be opened. Obsidian vaults are just folders of Markdown files, so direct writes are valid.

For this user's generated digests, stage accepted notes privately and use the shared scoped publisher to promote into `digests/` using the filename pattern `x-ai-YYYY-MM-DD.md` unless the user requests a different digest type or title. See `references/digest-output.md` for the exact vault/output convention captured from the setup session. For cleanup/verification of the user-specific X-AI digest format, run `scripts/verify-x-ai-digest-format.py` against `/Users/skypawalker/Dropbox/Obsidian`.

For accepted historical digests, preserve exact bytes, aliases, prose and the canonical digest indexes (`digests/x-ai-YYYY.md` year parent plus `digests/x-ai-YYYY-MM.md` monthly indexes), and verify backlinks. See `references/digest-normalization.md`. New editions use `digest_format: editorial-v2` after the staged producer rollout and the `ai-x-digest` plus `unslop` skills; do not impose the archive's duplicate H1 or mandatory takeaways on them. Do not rewrite archives during a normal daily run.

For this user's current vault operating map, see `references/vault-operating-map.md`: hosted public areas are `public/notes/`, `public/maps/`, `public/readings/`, `public/practices/` and `public/prompts/`; accepted digests are private under `digests/`; summaries are private under `sources/`; private/runtime state such as `.graphify/` stays outside `public/`. Bookmarks belong only in private Karakeep via `bookmark-capture` and `karakeep`, and only on an explicit save/bookmark request. A bare link in another workflow is context; if he explicitly asks to summarize a URL/image/file, use `summarize-to-obsidian` and save under `sources/`. For rename/cleanup passes after Nishant reorganizes files, use `references/vault-cleanup-and-republish.md`.

For the historical initial migration record, see `references/initial-vault-porting.md`. Its `public/wisdom/` layout is retired; do not use it to restructure `public/`.

For this user's vault graph setup, Graphify outputs live under `.graphify/` in the vault and the dashboard note is private at `/Users/skypawalker/Dropbox/Obsidian/graphify-vault-dashboard.md` (outside `public/`). Rebuild with `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh` or consult the `graphify` skill's `references/obsidian-vaults.md`.

For Pawhouse/Quartz public assets and homepage images, place assets in `/Users/skypawalker/Dropbox/Obsidian/public/`, use relative links from notes, and prefer raw `<img width="..." />` for sized images because Markdown image attribute syntax can render literally in this Quartz setup. Daily digest visuals instead follow `ai-x-digest` and its `story_metadata` contract. Do not copy assets or emit raw image HTML for that workflow.

For Pawhouse site-level Quartz configuration changes (analytics/gtag, site metadata, layout, deploy verification), edit source config such as `quartz.config.ts`, build locally, publish with `npm run publish -- "..."` when the request implies live-site change, watch GitHub Pages, and verify the live asset. Do not hand-edit generated `public/` files or bulk-format existing content as part of unrelated config work.

For Pawhouse 404/bad-URL cleanup, do not claim links are fixed from a successful build or one sampled URL. Run the generated-site internal crawl, distinguish internal links from external URLs, fix `baseUrl`, path-qualify resolvable wikilinks, unlink genuinely missing internal targets or add the missing asset, then publish and verify live routes.

## Link audits

When asked to check links in `public/`, report before editing. List broken `[[...]]` links, notes that no map lists, and idea notes without a `Map:` line. Resolve links by filename, which is lowercase kebab-case and unique across the vault.

For a requested repair pass:

- Back up touched notes under `<vault>/.graphify/backups/<repair-run>/` before modifying them.
- Point each broken link at the existing note it meant. Remove the link when no such note exists.
- Do not link from `public/` to `sources/`, which Quartz does not publish.
- After edits, rebuild Graphify with `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh`, run a Quartz build from Pawhouse, and confirm the output has no `internal broken` links.

## Graphify concept maps

Do not create Graphify-derived concept notes, concept-map files, or managed concept blocks inside `public/`. The hand-edited maps in `public/maps/` are the public theme index. If Nishant asks for a term-derived concept map, write it as a private report under `<vault>/.graphify/` unless he explicitly asks to publish it. Back up touched files under `<vault>/.graphify/backups/<run>/`, write a run report under `.graphify/`, and rebuild Graphify.

## Append to a note

Prefer a native file-tool workflow when it is not awkward:

- Read the target note with `read_file`.
- Use `patch` for an anchored append when there is stable context, such as adding a section after an existing heading or appending before a known trailing block.
- Use `write_file` when rewriting the whole note is clearer than constructing a fragile patch.

For an anchored append with `patch`, replace the anchor with the anchor plus the new content.

For a simple append with no stable context, `terminal` is acceptable if it is the clearest safe option.

## Targeted edits

Use `patch` for focused note changes when the current content gives you stable context. Prefer this over shell text rewriting.

## Wikilinks

Obsidian links notes with `[[Note Name]]` syntax. When creating notes, use these to link related content.
