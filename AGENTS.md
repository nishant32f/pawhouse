# Repository Guidelines

## Project Structure & Module Organization

This repository contains the Pawhouse notes website, the Machine Herald reader, and the Hermes digest publisher. Work on Pluto at `/Users/skypawalker/Dev/pawhouse`.

| Component         | Source of truth                                                            | Output                                                                    |
| ----------------- | -------------------------------------------------------------------------- | ------------------------------------------------------------------------- |
| Quartz            | `/Users/skypawalker/Dropbox/Obsidian/public`                               | `https://nishantkhurana.me` through GitHub Pages                          |
| Hermes curator    | Accepted private Markdown in `/Users/skypawalker/Dropbox/Obsidian/digests` | One authored edition per day, with private indexes                        |
| Content publisher | Accepted version 2 request and shared neutral compiler                     | Immutable JSON and full RSS in private R2 bucket `pawhouse-daily-content` |
| Daily reader      | Selected R2 manifest                                                       | Newspaper at `https://daily.nishantkhurana.me` and `/rss.xml`             |

Hermes owns research, curation, factual checks and a separate unslop rewrite. The publisher owns validation, JSON and RSS. The app owns fonts and layout. Bookmarks belong only in Karakeep.

- `content/` contains Markdown notes that are built and deployed.
- `quartz/` contains the Quartz application source and plugin system.
- `quartz.config.ts` controls site settings, plugins, theme, `baseUrl`, and title.
- `quartz.layout.ts` controls page layout components.
- `apps/daily/` contains the request-time Cloudflare Worker reader. Read its [guide](apps/daily/README.md).
- `hermes/ai-x-digest/` owns editorial instructions, the neutral content package and installed Hermes files. Read its [contract](hermes/ai-x-digest/contract.md) and [operations guide](hermes/ai-x-digest/rollout.md).
- `scripts/` contains shared publication, history, release and vault-sync helpers.
- `.github/workflows/deploy.yml` builds and deploys the site to GitHub Pages from `main`.
- `public/` is generated build output and should not be edited directly.

The source Obsidian vault publish folder is expected at `/Users/skypawalker/Dropbox/Obsidian/public`.

## Build, Test, and Development Commands

- `mise x node@22.16.0 -- npm ci`: install dependencies with the Node version Quartz expects.
- `mise x node@22.16.0 -- npx quartz build`: build the static site into `public/`.
- `mise x node@22.16.0 -- npx quartz build --serve --port 8080`: run a local preview server.
- `./scripts/sync-content-from-vault.sh`: copy notes from `/Users/skypawalker/Dropbox/Obsidian/public` into `content/`.
- `npm run publish -- "Update notes"`: sync, build, commit, and push the current branch.
- `npm run check`: run TypeScript checking and Prettier validation.
- `npm test`: run Quartz’s test suite via `tsx --test`.

## Coding Style & Naming Conventions

Use the existing Quartz TypeScript style. Keep two-space indentation, ES modules, and descriptive camelCase names for variables/functions. Markdown files may use human-readable Obsidian titles with spaces, for example `content/wisdom/tech/Linux.md`.

Format changed files only. Avoid bulk-formatting unrelated notes or editing generated `public/` files.

## Testing Guidelines

For Quartz code changes, use Node 22.16.0 and run:

```bash
npm run check
npm test
```

For content-only changes, at minimum run:

```bash
mise x node@22.16.0 -- npx quartz build
```

Confirm new notes render locally if they introduce embeds, links, callouts, or frontmatter changes.

Daily and neutral content packages use Node 22.23.3. Run their package-local `npm run check`, `npm test`, and the Daily SSR build when those packages change. Publisher and installer checks run with `python3 -B -m unittest discover -s hermes/ai-x-digest/tests`. For agent-doc-only edits, check changed Markdown, manifest hashes and installation parity; do not rebuild or deploy the reader.

## Commit & Pull Request Guidelines

Recent local commits use short imperative messages, for example `Use main branch for Pages deploy`. Upstream Quartz commits may use Conventional Commit prefixes such as `fix(cli): ...`; follow that style for Quartz source changes.

PRs should include a concise summary, affected areas (`content`, `quartz`, `scripts`, or workflows), validation commands run, and screenshots for visible layout/theme changes.

## Publishing Notes

Treat `/Users/skypawalker/Dropbox/Obsidian/public` as the source of truth for publishable notes. Publish with:

```bash
npm run publish -- "Update notes"
```

The publish script runs `rsync --delete` for ordinary notes, excluding root `public/digests/`. It builds Quartz, stages all repo changes, commits with the provided message, and pushes the current branch to `origin`. A push to `main` triggers the GitHub Pages workflow.

## Daily publishing and operations

R2 and the Hermes cutover are live as of 16 October 2026, through PR #19. Digests use private vault Markdown and the R2 publisher described in `hermes/ai-x-digest/rollout.md`.

1. Read `python3 scripts/daily-history.py published` for the selected publication, expected head/ETag and last seven published editions.
2. Follow the editorial contract, stage and accept the exact candidate privately, then use `./scripts/publish-from-vault.sh --digest PRIVATE_REQUEST.json`.
3. Read the approved reader `codeRevision` from `~/.local/state/pawhouse-publication/reader-release.json`. Verify with `python3 scripts/daily-release.py verify --origin https://daily.nishantkhurana.me --code-revision FULL_CODE_SHA --request PRIVATE_REQUEST.json`.

Normal digest publication makes no Git content commit, push, Quartz build or Worker deployment. Keep code and content revisions separate. Code releases use `scripts/release-daily-from-pluto.py` only with separate deployment authorization, using the full generated SSR configuration. Never use an assets-only deployment.

Private backend and receipts live in `~/.local/state/pawhouse-publication/`. Credentials live in mode-0600 files under `~/.config/pawhouse-daily/`; never print or commit their values. The R2 publisher credential is restricted to objects in `pawhouse-daily-content`. Read current revisions from private receipts, not a hard-coded document snapshot. Ordinary sync must neither import public digests nor delete any existing legacy destination digests. `content/digests/` is retired and Quartz ignores `digests/**`. Do not restore digest files, navigation, tags or feed entries to the notes website.

The user selected a direct personal-app cutover on 16 October 2026. Do not install legacy redirects or create a temporary preview app. Old main-site digest URLs may stop working, and downtime is acceptable. This supersedes the original plan's redirect and isolated-preview gates.

The archive, newspaper, RSS and website removal passed live verification. The public-vault homepage and About edits are applied. Preserve accepted sources and backups. Job `4eb8e806b8bc` stays at 08:00 IST with inherited model/provider and Telegram delivery. Installation does not prove a future scheduled run or delivery. Never rerun the job or send a canary to check documentation changes.

The redirect CLI is unused in this rollout. It must not create lists, rules or tokens without a new explicit request for redirects.
