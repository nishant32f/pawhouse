# Hermes daily digest package

This package supplies the `editorial-v2` producer for the independent daily reader. Changes to these sources do not install files, edit cron, deploy the app or send messages. The R2 producer is installed on Pluto. The cutover completed on 16 October 2026 through PR #19; see [current operations](rollout.md#current-production-state).

The private vault keeps one authored Markdown file per day. Story markers give the reader persistent article paths without separate public story files. Hermes must retain IDs through headline changes, reorders, retries, and archived corrections. It must complete a separate unslop rewrite and private draft/source comparison before accepting the candidate.

## Discovery and length

The producer checks official releases, repositories, builder reports and research before selecting. It compares the last seven published accepted editions and labels catch-up with the actual event date. Private collection and selection records distinguish failed sources, rejected candidates and no-news outcomes.

Normal editions aim for 10 to 14 distinct items. V2 permits up to eight full stories and six briefs. Quiet days may be shorter after a second discovery pass. The lead targets 140 to 200 words, supporting stories 70 to 120, and briefs 25 to 45. Hard limits remain 220 and 85. Legacy and v1 checks remain unchanged.

## Content and design

Hermes owns headlines, prose, section labels, decks and optional sourced visual data. The reader owns typography, backgrounds, columns, spacing, image treatment and chart drawing. The same accepted edition supplies the reader, article pages and full-text RSS. No second public draft or formatter belongs in Hermes.

The optional `story_metadata` map uses persistent story IDs. Each entry requires `section` and may contain `deck` and one `image` or `bar` visual. See [the exact schema](contract.md#editorial-metadata-and-design-separation). Hermes inspects actual source media, observes image dimensions and records provenance privately. Every visual cites an adjacent source in its own story.

Charts preserve numeric values, periods, units and explicit qualifiers. Hermes must omit unverifiable or unhelpful visuals. It must not interpolate data or fill empty space with stock or generated images. The unslop rewrite and source comparison cover decks, captions and chart labels too.

The reader's AST validator checks visual metadata during scoped publication. The Python checker still owns editorial structure and size. Neither validator proves that a caption or numeric claim matches its source.

The shared scoped publisher validates the accepted private request before accepted source writes. Humans and the scheduled publisher job use `scripts/publish-from-vault.sh --digest PRIVATE_REQUEST.json`. The request, first draft, edited copy, source snapshots, and review stay outside the repository and vault. See [the R2 contract](contract.md#r2-publication-and-history) for the exact request and receipt fields.

## Curator and publisher split

Hermes runs in a Lima VM on Pluto, set up by skyw-selfhost. Its `digest` profile is a curator only. It collects, drafts, applies unslop, reviews and stages one edition in `/outbox/digest-staging/D/`, with the changed indexes, the changed previous note, the review and the Telegram text. It reads X and Karakeep through gateway MCP tools and holds no secrets. It never publishes, writes a request or sends Telegram.

A job on macOS, owned by skyw-selfhost, builds the version 2 request, publishes, verifies the reader and writes the status file. Hermes's `main` profile sends that text. Scheduled receipts from this flow stop at `readerverified`. See [the staging contract](contract.md#hermes-curator-staging) and [the operations guide](rollout.md#hermes-vm-curator).

## Install phases

Use these phases for authorized installation or updates to owned Hermes files. The Hermes home is `/Users/Shared/hermes-config` on Pluto, which the VM mounts read-only. The initial rollout is complete. Documentation updates must refresh the manifest hashes, preserve installation backups, verify installed bytes and leave cron and delivery unchanged. A fresh adoption uses the checker phase first.

```sh
python3 hermes/ai-x-digest/install.py --hermes-home /Users/Shared/hermes-config --phase verifier
```

This phase installs only the dual legacy/v1/v2 checker and `story_identity.py`. The installer packages that helper from the canonical source in this directory. It keeps no second implementation in runtime. Test the installed checker against private fixtures before the producer phase.

```sh
python3 hermes/ai-x-digest/install.py --hermes-home /Users/Shared/hermes-config --phase producer
```

The producer phase installs every manifest file, including the skills and references. It remains the default for compatibility with the earlier installer interface. Both phases stage files, record hashes and prior existence, and back up replaced files. Failure restores completed replacements and removes files that did not exist before. Unrelated files and cron stay untouched.

Recovery receipts live under `HERMES_HOME/backups/ai-x-digest-editorial-v2-TIMESTAMP/`, for the `--hermes-home` given. Restore each listed file whose `existed` value is true from its matching backup path. Remove only listed files whose value is false. A `recovery-failed` receipt names unresolved restores. Keep each previous installation backup for producer rollback.

## Verification

From the repository root, run `python3 -B -m unittest discover -s hermes/ai-x-digest/tests`. The compatibility suite exercises real publication into temporary Git, vault, state, and bare-remote directories. It verifies v2 acceptance, accepted-request retry, malformed and mutated IDs before promotion, isolated helper packaging, checker-phase rollback, and visible archived attribution.

`tests/test_producer_contract.py` checks that the curator prompt and skill name the staging folder, the vault mirror and the sandbox verifier path, and no publish, history, release or delivery command. It does not prove that a scheduled run follows them. The cron job itself is created and tested in skyw-selfhost.

`tests/test_editorial_metadata_contract.py` checks the producer's complete Markdown example with the packaged editorial checker. Reader tests cover metadata validation and rendering. This example check does not prove source accuracy or that a scheduled run followed the editorial instructions.

Follow [the staged rollout](rollout.md) for adoption, delivery accounting, cutover, and rollback. The producer uses the verified daily domain after the authorized cutover. Returning the scheduled agent's text does not prove Telegram delivery.

Normal digest publication changes R2 content while code Git HEAD and Worker version remain fixed. Use `daily-release.py verify` for content proof. The code deployment wrapper is reserved for separately authorized code releases. Follow the [history inventory and relocation contract](contract.md#history-inventory-and-source-relocation) for the pinned bootstrap, report fields and collision checks. No live installation, cron edit, relocation, R2 import or deployment runs as part of package implementation.

## History tool prerequisites

The history inventory reuses Quartz's actual path and Markdown plugins plus the neutral content compiler. A fresh checkout needs both dependency trees, installed from their lockfiles. Use Node 22.16.0 for root Quartz dependencies and Node 22.23.3 for `hermes/ai-x-digest/content`. Then run the history CLI with Node 22.23.3 through the existing `mise` invocation. The helper resolves repository packages; no global Node packages or Python dependencies are required. Package implementation does not run installation against live Hermes.
