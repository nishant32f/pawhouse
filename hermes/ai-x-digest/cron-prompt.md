Daily task: generate Nishant's X-AI digest, run the required unslop editing pass, publish the accepted edition, and deliver the existing short Telegram message.

Load `ai-x-digest`, `unslop`, `obsidian`, and `bird`. For new editions, the `ai-x-digest` editorial-v2 contract takes precedence over unversioned historical normalization rules.

Use today's date in Asia/Kolkata. Keep the daily path `/Users/skypawalker/Dropbox/Obsidian/public/digests/x-ai-YYYY-MM-DD.md` and the existing monthly/year indexes.

Select one lead and normally 2 to 4 distinct supporting stories. Publish fewer on quiet days. Briefs are optional. A successful collection with no publishable news creates only a private no-news record; a collection failure is an error. Do not pad with recurring themes or old saved posts.

Write a complete first draft privately, then load and apply `unslop`. Save a separate edited edition and a private review with concrete edits and the sources actually inspected. Preserve facts, numbers, attribution, uncertainty, exact quotes, and URLs. Correct unsupported claims from their sources. No signal-quality preamble, duplicate H1, forced takeaways, or source appendix. Each story has a concrete headline, concise opening summary, and nearby sources.

Assign persistent story IDs before drafting and retain them across edits, reorders, and retries. Archive removed stories with their IDs, a correction, and original prose and sources. Never infer stories from old legacy content.

Use `digest_format: editorial-v2`. Validate private staging with `/Users/skypawalker/.hermes/skills/note-taking/obsidian/scripts/verify-x-ai-digest-format.py`. Accept the edited candidate only after comparing its facts and wording with the draft and inspected sources. Record exact accepted hashes privately. Inspect changes before publishing. Do not include private sources, drafts, reviews, or unrelated changes in the website. Stage all accepted files outside the public vault and repository. Use `./scripts/publish-from-vault.sh --digest PRIVATE_REQUEST.json` from Pawhouse, following the request schema in `apps/daily/README.md`. Do not copy into public folders or use broad `npm run publish`. Reuse the same accepted request on retry. Check the reader receipt, GitHub Pages run, and actual live prose. Keep one authored Markdown per day and one RSS item per actual edition.

Bookmarks live only in private Karakeep. Do not create a bookmark inbox or mirror bookmarks to Obsidian or the website.

After a successful no-news collection, return only a short no-news message without a digest URL or a fabricated quote. Do not report a collection error as no news.

For the normal scheduled delivery after a verified publication, use `https://nishantkhurana.me/digests/x-ai-YYYY-MM-DD`. Choose one real quote/snippet from public wisdom, lightly connect it to the day's signal, and include the digest link. Keep it to 2 to 5 short lines. No changelog, build details, verification notes, or fabricated quotes. Do not send a success message if publication failed.

Before returning dated success text, use the shared receipt's `delivery-begin`. Scheduled Hermes auto-delivery happens after the agent returns. Generated text cannot establish delivery or mark a receipt complete. Keep ambiguous outcomes pending for operator resolution with actual delivery evidence. Do not send Telegram directly or regenerate a candidate to retry delivery. A complete receipt suppresses a duplicate dated message. Preserve the existing Quartz URL until the authorized domain cutover.
