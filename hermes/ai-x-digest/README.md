# AI digest editorial release

Canonical source for the content-only `editorial-v1` release. The existing Quartz website renders this Markdown without a new layout or domain.

New editions select one lead and normally 2 to 4 supporting stories, with optional briefs and fewer stories on quiet days. Every edition gets a private first draft, a fact-preserving `unslop` pass, an edited copy, and a private review. Sources sit beside their stories. Unversioned archived editions keep their existing content and validation rules.

Run focused checks with `python3 -m unittest discover -s hermes/ai-x-digest/tests` from Pawhouse. Install the exact manifest with `python3 hermes/ai-x-digest/install.py --hermes-home /Users/skypawalker/.hermes`. The installer stages all files, records prior existence and backups, then replaces the listed files. A failed install restores files already replaced. It prints installed hashes on success. It does not alter cron.

After verification, update only the daily job's authored prompt from `cron-prompt.md` and append `unslop` to its existing skills through `hermes cron edit`. Preserve the job ID, primary skill, schedule, state, model/provider selection, delivery, and other jobs.

Generate one edition privately with the installed skills. Validate it, inspect source accuracy and the editing review, then copy only the accepted edition into the public vault and publish through Pawhouse. No separate story files, JSON formatter, newspaper styling, domain changes, or additional notification are part of this release.

Recovery copies and install receipts are under `~/.hermes/backups/ai-x-digest-editorial-v1-<timestamp>/`. The receipt records each file's prior existence and install status. To reverse a successful install, restore listed files whose `existed` value is true from their backup paths. Remove listed files whose value is false. Leave all other files alone. A `recovery-failed` receipt lists files that need manual recovery. Restore a revised public edition from its private source backup and republish if needed. The sanitized `hermes-setup-backup` repository remains a runtime mirror.
