# Local acceptance, 15 October 2026

Verified on Pluto. Production activation remains pending. Full evidence and rollout status are in [the implementation record](../../docs/plans/2026-10-15-1100-feat-hermes-newspaper-digest-plan.html#implementation-record).

| Contract     | Local evidence                                                                                                                                                                                                           |
| ------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| R1–R4        | Real browser at 1440px, 390px, tablet, and 200% layout. Native article navigation, no JavaScript, keyboard focus, theme/size persistence, blocked fonts, and print. Accessibility audit had 34 passes and no violations. |
| R5–R7        | Accepted prose and source URLs preserved. Separate private editing evidence remains required. Quiet-day and collection-error contracts remain distinct.                                                                  |
| R8–R10       | AST/identity validation and real temporary Git/vault publication. Missing/mutated IDs reject before promotion. Retry reuses the accepted commit.                                                                         |
| R11–R12      | Installer replacement/recovery fixtures and actual Hermes CLI against an in-memory API. Interrupted promotion and failed release preserve accepted state. Production remains disabled.                                   |
| R13          | 178 historical dates retained; 17 app tests; 360 canonical pages. Four-story preview has 364 pages. Real local static-assets server returns full-text RSS with correct MIME and true 404.                                |
| Main website | 69 Quartz tests pass; TypeScript passes. Root check retains 300 pre-existing formatting warnings. Authored content, Quartz rendering, and Pages workflow are unchanged.                                                  |

Preview [reader](http://localhost:56548/) and [RSS](http://localhost:56548/rss.xml) run separately from production. Today's preview IDs exist only in its private fixture. The live vault stays editorial-v1.

Pending live proof includes the custom domain, deployment version, redirects, main navigation/discovery, runtime installation, cron cutover, canary delivery, and next scheduled output. Follow [the rollout](../../hermes/ai-x-digest/rollout.md) under separate activation authority.
