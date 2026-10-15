# Staged Hermes adoption

The user authorized production activation after merging PR #11. The reader deploys from Pluto; GitHub retains source history and CI only. Keep the existing producer and delivery until live reader verification passes.

| Phase                               | Required evidence before continuing                                                                                                                                                                                             |
| ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Install the dual checker            | Private legacy, editorial-v1, v2, brief, and archived fixtures pass with the installed canonical helper. The current producer remains unchanged.                                                                                |
| Adopt latest accepted IDs privately | Copy the latest accepted editorial-v1 edition privately. Add identifiers without changing its prose, quotes, qualifications, or source URLs. Inspect the exact diff and accept it. Do not infer story routes for older history. |
| Verify the reader and domain        | Verify the pinned app artifact and actual home, dated/read/story pages, archive, search, complete RSS/MIME, sitemap, and missing-page behavior. Bind the domain only under its separate authorization.                          |
| Cut over discovery                  | Apply verified redirects, navigation, and feed cutover only when their actual reader destinations pass. Preserve the old pages when redirects are unavailable.                                                                  |
| Install the producer and edit cron  | Install the complete manifest only after earlier phases pass. Accept the marker producer and change only the intended prompt/skills and later authorized delivery URL.                                                          |

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
4. Publish the accepted private request and release its pinned commit from Pluto. Check actual live figures and complete RSS, including image URLs and numerical qualifiers. Record reader and independent Quartz results in their private receipts.
5. Install the reviewed producer with the existing producer phase. Compare all seven installed manifest files against the accepted source bytes. Update only the intended cron prompt and skills through the supported CLI, then compare complete job records.

Do not rerun the scheduled job or send a canary Telegram message for this revision. Record the next scheduled run as unobserved until it happens. Installation proves file and prompt state, not future generation quality or delivery.

## Editorial and publication proof

1. Save collection results and inspected source text privately. A failed collection is an error. A successful no-news result stops with a private record and no public files, routes, feed item, or delivery URL.
2. Assign IDs once. Save a complete first draft, apply unslop as a separate rewrite, and save a separate edited edition.
3. Write `review.md` with concrete before/after edits, factual corrections, inspected sources, and remaining uncertainty. Compare prose, decks, captions, labels, image evidence and chart values with the draft and sources. Preserve numerical bounds, attribution and exact quote meaning.
4. Accept exact candidate bytes and hashes privately. Keep the accepted IDs and request unchanged on publication retries.
5. Stage only the edition, affected indexes, and immediate previous daily note privately. The previous note may change only its Next link. Let the scoped publisher validate and promote them under its lock.
6. Run `python3 scripts/release-daily-from-pluto.py --commit ACCEPTED_COMMIT --request REQUEST` on Pluto. Its Cloudflare credential stays in the private local file. Check actual reader and Quartz text. Keep independent main-site and reader results in private receipts. One RSS item represents each actual date, including corrections.

The deterministic checker proves structure. It cannot certify factual accuracy or establish that an agent performed an unslop rewrite. The separate saved draft, edited copy, source comparison, and review are the editorial evidence.

## Scheduled delivery accounting

Hermes auto-delivers the final text after the agent returns. Before returning dated text, `delivery-begin` records the attempt. It requires verified reader publication. The agent must not treat its generated text as a delivery receipt.

After Hermes supplies confirmed delivery evidence, a later receipt update may call `delivery-complete --request REQUEST --reference DELIVERY_ID`. An interruption or unknown outcome stays pending. An operator resolves it with `delivery-resolve --request REQUEST --outcome delivered|not-delivered --reference EVIDENCE`. Completed receipts suppress ordinary duplicate delivery. No additional Telegram send belongs in a private generation check.

## Rollback

Restore the previous installed producer files from the recorded install backup, then restore only the daily job's authored prompt and skills if they changed. Preserve its ID, schedule, state, inherited model/provider, delivery, and other jobs. Keep the dual checker available so accepted v2 content remains readable. Do not strip published IDs or delete archived routes to roll back code.

Domain and redirect rollback belongs to the authorized cutover procedure. Restore old-site delivery URLs when reversing that cutover. Keep accepted Markdown and private publication/delivery receipts. A pending delivery needs evidence-based resolution before another dated message.
