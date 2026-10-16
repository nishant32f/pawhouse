# Hermes digest operations

## Current production state

The R2 cutover and PR #19 completed on 16 October 2026. Machine Herald and full-text RSS read the private `pawhouse-daily-content` bucket through Worker `pawhouse-daily`. Accepted Markdown and indexes live at `/Users/skypawalker/Dropbox/Obsidian/digests`. The main website excludes digests; old digest URLs return 404. No redirects were installed.

Hermes job `4eb8e806b8bc` is enabled at 08:00 IST with inherited model/provider and Telegram delivery. The next run at cutover was 17 October, 08:00 IST, and was unobserved. Check current job and delivery evidence before reporting later success.

Read selected content and reader revisions from `~/.local/state/pawhouse-publication/`, including `backend.json` and `reader-release.json`. The private activation proofs and backups are under `~/.local/share/pawhouse-migrations/daily-r2-2026-10-16/activation/`. A live content correction changed the article and RSS without changing Git HEAD or the Worker version.

Use the editorial/publication and delivery-accounting sections below for daily work. The adoption, cron-edit and source-switch procedures document the completed migration and future authorized repairs. Do not replay the bootstrap, move sources again, recreate resources or rerun cron merely because this guide contains those commands. Owned Hermes documentation updates use the manifest installer and hash readback, without changing cron or sending Telegram.

## Completed adoption procedure

R2 production activation requires the user's explicit deployment instruction for this migration. Keep the existing producer and delivery until the replacement passes live verification. Preserve all source snapshots and historical publication records.

The user selected a direct cutover on 16 October 2026. Legacy website URLs do not need redirects, no temporary preview app is required, and downtime is acceptable. This supersedes earlier redirect, preview and availability gates. Preserve all accepted editions and verify the live newspaper, archive and RSS.

| Phase                                | Required evidence before continuing                                                                                                                                                                    |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Install the dual checker             | Private legacy, editorial-v1, v2, brief, and archived fixtures pass with the installed canonical helper. The current producer remains unchanged.                                                       |
| Inventory accepted history privately | Preserve every accepted edition, existing story ID and index byte from the pinned legacy snapshot. Check hashes, routes, aliases and RSS identities. Never infer story routes for older history.       |
| Verify the reader and domain         | Verify the pinned app artifact and actual home, dated/read/story pages, archive, search, complete RSS/MIME, sitemap, and missing-page behavior. Bind the domain only under its separate authorization. |
| Cut over discovery                   | Remove the website digest section after the replacement reader passes. No legacy redirects are required.                                                                                               |
| Install the producer and edit cron   | Install the complete manifest only after earlier phases pass. Accept the marker producer and change only the intended prompt/skills and later authorized delivery URL.                                 |

## Cron update prepared from the supported CLI

The source inspected on Pluto was `~/.hermes/hermes-agent/hermes_cli/subcommands/cron.py` and `hermes_cli/cron.py`. Its edit interface accepts `--prompt`, repeatable `--add-skill`, and preserves omitted fields. It has no prompt-file flag.

At the authorized producer phase, the supported command is:

```sh
hermes cron edit 4eb8e806b8bc \
  --prompt "$(cat hermes/ai-x-digest/cron-prompt.md)" \
  --add-skill ai-x-digest --add-skill obsidian --add-skill bird --add-skill unslop
```

The checked-in prompt selects `https://daily.nishantkhurana.me/editions/YYYY-MM-DD/`. Install it only after authorized domain and route verification. Do not replace the job, set its model/provider, alter its schedule or state, change delivery settings, or touch other jobs. Compare the complete before/after job records. Job `4eb8e806b8bc` stays at 08:00 IST with inherited null model/provider and Telegram delivery.

## Illustrated reader revision

Keep content and design as separate changes. Hermes supplies optional `story_metadata` under [the accepted contract](contract.md#editorial-metadata-and-design-separation). The app validates that data and renders the figures. Do not install a template, media service or second formatter into Hermes.

1. Inspect the source media and data for the accepted edition. Save provenance, observed image dimensions and numerical qualifiers in its private review.
2. Compare the draft and edited headlines, prose, decks, captions and chart labels with those sources. Preserve persistent IDs and every adjacent source.
3. Verify the pinned app with and without metadata. Check complete prose, sourced figures, article routes, legacy editions, mobile, desktop, print and full-text RSS. A design-only change must render the same accepted Markdown.
4. Publish the accepted private request and verify its accepted R2 generation from Pluto. Check actual live figures and complete RSS, including image URLs and numerical qualifiers. Record the content proof in its private receipt. No per-edition code deployment or Quartz proof belongs to content publication.
5. Install the reviewed producer with the existing producer phase. Compare all eleven installed manifest files against the accepted source bytes. Update only the intended cron prompt and skills through the supported CLI, then compare complete job records.

Do not rerun the scheduled job or send a canary Telegram message for this revision. Record the next scheduled run as unobserved until it happens. Installation proves file and prompt state, not future generation quality or delivery.

## Editorial and publication proof

1. Save collection results and inspected source text privately. A failed collection is an error. A successful no-news result stops with a private record and no public files, routes, feed item, or delivery URL.
2. Assign IDs once. Save a complete first draft, apply unslop as a separate rewrite, and save a separate edited edition.
3. Write `review.md` with concrete before/after edits, factual corrections, inspected sources, and remaining uncertainty. Compare prose, decks, captions, labels, image evidence and chart values with the draft and sources. Preserve numerical bounds, attribution and exact quote meaning.
4. Accept exact candidate bytes and hashes privately. Keep the accepted IDs and request unchanged on publication retries.
5. Stage only the edition, affected indexes, and immediate previous daily note privately. The previous note may change only its Next link. Let the scoped publisher validate and promote them under its lock.
6. Run `python3 scripts/daily-release.py verify --origin https://daily.nishantkhurana.me --code-revision FULL_CODE_SHA --request REQUEST` on Pluto. Check the frozen accepted generation and full reader/RSS content. Failed verification stays published and blocks delivery. One RSS item represents each actual date, including corrections. Keep code Git HEAD and Worker version fixed during content publication.

The deterministic checker proves structure. It cannot certify factual accuracy or establish that an agent performed an unslop rewrite. The separate saved draft, edited copy, source comparison, and review are the editorial evidence.

## Scheduled delivery accounting

Hermes auto-delivers the final text after the agent returns. Before returning dated text, `delivery-begin` records the attempt. It requires verified reader publication. The agent must not treat its generated text as a delivery receipt.

After Hermes supplies confirmed delivery evidence, a later receipt update may call `delivery-complete --request REQUEST --reference DELIVERY_ID`. An interruption or unknown outcome stays pending. An operator resolves it with `delivery-resolve --request REQUEST --outcome delivered|not-delivered --reference EVIDENCE`. Completed receipts suppress ordinary duplicate delivery. No additional Telegram send belongs in a private generation check.

## Rollback

Before any R2-only edition has been accepted, a failed initial switch may restore the prior compatible full publication path. Preserve source snapshots and restore the identical cron record and enabled state under the fence and common lock. Verify the restored reader and producer before resuming publication.

After any R2-only edition has been accepted, retain private sources and every accepted R2 generation. Select a previously verified R2-compatible reader and producer that support all retained editions. Never restore a Git-writing producer, a static reader, or an old website delivery URL for new editions.

Keep the daily reader domain active. Verify the selected manifest, newest accepted prose and complete RSS with the restored compatible pair before resuming publication. Preserve the job's ID, schedule, state, inherited model/provider, delivery configuration and other jobs. Keep the dual checker, persistent IDs, archived routes, source backups and private publication/delivery receipts. A pending delivery still requires evidence-based resolution before another dated message.

## Private-source writer switch

1. Inventory the full pinned legacy snapshot with `daily-history.py inventory`. Check actual editions, indexes, aliases, heading anchors, source hashes, story routes and RSS identities. Resolve every old publication/recovery receipt before activation. Explicit operator no-delivery closure requires reason and evidence; ambiguous scheduled delivery still needs genuine provider proof.
2. Use the pinned history inventory for the production R2 import. A separate preview bucket or Worker is unnecessary for this personal app. Verify retained editions, complete prose, archived sources and the feed against the accepted inventory. Keep source backups for recovery.
3. Between scheduled runs, fence scheduled and manual starts, then drain active tasks. Hold the common publication lock across final import, reader deployment, live verification, source relocation, backend switch and producer switch. Install sync exclusions before relocating anything. Use the library `relocate()` while holding that lock; do not invoke a second locking subprocess.
4. Copy and back up accepted sources outside the public subtree. Verify all bytes before deletion. Different destination bytes stop the switch. Keep Obsidian year/month indexes and historical prose unchanged. If a gate fails, preserve snapshots and follow the rollback boundary above before resuming.
5. Install the reviewed eleven-file manifest and compare every installed hash. Restore the identical cron job definition and enabled state before releasing the fence. Do not replace job `4eb8e806b8bc`, its 08:00 IST schedule, inherited model/provider, Telegram delivery or other jobs.
6. Verify an actual accepted publication with unchanged code revision and Worker version. Corrections/backfills produce no extra Telegram. Observe the next normal scheduled run separately; installation and local tests cannot prove that run or its delivery.

Remove the old website digest inputs after live reader verification. Do not install redirects. Keep accepted generations and source backups through rollback. Production activation still requires the user's deployment instruction, which was given for PR #19 on 16 October 2026.
