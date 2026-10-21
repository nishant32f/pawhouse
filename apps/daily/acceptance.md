# Daily reader acceptance

## Approved newspaper layout, 21 October 2026

The reader follows the desktop/mobile layout approved from the 21 October preview. Its compact masthead carries the selected edition date, count and Inside links. Main articles and actual briefs have separate columns; secondary previews reuse authored summary HTML and retain sources. Complete lead prose and canonical article/full-edition reading remain intact.

Verification ran on Pluto with Node 22.23.3. Astro check reported zero errors, warnings or hints; all 40 reader tests and the SSR build passed. Browser checks used the built Worker with isolated local R2 storage, seeded from the published 21 October accepted snapshot plus retained legacy, single-story and brief/archive fixtures. No production bucket was modified.

At 1440, 768, 390 and 320 pixels, all ten current stories appeared once, the four briefs stayed grouped, and the document had no horizontal overflow. Browser-driven article navigation and return links worked. Theme and text-size controls worked. With JavaScript disabled, article navigation and server-rendered search worked. The RSS, complete prose, source/figure, archived-anchor and publication-replacement integration checks passed.

Screenshots: [desktop](../../docs/previews/2026-10-21-newspaper/desktop.png), [mobile](../../docs/previews/2026-10-21-newspaper/mobile.png). The frozen prototype's one-off DeepInfer drawing is not part of the general renderer; authored media remains the content source. This is local verification, not a production deployment receipt.

## Production acceptance, 16 October 2026

PR #19 is merged and the R2 cutover is live. All 179 accepted editions passed 380 live route checks, including complete prose, archive, search, article pages, sitemap, RSS bytes and MIME. Existing RSS identities remain unchanged. Desktop and mobile browser checks passed.

A subsequent accepted internal-link correction changed reading and RSS while Git HEAD and Worker version stayed fixed. All 188 Markdown sources and indexes are private in Obsidian. All eleven installed Hermes files matched the reviewed manifest at cutover, with only the cron prompt changed.

The notes website retained 162 ordinary notes and no digest discovery entries. Its old digest and digest-tag URLs return 404. Redirects and temporary preview infrastructure were explicitly excluded. The first unattended run after cutover was scheduled for 17 October, 08:00 IST, and remained unobserved at acceptance.

See [current operations](../../hermes/ai-x-digest/rollout.md#current-production-state) and the private activation proofs on Pluto. The sections below are dated historical evidence, not instructions to reactivate the Git reader or repeat migration.

## Earlier U4 implementation evidence, 16 October 2026

U4 separated code artifacts from accepted content. At this earlier snapshot, results covered isolated Pluto fixtures and local packaging, and production still used its Git release.

| Contract            | Evidence                                                                                                                                                                                                                                                                                                     |
| ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Code release        | A private clone installs and checks the neutral content package, then the app. Its complete SSR handler and client assets pass a real Wrangler dry-run. The cache identifies only the code revision. Deployment uses `dist/server/wrangler.json`.                                                            |
| Content proof       | The verifier reads immutable objects from the selected frozen bundle. It checks the exact publication and compiler revisions, expected code revision, every edition/read/story route, archived bodies, adjacent source links, figures, discovery, complete RSS bytes and MIME, and a real unknown-route 404. |
| Recovery            | HTTP errors, missing prose, altered figures, stale content, malformed RSS and false 404s fail proof. A failed retry preserves the publication ID and prior proof, records `verificationError`, returns to `published`, and blocks delivery. Completed and ambiguous delivery receipts remain unchanged.      |
| Local verification  | The 58 release tests pass on Pluto. The fixture runs the generated SSR handler against local R2 with accepted legacy, current and archived Markdown fixtures. It copies prebuilt SSR output into private temporary storage. The proof utility also passes TypeScript checking.                               |
| Activation boundary | No R2 resource, Worker deployment or private backend switch was performed for U4. Real Cloudflare preview, runtime CPU and production publication proof remain pending deployment authorization. A local fixture result is not that proof.                                                                   |

For an active R2 publication, use `python3 scripts/daily-release.py verify --request PRIVATE_REQUEST --origin READER_URL --code-revision CODE_SHA`. This command requires neither digest Git ancestry nor a build, Wrangler or Quartz. Add `--version` only with the actual separately observed Worker version.

Before backend activation, select `--bundle FROZEN_BUNDLE` instead of `--request`. This verifies the selected preview URL without mutating a publication receipt. The production code-release wrapper uses `--commit CODE_SHA` with either `--request PRIVATE_REQUEST` or `--bundle FROZEN_BUNDLE`. Its private Cloudflare credentials and actual deployment-version lookup remain required. It retains the selected live content and rejects older code or removed routes.

The record below describes the earlier deployed Git reader. Its revision, tests and live proofs do not describe the R2 implementation.

## Earlier reader acceptance, 15 October 2026

The separate reader and full-text RSS are live. Pluto deploys the accepted Git revision directly. GitHub runs reader CI; Quartz keeps its independent Pages deployment.

| Contract     | Evidence                                                                                                                                                                                                                                                                                                                                                |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| R1–R4        | Earlier browser acceptance covered desktop, 390px phone, tablet, 200% layout, no JavaScript, keyboard focus, themes, text size, blocked fonts, and print. Accessibility audit had 34 passes and no violations. Live desktop/mobile checks confirmed the newspaper layout, self-hosted fonts, article reloads, and no horizontal overflow.               |
| R5–R7        | Today's accepted prose and source URLs survived identity adoption unchanged. The installed producer requires a separate unslop edit and private comparison with inspected sources. Quiet-day and collection-error behavior remain distinct.                                                                                                             |
| R8–R10       | 94 Python tests pass. A real uncached build and Wrangler dry-run pass without canonical app dependencies. Invalid requests fail before deployment, and failed retries cannot authorize delivery.                                                                                                                                                        |
| R11–R12      | All seven installed producer files match reviewed source bytes. The supported cron edit changed only the prompt. Job identity, schedule, state, skills, null model/provider, Telegram settings, and all other jobs remain unchanged. An older live revision candidate was refused; its existing article still returned 200. No production rollback ran. |
| R13          | Full live verification passed 178 dates across 366 routes, complete prose/source comparisons, RSS identity/full text/MIME, discovery, and a real 404. The feed has one item per actual edition. The 17 app tests pass.                                                                                                                                  |
| Main website | Today's four headlines and seven source links passed live checks. The existing footer gains Daily and Daily RSS links. The 69 Quartz tests, TypeScript, focused formatting, and full Quartz build pass. Root formatting retains 301 existing warnings outside changed paths.                                                                            |

The deployed source is `d774fdf21697e4492f7356fff520531ea2fb2bcb`. A real release through `release-daily-from-pluto.py` passed with Individual Workers Editor limited to `pawhouse-daily` and recorded Cloudflare version `f75749b3-b99f-4f6d-8d64-b5621aeb0dcc`. The accepted publication receipt is `readerverified`.

- [Reader](https://daily.nishantkhurana.me/)
- [Full-text RSS](https://daily.nishantkhurana.me/rss.xml)
- [Today's edition](https://daily.nishantkhurana.me/editions/2026-10-15/)

Existing dated knowledge URLs remain available. No external redirect rules were added. No duplicate Telegram message or monitor was created.

The next scheduled Hermes run is **16 October 2026 at 08:00 IST**. Its generated edition and actual Telegram delivery have not been observed. Returning text cannot complete its delivery receipt.

Implementation review `20261015-164051-e36143ee` and Pluto deployment review `20261015-202937-ee6ba1e2` completed; all confirmed findings are fixed. Their external adapter failed before provider egress, so both used an in-process adversarial fallback. Footer review `20261015-210034-c111c23c` completed without findings.

See the [live activation record](../../docs/plans/2026-10-15-1100-feat-hermes-newspaper-digest-plan.html#activation-revision) and [rollback procedure](../../hermes/ai-x-digest/rollout.md). Private credentials, source captures, drafts, reviews, backups, and release receipts remain outside the repository and public vault.

## Direct cutover selected on 16 October 2026

The user authorized merging PR #19 and completing R2 deployment and the Hermes cutover. They then removed legacy redirects, isolated preview infrastructure and downtime requirements from the scope. Historical verification records above describe the earlier system and do not require keeping old website digest pages. Verify the live newspaper, archive and complete RSS against accepted sources. Preserve source backups and the existing job's schedule and delivery controls. Do not send a migration Telegram message.
