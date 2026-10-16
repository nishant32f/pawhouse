# Pawhouse

[![Deploy Quartz site to GitHub Pages](https://github.com/nishant32f/pawhouse/actions/workflows/deploy.yml/badge.svg?branch=main)](https://github.com/nishant32f/pawhouse/actions/workflows/deploy.yml)

Pawhouse contains the Quartz notes website, the Machine Herald newspaper app, and the Hermes content publisher. The canonical checkout runs on Pluto.

- Notes website: <https://nishantkhurana.me/>
- Machine Herald: <https://daily.nishantkhurana.me/>
- Full-text RSS: <https://daily.nishantkhurana.me/rss.xml>
- Source notes: `/Users/skypawalker/Dropbox/Obsidian/public`
- Published content snapshot: `content/`

## Publishing ordinary notes

From this repository, run:

```bash
npm run publish -- "Update notes"
```

That command syncs the vault notes with `rsync`, builds Quartz, commits changes, and pushes the current branch. A push to `main` triggers the GitHub Pages deployment workflow shown by the badge above.

Digests use private Markdown at `/Users/skypawalker/Dropbox/Obsidian/digests`, outside the public website tree. Hermes curates Markdown, the publisher writes neutral JSON and full RSS to private R2, and `apps/daily/` renders the newspaper. Normal editions require no Git content commit or app deployment. Bookmarks live only in Karakeep.

Read [AGENTS.md](AGENTS.md), the [reader guide](apps/daily/README.md), the [editorial contract](hermes/ai-x-digest/contract.md), and the [operations guide](hermes/ai-x-digest/rollout.md) before changing publication.

## Local preview

```bash
npm run quartz -- build --serve
```

Quartz documentation: <https://quartz.jzhao.xyz/>
