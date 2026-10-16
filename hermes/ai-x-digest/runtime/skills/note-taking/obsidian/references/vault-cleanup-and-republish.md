# Vault cleanup, rename compliance, and republish workflow

Use this reference when Nishant has renamed Obsidian public files/folders, asks whether an old structural note is still needed, or asks to rebuild Graphify and republish Pawhouse.

## Canonical public shape

- Hosted content root: `/Users/skypawalker/Dropbox/Obsidian/public`
- Public top-level areas: `summaries/`, `wisdom/`, plus `index.md`. Bookmarks belong only in private Karakeep
- Public filenames and folders are lowercase kebab-case.
- Human-facing `title:` values and H1 headings may remain readable Title Case / `X-AI ...` casing.
- `obsidian-value-map.md` is obsolete; use `public/index.md` and `[[index|Mindscape]]` as the home/value-map backlink target.

Accepted digests live at `<vault>/digests/`, outside the hosted root. For digest changes use `ai-x-digest` and its R2 publisher. Preserve exact historical bytes during relocation. The Pawhouse publish command below applies only to ordinary public notes.

## Cleanup sequence

1. Inspect before deleting:
   - Search filenames under the vault for the obsolete note/slug.
   - Search public note contents for links to the obsolete note.
   - Read the candidate note if it exists to confirm it contains no unique public content that must be migrated.
2. Back up destructive edits outside hosted content, preferably under `<vault>/.graphify/backups/<run>/`.
3. Rewrite links before deletion. For `obsidian-value-map`, replace `[[obsidian-value-map]]` and `[[Obsidian Value Map]]` with `[[index|Mindscape]]`.
4. Remove the obsolete file only after links are migrated.
5. Update skills, cron prompts, and helper scripts that encode old filenames or route casing. Search at least:
   - `/Users/skypawalker/.hermes/skills`
   - `/Users/skypawalker/.hermes/scripts`
   - `/Users/skypawalker/.hermes/cron/jobs.json`
6. Run deterministic verifiers, especially:

```bash
python /Users/skypawalker/.hermes/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py /Users/skypawalker/Dropbox/Obsidian
```

7. Rebuild the whole vault graph:

```bash
/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.sh
```

8. Verify the graph summary and spot-check key edge families when relevant. For digest rename work, confirm `NEXT_DIGEST` and `INDEXED_BY_MONTH` edges are nonzero in `.graphify/graph.json`.
9. Publish ordinary public notes through Pawhouse from `/Users/skypawalker/Dev/pawhouse`:

```bash
npm run publish -- "Update notes"
```

10. Verify the repo is clean and smoke-test a public route with `curl -I -L`.

## Pitfalls

- Do not treat `[[index|Mindscape]]` as a forbidden stale backlink; it is now the intended public home backlink.
- Lowercase kebab-case applies to filenames/routes, not necessarily note titles or H1s.
- Graphify helper scripts can silently lose custom sequence/index edges after filename casing changes. Update regexes in rebuild scripts when digest/file route conventions change.
- Pawhouse warnings about newly tracked content dates are not necessarily failures; still verify build success, commit/push, and a public route.
