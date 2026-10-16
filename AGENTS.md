# Repository Guidelines

## Project Structure & Module Organization

This repository is a Quartz site for publishing the Pawhouse Obsidian notes.

- `content/` contains Markdown notes that are built and deployed.
- `quartz/` contains the Quartz application source and plugin system.
- `quartz.config.ts` controls site settings, plugins, theme, `baseUrl`, and title.
- `quartz.layout.ts` controls page layout components.
- `scripts/` contains local helper scripts, including vault-to-site syncing.
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

Run `npm run format` before large code changes. Avoid editing generated `public/` files.

## Testing Guidelines

For code changes, run:

```bash
npm run check
npm test
```

For content-only changes, at minimum run:

```bash
mise x node@22.16.0 -- npx quartz build
```

Confirm new notes render locally if they introduce embeds, links, callouts, or frontmatter changes.

## Commit & Pull Request Guidelines

Recent local commits use short imperative messages, for example `Use main branch for Pages deploy`. Upstream Quartz commits may use Conventional Commit prefixes such as `fix(cli): ...`; follow that style for Quartz source changes.

PRs should include a concise summary, affected areas (`content`, `quartz`, `scripts`, or workflows), validation commands run, and screenshots for visible layout/theme changes.

## Publishing Notes

Treat `/Users/skypawalker/Dropbox/Obsidian/public` as the source of truth for publishable notes. Publish with:

```bash
npm run publish -- "Update notes"
```

The publish script runs `rsync --delete` for ordinary notes, excluding root `public/digests/`. It builds Quartz, stages all repo changes, commits with the provided message, and pushes the current branch to `origin`. A push to `main` triggers the GitHub Pages workflow.

Digests use private vault Markdown and the R2 publisher described in `hermes/ai-x-digest/rollout.md`. Ordinary sync must neither import public digests nor delete any existing legacy destination digests. The retirement change removes `content/digests/` explicitly and Quartz ignores `digests/**`.

Keep the Quartz ignore, removal and navigation changes unmerged until replacement history and every exact HTTP 301 pass live verification. Installing ignore early would hide legacy pages on the next notes build. At authorized retirement, apply the matching public-vault homepage and About edits from their private reviewed snapshots before the next notes sync. Preserve accepted sources and backups.

`scripts/daily-redirects.py prepare --inventory INVENTORY --output PLAN` consumes the pinned U5 inventory. `preflight --inventory INVENTORY` reads the personal Cloudflare account, DNS, token permissions and conservative Free capacity. Under explicit deployment authorization, `apply --inventory INVENTORY --reader-proof U4_PROOF` requires the exhaustive U4 proof for that publication and rechecks its served revision before enabling redirects. It creates only its dedicated list and rule and records private resource ownership for safe retry. `verify --inventory INVENTORY` requires actual HTTP 301, exact Location with preserved queries, final 200, and unknown-date 404. API success alone does not permit Quartz removal. See `python3 scripts/daily-redirects.py --help` for private report and state paths.

Redirect preflight uses the canonical account-owned token through `/accounts/1688bfec49a43a217df10ed33b86e300/tokens/verify` and its token-details GET. It needs Account API Tokens Read for self-policy inspection, plus Account Filter Lists Edit, Bulk URL Redirects Edit, Zone Read and DNS Read. Account API Tokens Write is unnecessary. Keep the existing credential unchanged during implementation; a 403 stops preflight and does not prove resources are absent.
