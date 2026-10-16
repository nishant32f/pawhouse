# X-AI digest index hierarchy

Use this reference when creating, repairing, or auditing Nishant's X-AI digest indexes.

## Canonical files

- Daily digest: `digests/x-ai-YYYY-MM-DD.md`
- Monthly index: `digests/x-ai-YYYY-MM.md`
- Year parent index: `digests/x-ai-YYYY.md`

These are private Obsidian paths outside `public/`. Reader editions use `/editions/YYYY-MM-DD/`; old website year/month indexes redirect to `/archive/`. They are not new Quartz inputs.

## What not to create

Do not create or preserve these as first-class digest indexes:

- `digests/X-AI Hub.md`
- `digests/Imported Digests.md`
- `digests/Imported Digest Index.md`
- `digests/Imported Home.md`
- bare monthly files such as `digests/2026-03.md`

Preserve the inventoried accepted historical notes during relocation. Do not regenerate indexes or delete accepted bytes as part of the move.

## Link rules

Daily digest `## Backlinks` should include:

```markdown
- [[index|Mindscape]]
- [[digests/x-ai-YYYY|X-AI YYYY]]
- [[digests/x-ai-YYYY-MM|X-AI-YYYY-MM]]
```

Monthly index backlinks should include:

```markdown
- [[index|Mindscape]]
- [[digests/x-ai-YYYY|X-AI YYYY]]
```

The year parent should list all monthly indexes for that year and backlink `[[index|Mindscape]]`.

## Repair workflow

1. Back up touched digest files outside the hosted tree, preferably under `<vault>/.graphify/backups/<run>/`.
2. For a new accepted revision, update monthly indexes from existing `x-ai-YYYY-MM-DD.md` files.
3. For a new accepted revision, update the year parent from existing `x-ai-YYYY-MM.md` monthly indexes.
4. Rewrite stale links from `X-AI Hub`, `Imported Digest*`, or bare `YYYY-MM` to the new year/month targets.
5. Remove obsolete index files once their links have been migrated.
6. Run the X-AI digest verifier:

```bash
python /Users/skypawalker/.hermes/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py /Users/skypawalker/Dropbox/Obsidian
```

7. Rebuild private Graphify when requested. Publish accepted digest revisions through the shared R2 publisher, without broad notes publication. If digest filename casing changed, verify the Graphify Obsidian rebuild script still recognizes lowercase `digests/x-ai-YYYY-MM-DD.md` and produces `NEXT_DIGEST` / `INDEXED_BY_MONTH` edges.
