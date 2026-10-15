# Historical digest normalization for Obsidian

This reference governs unversioned historical imports. New daily editions use `digest_format: editorial-v2` after the staged producer rollout and the `ai-x-digest` skill, including its required `unslop` pass. Do not apply the archive's duplicate H1 or mandatory takeaway rules to editorial-v1 or editorial-v2 notes. Do not rewrite archived editions during a normal daily run.

Nishant explicitly prefers clinical consistency and rich backlinks over historical fidelity for digest imports.

When importing or cleaning historical digest material:

- Do not preserve legacy split filenames as first-class notes when they conflict with the current convention.
- Normalize old `YYYY-MM-DD-morning.md` and `YYYY-MM-DD-evening.md` files into one daily note:
  - `public/digests/x-ai-YYYY-MM-DD.md`
- Preserve legacy names/titles only as aliases and source provenance, not as visible primary structure.
- Keep backups outside the hosted public tree before destructive cleanup, e.g. under `<vault>/.graphify/backups/...`.
- Remove obsolete morning/evening files from the vault after successful normalized writes, so search/backlinks stay clean.
- Use only the canonical digest index hierarchy: year index `public/digests/x-ai-YYYY.md` containing monthly indexes, and monthly indexes `public/digests/x-ai-YYYY-MM.md` containing daily notes. Do not maintain a separate `X-AI Hub.md`, imported digest redirect, or bare `YYYY-MM.md` monthly index.

Required unversioned historical digest shape:

```markdown
---
title: "X-AI-YYYY-MM-DD"
date: YYYY-MM-DD
tags: [AI, digest, x]
type: daily-digest
source: bird-cli-json-and-imported-digests
aliases:
  - "old-import-filename"
---

# X-AI-YYYY-MM-DD

## Digest

...

## Source provenance

...

## Navigation

- Previous: [[digests/x-ai-YYYY-MM-DD|X-AI-YYYY-MM-DD]]
- Next: [[digests/x-ai-YYYY-MM-DD|X-AI-YYYY-MM-DD]]

## Backlinks

- [[index|Mindscape]]
- [[digests/x-ai-YYYY|X-AI YYYY]]
- [[digests/x-ai-YYYY-MM|X-AI-YYYY-MM]]
```

Required index structure:

- `public/digests/x-ai-YYYY.md` is the only year-level digest parent index.
- `public/digests/x-ai-YYYY-MM.md` monthly indexes link all normalized daily notes for that month.
- Do not keep a separate `X-AI Hub.md`, imported digest redirect indexes, or bare `YYYY-MM.md` monthly indexes.
- Do not create or keep `obsidian-value-map.md`; use `public/index.md` / `[[index|Mindscape]]` as the public garden/home backlink.

Verification checklist:

1. Count normalized daily files:
   - match `^x-ai-\d{4}-\d{2}-\d{2}\.md$`
2. Ensure old split files are gone:
   - no `^\d{4}-\d{2}-\d{2}-(morning|evening)\.md$`
3. For every daily note verify:
   - YAML frontmatter starts the file
   - `title`, `date`, `tags: [AI, digest, x]`, `type: daily-digest`
   - H1 starts with `# X-AI`
   - no clinical intro/blockquote line after the H1
   - Backlinks section links `[[index|Mindscape]]`, the year parent `[[digests/x-ai-YYYY|X-AI YYYY]]`, and the monthly index `[[digests/x-ai-YYYY-MM|X-AI-YYYY-MM]]`
   - Navigation section exists
   - Navigation and Backlinks are the final top-level sections in the note, in that order
   - No `### Run metadata` section
   - unversioned generated notes from the old workflow use the label `Practical takeaway:`; editorial-v1 and editorial-v2 editions omit it and put sources beside each story
4. Check explicit path wikilinks resolve within the vault.
5. Use Obsidian CLI backlinks as a smoke test, for example:
   - `obsidian backlinks path="digests/x-ai-2026.md" format=json`
6. For a deterministic vault-wide format check, run:
   - `python /Users/skypawalker/.hermes/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py /Users/skypawalker/Dropbox/Obsidian`
