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

Identity does not change the shipped editorial targets. Keep concrete headlines, concise evidence, attributed claims, uncertainty, numbers, dates, and source support. Keep the separate mandatory unslop edit and private source comparison.

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
