# Pawhouse

[![Deploy Quartz site to GitHub Pages](https://github.com/nishant32f/pawhouse/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/nishant32f/pawhouse/actions/workflows/deploy.yml)

Pawhouse is a Quartz site that publishes notes from the Obsidian vault publish folder.

- Live site: <https://nishant32f.github.io/pawhouse/>
- Source notes: `/Users/skypawalker/Dropbox/Obsidian/public`
- Published content snapshot: `content/`

## Publishing

From this repository, run:

```bash
npm run publish -- "Update notes"
```

That command syncs the vault notes with `rsync`, builds Quartz, commits changes, and pushes the current branch. A push to `main` triggers the GitHub Pages deployment workflow shown by the badge above.

## Local Preview

```bash
npm run quartz -- build --serve
```

Quartz documentation: <https://quartz.jzhao.xyz/>
