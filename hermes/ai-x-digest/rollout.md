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

## Editorial and publication proof

1. Save collection results and inspected source text privately. A failed collection is an error. A successful no-news result stops with a private record and no public files, routes, feed item, or delivery URL.
2. Assign IDs once. Save a complete first draft, apply unslop as a separate rewrite, and save a separate edited edition.
3. Write `review.md` with concrete before/after edits, factual corrections, inspected sources, and remaining uncertainty. Compare the edited facts with the draft and source text. Preserve attribution and exact quote meaning.
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
