# Digest notes in Obsidian

Session-specific convention for this user:

- Vault path: `/Users/skypawalker/Dropbox/Obsidian`
- Hermes env var: `OBSIDIAN_VAULT_PATH="/Users/skypawalker/Dropbox/Obsidian"`
- Digest folder: `public/digests/`
- Daily X-AI digest filename pattern: `x-ai-YYYY-MM-DD.md`
- Year digest parent index: `public/digests/x-ai-YYYY.md` (for example `x-ai-2026.md`; title/H1 stay `X-AI 2026`)
- Monthly digest indexes: `public/digests/x-ai-YYYY-MM.md`
- Daily notes should end with `## Navigation` followed by `## Backlinks`, linking to `[[index|Mindscape]]`, `[[digests/x-ai-YYYY|X-AI YYYY]]`, and `[[digests/x-ai-YYYY-MM|X-AI-YYYY-MM]]`.
- Historical imports should be normalized for clinical consistency; see `references/digest-normalization.md`.
- Daily digest automation exists as Hermes cron job `daily-ai-x-digest-to-obsidian`, scheduled `0 8 * * *`, using `bird` JSON plus summarization.
- New daily editions use `digest_format: editorial-v1` and the `ai-x-digest` plus `unslop` skills. Write a private first draft, edit it, check the sources, and validate before publication. Use concrete story headings, adjacent source links, and optional advice. The historical H1, theme-count, and takeaway rules do not apply to this format.
- Absolute output path pattern: `/Users/skypawalker/Dropbox/Obsidian/public/digests/x-ai-YYYY-MM-DD.md`

Recommended workflow:

1. Resolve the vault path from `OBSIDIAN_VAULT_PATH`; do not pass literal `$OBSIDIAN_VAULT_PATH` to file tools.
2. Ensure the `public/digests/` folder exists.
3. Write the final Markdown digest directly to the absolute path. Direct filesystem writes are valid for Obsidian vaults and are safer than shell-quoting large multiline content through the CLI.
4. If the user asks to open the result in Obsidian, use the CLI after writing:

```bash
obsidian open path="public/digests/x-ai-YYYY-MM-DD.md"
```

For daily digest automation, keep collection scripts under `~/.hermes/scripts/<workflow>/` and raw/state data under `~/.hermes/data/<workflow>/`; only the final curated digest belongs in the vault.
