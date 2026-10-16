# About profile verification

Verified on Earth on 16 October 2026 using Node 22.16.0 and Quartz 4.5.2. Preview was `http://localhost:8086/about`.

| Check                | Result                                                                                                                                                                                             |
| -------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Completed résumé     | All six employers, eight roles, ten date spans and both degrees appear. VIRGIO begins October 2021. Spectrum and Tectonic share one stint.                                                         |
| Build                | 349 inputs produced 1,208 files. Native `about.html`, sitemap entry, search content and `about-og-image.webp` exist.                                                                               |
| Navigation test      | Fails without ProfileNav. Passes for root, profile, nested note, folder and tag URLs.                                                                                                              |
| Tests and TypeScript | `npm test` passes all 70 tests. `npx tsc --noEmit` passes.                                                                                                                                         |
| Full check           | `npm run check` fails on existing formatting. Its 303 warning lines match the recorded pre-code baseline exactly. No new warnings.                                                                 |
| Responsive layout    | 360, 768 and 1,280 pixels, light and dark. No profile overflow. One page H1, one site nav, loaded 120px portrait.                                                                                  |
| Interaction          | Search for Nishant Khurana returns the profile. Theme toggle, visible keyboard focus and garden popovers work. Browser reports no page errors.                                                     |
| Garden preservation  | Home, wisdom folder, hope tag and Huberman Protocols retain their normal layouts. Nested navigation and Back/Forward restore the expected body slug and furniture.                                 |
| Route                | Local Quartz serves `/about` and redirects `/about.html` to it. `/about/` is not an acceptance route. Live Pages remains unverified until release.                                                 |
| Obsidian sync        | Existing sync entry point ran with disposable repo, source and state folders. Profile, homepage and portrait remained byte-identical. A repository-only note disappeared through `rsync --delete`. |
| Public copy          | No résumé phone/email, private source paths, résumé files, interview drafts or TODO markers. Public social destinations match the existing homepage.                                               |

Screenshots are in [about-profile/](about-profile/). They include both themes at each width, career typography and a normal garden note.

Install on this Mac required `SHARP_IGNORE_GLOBAL_LIBVIPS=1 mise x node@22.16.0 -- npm ci`. This uses sharp's supported prebuilt dependency path. No dependency or lockfile changed.

The real Pluto checkout and live Obsidian vault were untouched. Before release, follow [the source integration runbook](../runbooks/about-profile.md). This matters because sync deletes content absent from the vault.
