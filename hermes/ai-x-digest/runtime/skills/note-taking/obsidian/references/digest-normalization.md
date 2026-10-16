# Accepted historical digest sources

Accepted history uses `<vault>/digests/`, outside `<vault>/public/`. Preserve exact source bytes, aliases, prose, IDs, archived bodies, source associations and existing index notes. Do not normalize accepted historical prose, add IDs to legacy editions, or split morning/evening sources during relocation.

Use `python3 scripts/daily-history.py inventory --legacy-sha FULL_LEGACY_SHA --compiler-revision FULL_CURRENT_SHA --output PRIVATE_DIRECTORY --rss ACCEPTED_RSS` from Pawhouse for the one-time pinned legacy bootstrap. The inventory includes exact edition and index bytes, hashes, source links, actual aliases, heading anchors, article routes and RSS identities. Its `relocate` command backs up and verifies all files before optional source removal. A different destination hash stops the operation. Hold the common publication lock across activation; use the Python `relocate()` function when the caller already holds it.

Keep the year and month indexes useful in Obsidian. Preserve historical navigation and backlinks during relocation. Make later navigation changes in explicit new accepted revisions. A normal daily publication may change only the previous daily note's Next link alongside the new edition and its affected indexes.

New editions use `editorial-v2`, the `ai-x-digest` skill and a separate unslop pass. The checker still accepts unversioned and editorial-v1 archives without changing their editorial rules. Its default is `<vault>/digests`; use `--digest-dir PATH` only for private staging or an explicit legacy fixture.

Never use broad note publication, a Git content commit, Quartz proof or a Worker deployment for a digest. See the reviewed R2 contract in Pawhouse `hermes/ai-x-digest/contract.md`.
