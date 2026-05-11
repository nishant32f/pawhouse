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

The source Obsidian vault publish folder is expected at `../obsidian/public`.

## Build, Test, and Development Commands

- `mise x node@22.16.0 -- npm ci`: install dependencies with the Node version Quartz expects.
- `mise x node@22.16.0 -- npx quartz build`: build the static site into `public/`.
- `mise x node@22.16.0 -- npx quartz build --serve --port 8080`: run a local preview server.
- `./scripts/sync-content-from-vault.sh`: copy notes from `../obsidian/public` into `content/`.
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

Treat `../obsidian/public` as the source of truth for publishable notes. Publish with:

```bash
npm run publish -- "Update notes"
```

The publish script runs `rsync --delete`, builds Quartz, stages all repo changes, commits with the provided message, and pushes the current branch to `origin`. A push to `main` triggers the GitHub Pages workflow.
