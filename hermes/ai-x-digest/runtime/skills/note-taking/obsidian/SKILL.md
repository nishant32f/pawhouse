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

For this user's generated digests, write final digest notes under the vault's hosted content root `public/digests/` folder using the filename pattern `x-ai-YYYY-MM-DD.md` unless the user requests a different digest type or title. See `references/digest-output.md` for the exact vault/output convention captured from the setup session. For cleanup/verification of the user-specific X-AI digest format, run `scripts/verify-x-ai-digest-format.py` against `/Users/skypawalker/Dropbox/Obsidian`.

When importing or cleaning unversioned historical digests for Nishant, normalize legacy morning/evening notes into one daily note per date, keep old names as aliases/provenance only, maintain only the canonical digest indexes (`public/digests/x-ai-YYYY.md` year parent plus `public/digests/x-ai-YYYY-MM.md` monthly indexes), and verify backlinks. See `references/digest-normalization.md`. New editions use `digest_format: editorial-v1` and the `ai-x-digest` plus `unslop` skills; do not impose the archive's duplicate H1 or mandatory takeaways on them. Do not rewrite archives during a normal daily run.

For this user's current vault operating map, see `references/vault-operating-map.md`: hosted public areas are `public/digests/`, `public/wisdom/`, and `public/summaries/`; private/runtime state such as `.graphify/` stays outside `public/`. Bookmarks belong only in private Karakeep via `bookmark-capture` and `karakeep`, and only on an explicit save/bookmark request. A bare link in another workflow is context; if he explicitly asks to summarize a URL/image/file, use `summarize-to-obsidian` and save under `public/summaries/`. For rename/cleanup passes after Nishant reorganizes files, use `references/vault-cleanup-and-republish.md`.

For the initial/repair migration shape, see `references/initial-vault-porting.md`: one-time port legacy digests from `~/Dev/digest/`, use `~/Dev/dg-gatsby/content/garden/` TOC files to structure `public/wisdom/`, treat files outside those TOCs as context about Nishant, and verify digests/linkages/Graphify/Pawhouse after changes.

For this user's vault graph setup, Graphify outputs live under `.graphify/` in the vault and the dashboard note is private at `/Users/skypawalker/Dropbox/Obsidian/Graphify Vault Dashboard.md` (outside `public/`). Rebuild with `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh` or consult the `graphify` skill's `references/obsidian-vaults.md`.

For Pawhouse/Quartz public assets and homepage images, see `references/pawhouse-quartz-assets.md`: place assets in `/Users/skypawalker/Dropbox/Obsidian/public/`, use relative links from notes, and prefer raw `<img width="..." />` for sized images because Markdown image attribute syntax can render literally in this Quartz setup.

For Pawhouse site-level Quartz configuration changes (analytics/gtag, site metadata, layout, deploy verification), see `references/pawhouse-quartz-site-config.md`: edit source config such as `quartz.config.ts`, build locally, publish with `npm run publish -- "..."` when the request implies live-site change, watch GitHub Pages, and verify the live asset. Do not hand-edit generated `public/` files or bulk-format existing content as part of unrelated config work.

For Pawhouse 404/bad-URL cleanup, see `references/pawhouse-link-health.md`: do not claim links are fixed from a successful build or one sampled URL. Run the generated-site internal crawl, distinguish internal links from external URLs, fix `baseUrl`, path-qualify resolvable wikilinks, unlink genuinely missing internal targets or add the missing asset, then publish and verify live routes.

## Wisdom linkage audits

When asked to scan the user's `public/wisdom/` folder for missing Obsidian linkages, run a conservative report-only audit before editing notes. Use the bundled helper:

```bash
python /Users/skypawalker/.hermes/skills/note-taking/obsidian/scripts/wisdom-linkage-scan.py /Users/skypawalker/Dropbox/Obsidian
```

It writes `<vault>/.graphify/wisdom-linkage-scan.md` and reports unresolved/broken wikilinks, notes with no inbound/outbound wisdom links, fully isolated wisdom notes, exact-title mentions that are not linked, related-section entries that are not linked, and conservative Graphify-backed structural candidates. It resolves links by path stem, frontmatter title, aliases, and slugified title because Nishant's current public wisdom convention is lowercase kebab-case filenames with readable title/H1 wikilinks. Treat remaining unresolved links as genuinely missing or intentionally pruned concept notes unless the user asks for repair.

For a requested repair pass:

- Backup touched wisdom notes under `<vault>/.graphify/backups/<repair-run>/` before modifying them.
- First canonicalize old imported long-title wikilinks to existing note names, preserving display aliases only when useful, e.g. `[[Curse of Competence - Paradox of Choice]]` -> `[[Curse of Competence]]` and `[[How to Find Out What You're Really Made Of]]` -> `[[What Youre Made Of|How to Find Out What You're Really Made Of]]`.
- Path-qualified wikilinks such as `[[wisdom/deep/Index]]` are valid; do not treat them as broken. Bare duplicate names such as `[[Index]]` should be path-qualified because many wisdom subfolders have `Index.md`.
- If two notes share the same stem, rename or path-qualify to remove ambiguity. In Nishant's vault, the life-lessons duplicate was renamed to `wisdom/life-lessons/Self-Belief vs Action - Life Lessons.md`, while `wisdom/modern-wisdom/Self-Belief vs Action.md` remains canonical for the shorter modern-wisdom note.
- If a missing wikilink names a real concept with no file, create a small bridge note rather than self-linking. Example: `wisdom/deep/Ordinary Life Wisdom.md` resolves the imported `[[Ordinary Life Wisdom]]` link and points back to `[[Appreciate Everything]]`.
- After edits, rerun the scan helper and rebuild Graphify with `/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh`. A successful repair should drive unresolved wisdom wikilinks to zero and keep fully isolated wisdom notes at zero.

## Wisdom term-derived concept map

When the user says wisdom relations are too dependent on `Related Notes` / imported related-article metadata, build a second linkage layer from the actual note body text:

1. Parse wisdom notes while excluding frontmatter, existing wikilinks, imported provenance, and sections named `Related Notes`, `Related Concepts`, `Similar Notes`, `Wisdom linkage repair`, or `Graphify suggested links`.
2. Use curated concept vocabularies/patterns for recurring wisdom themes such as Action and Agency, Ambition and Expectations, Boundaries and Communication, Discipline and Consistency, Focus and Attention, Happiness and Fulfillment, Leadership and Startups, Learning and Advice, Mental Health and Self-Awareness, Relationships and Love, Resilience and Adversity, Self-Belief and Confidence, Self-Worth and Validation, Strategy and Decision-Making, Gratitude and Presence, Wealth and Business, AI Prompting and Tools, and Technology and Systems.
3. Do not create Graphify-derived concept notes, Wisdom Concept Map files, or managed term-concept blocks inside `public/`. Nishant wants public to remain only `digests`, `summaries`, and curated `wisdom` notes; Graphify concepts/files must stay private outside `public/` (for example under `<vault>/.graphify/` or a private non-hosted vault path).
4. If a term-derived concept map is requested, produce it as a private report under `<vault>/.graphify/` unless Nishant explicitly asks to publish it.
5. Backup touched files under `<vault>/.graphify/backups/<run>/`, write a run report under `.graphify/`, rerun the wisdom linkage scan helper, and rebuild Graphify. The goal is to use Graphify as a private map/backbone without leaking generated concept artifacts into hosted content.

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
