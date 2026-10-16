# Daily edition identity contract

One public Markdown edition remains the authored source. The reader derives its records and HTML from that edition. It introduces no authored article files or JSON writer checkpoint.

## Format compatibility

| `digest_format` | Identity behavior                                                                                   |
| --------------- | --------------------------------------------------------------------------------------------------- |
| Absent          | Keep the original edition text and actual sources. Do not infer story boundaries or article routes. |
| `editorial-v1`  | Keep the original edition text and actual sources. Do not infer story boundaries or article routes. |
| `editorial-v2`  | Require explicit story identity and the section grammar below.                                      |
| Any other value | Reject before publication or artifact output.                                                       |

A legacy edition remains a whole edition in the reader. Explicit adoption of the latest accepted edition changes only its version and adds reviewed ID comments. Preserve its original source privately. The four-story adoption fixture proves this change without changing the public source file.

## Editorial metadata and design separation

The optional `story_metadata` frontmatter map contains content, keyed by an existing story ID. It works only with `editorial-v2`. Existing editions without it keep their original prose and routes.

Each entry requires a plain-text `section`. It may include a plain-text `deck` and one `visual`. These are editorial facts and descriptions. Fonts, colors, columns, spacing, chart drawing, image treatment and templates belong to the app. The metadata rejects unknown fields, including layout or style instructions. Hermes emits no HTML, SVG, CSS or JavaScript.

```yaml
story_metadata:
  anthropic-monorepo:
    section: Engineering
    deck: Anthropic reports increased daily merges.
    visual:
      kind: bar
      title: Reported code merges per day
      unit: merges per day
      caption: Two figures reported by Anthropic; September exceeds 30,000.
      source_url: https://x.com/AnthropicAI/status/2110047081414987957
      points:
        - label: May
          value: 2500
          qualifier: approximate
        - label: September
          value: 30000
          qualifier: greater-than
  gloss-x-import:
    section: Reading
    visual:
      kind: image
      src: https://pbs.twimg.com/amplify_video_thumb/2110385606014480384/img/Izsh3-4wJEFdJjBI.jpg
      width: 1200
      height: 675
      alt: A saved Magic Ink article card in the Gloss launch demonstration.
      caption: Saved reading in Gloss, from the launch demonstration.
      credit: Hassan
      source_url: https://x.com/nutlope/status/2110385721391366263
```

Both visual variants require a nonempty caption and a `source_url` that matches an actual adjacent source in that same story. An image requires an HTTPS URL without credentials or control characters, positive integer intrinsic width and height, nonempty alt text and credit. Native images do not cause server-side media downloads. An unavailable image leaves the article, alt text, caption and source readable.

A bar chart requires a title, unit and two to four comparable points. Each point requires a label, finite nonnegative numeric value and explicit `exact`, `approximate`, `greater-than` or `at-least` qualifier. At least one value must be positive. Do not infer missing intermediate figures, mix measurement units, or convert an approximate value or bound into an exact measurement.

The examples contain actual 15 October sources. New editions must use their own inspected source media and data, never copy the sample URLs or values as filler. Omit a visual when useful evidence is unavailable. Keep provenance and the source-to-caption/data comparison in the private review. The unslop edit covers decks, labels and captions too.

`src/lib/editorial.ts` validates this data at the reader AST boundary used by publication. Parsed story records expose `editorial: StoryEditorial | null`. The module owns no markup or CSS. Existing `story.html` and `edition.html` remain the accepted Markdown renderings. The view-owned `src/components/visuals.ts` renders escaped figures for the reader and full-text RSS. A design change reuses identical accepted Markdown; a content change reuses the same renderer. No renderer writes back into the vault.

## Active stories

A full story uses an H2 heading. A brief uses an H3 heading inside the exact reserved H2 section `In brief`.

<!-- prettier-ignore -->
```markdown
## A concrete full-story headline
<!-- story-id: stable-story-id -->

Original opening summary.

Original body and adjacent source links.

## In brief

### A concrete brief headline
<!-- story-id: stable-brief-id -->

Original brief and adjacent source links.
```

1. Put each heading and ID comment at column zero. Put the comment on the very next line, without an intervening blank line.
2. Use exactly `<!-- story-id: ID -->`. IDs match `[a-z0-9]+(?:-[a-z0-9]+)*` and are unique across full stories, briefs, and archives in one edition.
3. Assign an ID once. Keep it when a headline changes or the story moves. Never regenerate it from a headline or position.
4. Start the edition with a full story as its lead. Active records retain their Markdown order. Briefs do not replace the lead.
5. Keep the final two H2 sections as `Navigation` then `Backlinks`. Neither section has an ID or creates a story record.

`In brief` and `Archived stories` each occur at most once. They contain H3 records with no introductory prose. An H3 record outside these sections is invalid. Reserved heading spelling and case are exact. An edition needs at least one active full story.

An ID comment elsewhere in visible Markdown is invalid. Headings and marker examples inside fenced code or ordinary HTML comments do not create records. The reader interprets the allowlisted ID comment as metadata. It escapes other raw HTML when rendering.

## Removed stories

Removing a published ID without retaining it in the same edition is invalid. Move a removed full story or brief into the exact reserved `Archived stories` section. It must be the final content section, immediately before `Navigation`. Use an H3 heading for either former role.

<!-- prettier-ignore -->
```markdown
## Archived stories

### The original story headline
<!-- story-id: stable-story-id -->

Correction: Give a concrete, non-empty reason for withdrawing this story.

Retain the original prose here, including its actual source links.
```

The correction is the first paragraph after the marker. Start it with the exact text `Correction: ` and give a non-empty reason. A blank line separates it from the retained body.

The archived body must match the previous accepted body, including sources. The identity comparison ignores only surrounding whitespace and the correction paragraph. It preserves internal whitespace and punctuation. The original full-story or brief role is no longer needed.

Archived records retain their IDs and article routes. Exclude them from current cards and previous/next navigation. Their article pages show both the correction and the original prose. Future revisions must retain these IDs too.

## Editorial and source boundaries

V2 permits one to eight full stories and an optional group of one to six briefs. Normal editions aim for 10 to 14 distinct items; quiet days may be shorter. Soft word targets are 140 to 200 for the lead, 70 to 120 for supporting stories and 25 to 45 for briefs. Hard limits remain 220 and 85. Legacy and v1 rules remain unchanged.

Discovery covers official releases, repositories, builder reports and research. Compare seven accepted editions and label any seven-day catch-up with its actual event date. Keep collection, selection and source evidence private. Keep concrete headlines, concise evidence, attributed claims, uncertainty, numbers, dates, and source support. Keep the separate mandatory unslop edit and private source comparison.

Preserve each story's actual adjacent source links and attribution. A source in another story does not cover a missing citation. The existing editorial checker owns prose targets and source adjacency. The reader adapter owns Markdown rendering and unsafe-link rejection. Identity parsing does not replace either check.

Successful collection with no publishable news creates no edition or dated URL. Collection failure remains an error. Neither outcome is Markdown edition content. A quiet edition with one useful full story is valid.

## Shared helper boundary

`story_identity.py` exposes:

| API                                                        | Result                                                                                                                                              |
| ---------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| `parse_edition(text)`                                      | An immutable `Edition` or `IdentityError`. It validates v2 structure and identity without comparing history.                                        |
| `validate_revision(previous_text, current_text)`           | The parsed current edition or `IdentityError`. It additionally retains every previous v2 ID, rejects a format downgrade, and checks archived prose. |
| `Edition.format`, `original_text`, `stories`               | Version, exact input text, and ordered identified records. Legacy records have an empty stories tuple.                                              |
| `Edition.active_stories`, `archived_stories`, `lead`       | Ordered active records, retained archives, and the first full story or `None`.                                                                      |
| `Story.story_id`, `headline`, `kind`, `body`, `correction` | Identity, heading text, `story`/`brief`/`archived`, body without heading/marker, and an archive correction without its label.                       |

Content parsing alone cannot detect deletion of an old published ID. The U5 verifier and scoped publisher must call revision validation against the accepted previous Markdown before promotion. They must also run editorial and source checks. A legacy-to-v2 migration requires operator review of identity and prose, since legacy input has no story IDs to compare.

The helper does not validate dates, filenames, prose targets, source URLs, delivery state, or publication locks. These belong to the named reader, verifier, and publisher units. The publisher also passes the private previous edition to the reader AST validator. It compares each archived story's resolved citations with its previous record, including reference definitions outside the story. Raw body equality alone cannot preserve those targets.

## Shared fixtures

Fixtures live in `apps/daily/tests/fixtures/` for Python identity tests and the reader adapter.

| Filename                        | Purpose                                                                                       |
| ------------------------------- | --------------------------------------------------------------------------------------------- |
| `editorial-v2-four-stories.md`  | Actual accepted 15 October edition with only the format change and four reviewed ID comments. |
| `editorial-v1.md`               | Exact original 15 October Markdown, including its real sources and vault furniture.           |
| `legacy-unversioned.md`         | Small legacy whole-edition example with original wording and a source link.                   |
| `editorial-v2-brief-archive.md` | One full story, one active brief, and one archived story with a correction.                   |
| `no-news.txt`                   | A private fixture outcome, without authored edition content or a dated URL.                   |
| `collection-error.txt`          | A distinct failed-collection fixture outcome, without an edition or a dated URL.              |

The four reviewed IDs are `anthropic-monorepo`, `cloud-computers`, `gloss-x-import`, and `claude-code-hooks`. Tests remove those comments and restore `editorial-v1` to prove byte-for-byte equality with the accepted original.
