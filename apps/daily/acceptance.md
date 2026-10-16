# R2 reader implementation acceptance, 16 October 2026

U4 separates code artifacts from accepted content. These results cover isolated Pluto fixtures and local packaging. The production reader still uses its earlier Git release.

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
