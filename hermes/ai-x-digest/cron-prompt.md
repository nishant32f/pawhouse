Daily task: curate Nishant's X-AI digest, run the required unslop editing pass, and stage the accepted edition and its Telegram text for publication. You do not publish or send anything.

Load `ai-x-digest`, `unslop` and `obsidian`. Do not load a `bird` skill. For new editions, the `ai-x-digest` editorial-v2 contract takes precedence over unversioned historical normalization rules.

Use today's date in Asia/Kolkata as `D`, in `YYYY-MM-DD` form. Your commands run in a sandbox with no secrets. Read accepted editions and indexes only from `/vault-mirror/digests/`, and public notes only from `/vault-mirror/public/`. Both are read only. Write only `/outbox/digest-staging/D/`. Keep private records under `/workspace/ai-x-digest/<date-and-run>/`. If `/outbox/digest-staging/D/READY.json` already exists, change nothing and stop with a short status.

Complete the five discovery categories in `ai-x-digest`: official releases, repositories, builder reports, research, and verification, review and security. A small X sample alone is insufficient. Read X only through the `bird` MCP tool's three calls: `home_timeline`, `search` and `post`. Read Karakeep only through the read-only `karakeep` MCP tool, for optional background research. Inspect selected primary sources, repository releases/licenses/platform limits and relevant paper results. Keep private collection and selection records with source snapshots, event dates, novelty checks and failure status. Compare the last seven published accepted editions, read from `/vault-mirror/digests/`. Label catch-up within seven days with its actual date and current reason; do not repeat an old project without a new development.

Aim for 10 to 14 distinct items in the main selection, usually one lead, five to seven supporting stories and four to six briefs. The v2 checker permits 11 full stories and 8 briefs. Counts are targets. If fewer than ten qualify, make a second focused discovery pass before accepting a shorter edition. Keep useful new repositories and builder tools eligible even when their launch posts sound promotional. Strip marketing, verify facts and link the repository. Do not infer growth from a single star count. Quiet days may remain short. Never pad with recurring themes or old saved posts.

Add the separate verification, review and security section that `ai-x-digest` describes: 3 to 5 items on software verification, pull request and code review, and security, on top of the main selection. Label each one `section: Verification, review and security` in `story_metadata`. Keep its full stories together after the main supporting stories and put its briefs last in `In brief`. For a vulnerability, give the affected versions, the fix and the advisory ID, and link the advisory. Omit the section rather than pad it.

Write roughly 140 to 200 words for the lead, 70 to 120 for supporting stories and 25 to 45 for briefs. These are soft targets. Keep material qualifications and omit generic significance paragraphs. Do not add filler to meet a length target.

Write a complete first draft privately, then load and apply `unslop`. Save a separate edited edition and a review with concrete edits and the sources actually inspected. Preserve facts, numbers, attribution, uncertainty, exact quotes, and URLs. Correct unsupported claims from their sources. No signal-quality preamble, duplicate H1, forced takeaways, or source appendix. Each story has a concrete headline, concise opening summary, and nearby sources.

Keep content and design separate. Hermes supplies optional `story_metadata` keyed by persistent story ID, following `ai-x-digest`. Each entry requires a plain-text section; deck and one sourced image or bar chart are optional. The app owns fonts, backgrounds, columns, spacing, image treatment and chart drawing. Emit no HTML, SVG, CSS, templates or layout fields. Keep one authored Markdown edition.

Inspect original media or data before including a visual. An image needs its actual HTTPS URL, observed intrinsic dimensions, alt text, caption, credit and same-story cited source. A bar chart needs 2 to 4 comparable points with explicit exact/approximate/greater-than/at-least qualifiers. Preserve every numeric value, period, unit and bound. Never interpolate or mix units. Omit a visual when useful evidence is unavailable; do not add stock or generated filler. Save provenance and source-to-caption/data comparisons privately. Apply the separate unslop edit to decks, captions and labels too.

Assign persistent story IDs before drafting and retain them across edits, reorders, and retries. Archive removed stories with their IDs, a correction, and original prose and sources. Never infer stories from old legacy content.

Use `digest_format: editorial-v2`. Stage exactly what the "Validate and stage" section of `ai-x-digest` lists, in `/outbox/digest-staging/D/`:

1. `files/x-ai-D.md`, the accepted edited edition.
2. `files/x-ai-YYYY-MM.md` and `files/x-ai-YYYY.md`, only when the new edition changes them.
3. `files/x-ai-P.md`, the previous edition, only when it changes. Change only its `Next` link.
4. `telegram.txt` and `review.md`.
5. `READY.json`, written last, with the SHA-256 of every staged file and of `telegram.txt`, and `kind: scheduled`.

Validate the staged files with `python3 /root/.hermes/external_skills/0/note-taking/obsidian/scripts/verify-x-ai-digest-format.py --digest-dir /outbox/digest-staging/D/files`. Accept the edited candidate only after comparing its facts and wording with the draft and inspected sources. Compare each staged edition that already exists in the mirror through `story_identity.validate_revision`. Record exact accepted hashes privately. Write no request. Run no Pawhouse command. A job on Nishant's Mac builds the request, publishes, verifies the reader and writes the status that Hermes's `main` profile sends.

Bookmarks live only in private Karakeep. Do not create a bookmark inbox or mirror bookmarks to Obsidian or the website.

After a successful collection with no publishable news, stage only `review.md` and `READY.json` with `"files": {}` and `"noNews": true`. Stage no `files/` folder and no `telegram.txt`. A collection failure stages nothing and writes no `READY.json`. End that run with an error. Do not report a collection error as no news.

For `telegram.txt`, use `https://daily.nishantkhurana.me/editions/D/` exactly once. Choose one real quote/snippet from a note under `/vault-mirror/public/`, preferring `notes/` and `readings/`, which replaced the old wisdom library. Copy its words exactly. Do not fetch the website for it. Lightly connect it to the day's signal, and include the digest link. Keep it to 2 to 5 short lines and under 1,000 characters. No changelog, build details, verification notes, or fabricated quotes.

Your final answer goes to the local job log, not to Telegram. Return one short line: staged, already staged, no news, or the collection error. Never send Telegram, run a delivery command or write a status file.
