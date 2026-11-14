# Digest notes in Obsidian

Convention for this user:

- The digest runs in Hermes's `digest` profile sandbox. It reads accepted digests from the read-only mirror `/vault-mirror/digests/` and writes only `/outbox/digest-staging/YYYY-MM-DD/`.
- Vault digest folder: `digests/`. Only the publisher job on Nishant's Mac writes it.
- Daily X-AI digest filename pattern: `x-ai-YYYY-MM-DD.md`
- Year digest parent index: `digests/x-ai-YYYY.md` (for example `x-ai-2026.md`; title/H1 stay `X-AI 2026`)
- Monthly digest indexes: `digests/x-ai-YYYY-MM.md`
- Daily notes should end with `## Navigation` followed by `## Backlinks`, linking to `[[index|Mindscape]]`, `[[digests/x-ai-YYYY|X-AI YYYY]]`, and `[[digests/x-ai-YYYY-MM|X-AI-YYYY-MM]]`.
- Historical accepted imports preserve exact bytes; see `references/digest-normalization.md`.
- Daily digest automation is Hermes cron job `ai-x-digest` in the `digest` profile, at 08:00 Asia/Kolkata, using the `bird` MCP tool's JSON plus summarization.
- The active R2 producer uses `digest_format: editorial-v2` and the `ai-x-digest` plus `unslop` skills. Write a private first draft, edit it, check the sources, and validate before publication. Use concrete story headings, adjacent source links, and optional advice. The historical H1, theme-count, and takeaway rules do not apply to this format.
- Follow `ai-x-digest` for four discovery categories and private collection/selection records. Normal v2 editions aim for 10 to 14 distinct items, with shorter quiet days. Use dated catch-up and check recent editions for repeats.
- Staged output path pattern: `/outbox/digest-staging/YYYY-MM-DD/files/x-ai-YYYY-MM-DD.md`
- Digest illustrations use optional `story_metadata` frontmatter under the `ai-x-digest` contract. Hermes supplies inspected media, captions and chart facts. The reader owns their HTML and design. Do not apply general Quartz raw-image or asset-copying advice to this workflow.

Recommended workflow:

1. Keep the draft, edited candidate, source snapshots and run records under `/workspace/ai-x-digest/<date-and-run>/`.
2. Follow `ai-x-digest` for persistent IDs, optional sourced editorial metadata, the separate unslop pass, and the staging folder. Review prose, decks, captions, labels and numerical bounds against the inspected sources.
3. Stage the edition, changed indexes, changed previous note, Telegram text, review and `READY.json` as `ai-x-digest` describes. The sandbox writes no request. Only the publisher job on the Mac promotes accepted files into the vault.

Only the final curated digest belongs in the vault.
