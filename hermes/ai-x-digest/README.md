# Hermes daily digest package

This package supplies the `editorial-v2` producer for the independent daily reader. Changes to these sources do not install files, edit cron, deploy the app or send messages. The reviewed producer revision installs after its reader passes live verification.

The public vault keeps one authored Markdown file per day. Story markers give the reader persistent article paths without separate public story files. Hermes must retain IDs through headline changes, reorders, retries, and archived corrections. It must complete a separate unslop rewrite and private draft/source comparison before accepting the candidate.

## Content and design

Hermes owns headlines, prose, section labels, decks and optional sourced visual data. The reader owns typography, backgrounds, columns, spacing, image treatment and chart drawing. The same accepted edition supplies the website, article pages and full-text RSS. No second public draft or formatter belongs in Hermes.

The optional `story_metadata` map uses persistent story IDs. Each entry requires `section` and may contain `deck` and one `image` or `bar` visual. See [the exact schema](contract.md#editorial-metadata-and-design-separation). Hermes inspects actual source media, observes image dimensions and records provenance privately. Every visual cites an adjacent source in its own story.

Charts preserve numeric values, periods, units and explicit qualifiers. Hermes must omit unverifiable or unhelpful visuals. It must not interpolate data or fill empty space with stock or generated images. The unslop rewrite and source comparison cover decks, captions and chart labels too.

The reader's AST validator checks visual metadata during scoped publication. The Python checker still owns editorial structure and size. Neither validator proves that a caption or numeric claim matches its source.

The shared scoped publisher validates the accepted private request before public writes. Humans and Hermes both use `scripts/publish-from-vault.sh --digest PRIVATE_REQUEST.json`. The request, first draft, edited copy, source snapshots, and review stay outside the repository and public vault. See [the reader's publication contract](../../apps/daily/README.md#accepted-publication) for the exact request and receipt fields.

## Install phases

Run these commands only during the separately authorized rollout. Use the checker phase first.

```sh
python3 hermes/ai-x-digest/install.py --hermes-home /Users/skypawalker/.hermes --phase verifier
```

This phase installs only the dual legacy/v1/v2 checker and `story_identity.py`. The installer packages that helper from the canonical source in this directory. It keeps no second implementation in runtime. Test the installed checker against private fixtures before the producer phase.

```sh
python3 hermes/ai-x-digest/install.py --hermes-home /Users/skypawalker/.hermes --phase producer
```

The producer phase installs every manifest file, including the skills and references. It remains the default for compatibility with the earlier installer interface. Both phases stage files, record hashes and prior existence, and back up replaced files. Failure restores completed replacements and removes files that did not exist before. Unrelated files and cron stay untouched.

Recovery receipts live under `~/.hermes/backups/ai-x-digest-editorial-v2-TIMESTAMP/`. Restore each listed file whose `existed` value is true from its matching backup path. Remove only listed files whose value is false. A `recovery-failed` receipt names unresolved restores. Keep each previous installation backup for producer rollback.

## Verification

From the repository root, run `python3 -B -m unittest discover -s hermes/ai-x-digest/tests`. The compatibility suite exercises real publication into temporary Git, vault, state, and bare-remote directories. It verifies v2 acceptance, accepted-request retry, malformed and mutated IDs before promotion, isolated helper packaging, checker-phase rollback, and visible archived attribution.

The cron fixture imports Pluto's actual Hermes CLI parser and edit function. It substitutes an in-memory job store and API. It proves only prompt/skills change while ID, schedule, state, inherited model/provider, Telegram delivery, primary skill, and another job survive. It skips when that Pluto source checkout is unavailable. It never invokes live cron or Telegram.

`tests/test_editorial_metadata_contract.py` checks the producer's complete Markdown example with the packaged editorial checker. Reader tests cover metadata validation and rendering. This example check does not prove source accuracy or that a scheduled run followed the editorial instructions.

Follow [the staged rollout](rollout.md) for adoption, delivery accounting, cutover, and rollback. The producer uses the verified daily domain after the authorized cutover. Returning the scheduled agent's text does not prove Telegram delivery.

The user selected direct deployment from Pluto. After the accepted source push, use `scripts/release-daily-from-pluto.py` with the accepted commit and private request. GitHub Actions keeps build/test checks only. The deployment credential remains in the protected Pluto configuration file. Install the new producer and cron prompt only after live reader verification, as described in `rollout.md`.
