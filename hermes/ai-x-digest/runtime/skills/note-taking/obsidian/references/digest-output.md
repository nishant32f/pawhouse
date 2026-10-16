# Digest notes in Obsidian

Session-specific convention for this user:

- Vault path: `/Users/skypawalker/Dropbox/Obsidian`
- Hermes env var: `OBSIDIAN_VAULT_PATH="/Users/skypawalker/Dropbox/Obsidian"`
- Digest folder: `digests/`
- Daily X-AI digest filename pattern: `x-ai-YYYY-MM-DD.md`
- Year digest parent index: `digests/x-ai-YYYY.md` (for example `x-ai-2026.md`; title/H1 stay `X-AI 2026`)
- Monthly digest indexes: `digests/x-ai-YYYY-MM.md`
- Daily notes should end with `## Navigation` followed by `## Backlinks`, linking to `[[index|Mindscape]]`, `[[digests/x-ai-YYYY|X-AI YYYY]]`, and `[[digests/x-ai-YYYY-MM|X-AI-YYYY-MM]]`.
- Historical accepted imports preserve exact bytes; see `references/digest-normalization.md`.
- Daily digest automation exists as Hermes cron job `daily-ai-x-digest-to-obsidian`, scheduled `0 8 * * *`, using `bird` JSON plus summarization.
- The active R2 producer uses `digest_format: editorial-v2` and the `ai-x-digest` plus `unslop` skills. Write a private first draft, edit it, check the sources, and validate before publication. Use concrete story headings, adjacent source links, and optional advice. The historical H1, theme-count, and takeaway rules do not apply to this format.
- Follow `ai-x-digest` for four discovery categories and private collection/selection records. Normal v2 editions aim for 10 to 14 distinct items, with shorter quiet days. Use dated catch-up and check recent editions for repeats.
- Absolute output path pattern: `/Users/skypawalker/Dropbox/Obsidian/digests/x-ai-YYYY-MM-DD.md`
- Digest illustrations use optional `story_metadata` frontmatter under the `ai-x-digest` contract. Hermes supplies inspected media, captions and chart facts. The reader owns their HTML and design. Do not apply general Quartz raw-image or asset-copying advice to this workflow.

Recommended workflow:

1. Resolve the vault path from `OBSIDIAN_VAULT_PATH`; do not pass literal `$OBSIDIAN_VAULT_PATH` to file tools.
2. Stage the draft, edited candidate, source snapshots, review, indexes, and request privately outside the public vault and repository.
3. Follow `ai-x-digest` for persistent IDs, optional sourced editorial metadata, the separate unslop pass, and the shared scoped publisher. Review prose, decks, captions, labels and numerical bounds against the inspected sources. Only `publish-from-vault.sh --digest PRIVATE_REQUEST.json` promotes accepted files. Never write a digest directly into the public vault.
4. If the user asks to open the accepted result in Obsidian, use the CLI after publication:

```bash
obsidian open path="digests/x-ai-YYYY-MM-DD.md"
```

For daily digest automation, keep collection scripts under `~/.hermes/scripts/<workflow>/` and raw/state data under `~/.hermes/data/<workflow>/`; only the final curated digest belongs in the vault.
