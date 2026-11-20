# Graph Report - .  (2026-11-20)

## Corpus Check
- Large corpus: 549 files · ~325,576 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 983 nodes · 1846 edges · 51 communities detected
- Extraction: 98% EXTRACTED · 2% INFERRED · 0% AMBIGUOUS · INFERRED: 39 edges (avg confidence: 0.5)
- Token cost: 0 input · 0 output


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 549 · Candidates: 612
- Excluded: 0 untracked · 0 ignored · 0 sensitive · 0 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `229608b`
- Compare this hash to `git rev-parse HEAD` before trusting freshness-sensitive graph output.
## God Nodes (most connected - your core abstractions)
1. `Publisher` - 39 edges
2. `ReleaseContractTest` - 37 edges
3. `R2Publisher` - 25 edges
4. `ReleaseTest` - 24 edges
5. `LifecycleTest` - 22 edges
6. `PlutoReleaseTest` - 20 edges
7. `PublishingTest` - 18 edges
8. `RedirectTest` - 16 edges
9. `StoryIdentityTest` - 16 edges
10. `FileTrieNode` - 16 edges

## Surprising Connections (you probably didn't know these)
- `Code releases and accepted content have independent identities and failure gates` --uses--> `Publisher`  [INFERRED]
  hermes/ai-x-digest/tests/test_daily_release.py → scripts/publication.py
- `Private credentials, pinned SSR builds, actual deployment versions and no delive` --uses--> `Publisher`  [INFERRED]
  hermes/ai-x-digest/tests/test_pluto_release.py → scripts/publication.py
- `HistoryTest` --uses--> `Publisher`  [INFERRED]
  hermes/ai-x-digest/tests/test_daily_history.py → scripts/publication.py
- `InventoryStagingTest` --uses--> `Publisher`  [INFERRED]
  hermes/ai-x-digest/tests/test_daily_history.py → scripts/publication.py
- `InventoryVaultAliasTest` --uses--> `Publisher`  [INFERRED]
  hermes/ai-x-digest/tests/test_daily_history.py → scripts/publication.py

## Communities

### Community 0 - "Community 0"
Cohesion: 0.08
Nodes (9): R2Publisher, Private accepted-source publication. The explicit backend switch owns activation, U4 reads this under owner.locked(), then persists real reader proof to receipt_p, HistoryCliTest, HistoryTest, InventoryStagingTest, InventoryVaultAliasTest, CliPublicationTest (+1 more)

### Community 1 - "Community 1"
Cohesion: 0.09
Nodes (21): backfill(), exact_copy(), feed_identities(), inventory(), main(), Caller holds owner.locked(); publish only the pinned, byte-checked inventory., Caller owns the publication lock. Validate all collisions before copying or dele, relocate() (+13 more)

### Community 3 - "Community 3"
Cohesion: 0.1
Nodes (2): Negative HTTP proofs preserve full prose, figures, discovery, RSS and real 404s., ReleaseContractTest

### Community 4 - "Community 4"
Cohesion: 0.14
Nodes (27): HTMLParser, build(), check_edition(), check_prose(), check_story(), check_visual(), cloudflare_deployments(), code_artifact() (+19 more)

### Community 5 - "Community 5"
Cohesion: 0.08
Nodes (21): addToVisited(), cleanupGlobalGraphs(), cleanupLocalGraphs(), getVisited(), handleThemeChange(), hideGlobalGraph(), renderGlobalGraph(), renderGraph() (+13 more)

### Community 9 - "Community 9"
Cohesion: 0.21
Nodes (19): HTTPRedirectHandler, RuntimeError, API, APIError, apply(), encoded_path(), entrypoint(), http_get() (+11 more)

### Community 10 - "Community 10"
Cohesion: 0.08
Nodes (2): Code releases and accepted content have independent identities and failure gates, ReleaseTest

### Community 11 - "Community 11"
Cohesion: 0.16
Nodes (2): LifecycleTest, R2PublicationTest

### Community 12 - "Community 12"
Cohesion: 0.15
Nodes (15): fail(), headingName(), isComment(), isMarker(), isObject(), knowledgeLink(), parseDate(), parseEdition() (+7 more)

### Community 13 - "Community 13"
Cohesion: 0.13
Nodes (2): renderPage(), renderTranscludes()

### Community 14 - "Community 14"
Cohesion: 0.17
Nodes (23): _addRelativeToStart(), containsForbiddenCharacters(), endsWith(), getFileExtension(), _hasFileExtension(), isFilePath(), isFolderPath(), isFullSlug() (+15 more)

### Community 15 - "Community 15"
Cohesion: 0.2
Nodes (2): PlutoReleaseTest, Private credentials, pinned SSR builds, actual deployment versions and no delive

### Community 16 - "Community 16"
Cohesion: 0.25
Nodes (1): PublishingTest

### Community 17 - "Community 17"
Cohesion: 0.13
Nodes (2): buildQuartz(), startWatching()

### Community 18 - "Community 18"
Cohesion: 0.25
Nodes (4): edition(), fixture(), story(), StoryIdentityTest

### Community 19 - "Community 19"
Cohesion: 0.16
Nodes (2): DiagramPanZoom, hideMermaid()

### Community 20 - "Community 20"
Cohesion: 0.33
Nodes (2): RedirectTest, server()

### Community 21 - "Community 21"
Cohesion: 0.18
Nodes (2): Date(), formatDate()

### Community 22 - "Community 22"
Cohesion: 0.16
Nodes (8): decodeHead(), decodeManifest(), decodeObjectRef(), available(), json(), PublicationUnavailable, referenced(), selectPublication()

### Community 23 - "Community 23"
Cohesion: 0.33
Nodes (2): edition(), EditorialFormatTest

### Community 24 - "Community 24"
Cohesion: 0.17
Nodes (1): FileTrieNode

### Community 26 - "Community 26"
Cohesion: 0.17
Nodes (6): emit(), generateSocialImage(), partialEmit(), processOgImage(), getIconCode(), toCodePoint()

### Community 27 - "Community 27"
Cohesion: 0.2
Nodes (10): Edition, IdentityError, parse_edition(), Parse editorial-v2 identity and compare accepted Markdown revisions.  This modul, Keep every published v2 ID and preserve prose when archiving a story., Return unchanged legacy text, or ordered identified v2 story records.      Raise, Story, _structure() (+2 more)

### Community 28 - "Community 28"
Cohesion: 0.27
Nodes (9): hash(), inspect(), operateBundle(), parse(), predecessor(), publishBundle(), S3Store, verify() (+1 more)

### Community 29 - "Community 29"
Cohesion: 0.22
Nodes (5): anchors(), decodeEdition(), editorial(), sources(), story()

### Community 30 - "Community 30"
Cohesion: 0.21
Nodes (8): clamp(), createFileParser(), createHtmlProcessor(), createMarkdownParser(), createMdProcessor(), parseMarkdown(), transpileWorkerScript(), QuartzLogger

### Community 31 - "Community 31"
Cohesion: 0.2
Nodes (4): compileEdition(), compileRepository(), jsonBytes(), toWire()

### Community 32 - "Community 32"
Cohesion: 0.27
Nodes (5): Fixture, Accepted fixture bytes served by the actual SSR build, then copied for negative, run(), setUpClass(), start_runtime()

### Community 33 - "Community 33"
Cohesion: 0.2
Nodes (2): CompatibilityTest, V2PublishingTest

### Community 34 - "Community 34"
Cohesion: 0.44
Nodes (8): dimension(), fields(), imageUrl(), isObject(), object(), parseStoryMetadata(), text(), visual()

### Community 35 - "Community 35"
Cohesion: 0.33
Nodes (7): decodeNode(), decodeProse(), fields(), normalizeProse(), object(), safeUrl(), string()

### Community 36 - "Community 36"
Cohesion: 0.31
Nodes (4): decodeCatalog(), decodeRoutes(), decodeSearch(), envelope()

### Community 38 - "Community 38"
Cohesion: 0.53
Nodes (1): ArchiveSourcesTest

### Community 39 - "Community 39"
Cohesion: 0.44
Nodes (1): NewDayPublishingTest

### Community 40 - "Community 40"
Cohesion: 0.33
Nodes (2): fetchPath(), provenance()

### Community 41 - "Community 41"
Cohesion: 0.48
Nodes (5): handleCreate(), handleRestore(), handleSync(), handleUpdate(), resolveContentPath()

### Community 42 - "Community 42"
Cohesion: 0.48
Nodes (5): createFileNode(), createFolderNode(), setFolderState(), setupExplorer(), toggleFolder()

### Community 43 - "Community 43"
Cohesion: 0.43
Nodes (5): formatFontSpecification(), getFontSpecificationName(), googleFontHref(), googleFontSubsetHref(), joinStyles()

### Community 45 - "Community 45"
Cohesion: 0.67
Nodes (5): check_editorial(), display_stem(), has_source_link(), main(), without_hidden_blocks()

### Community 46 - "Community 46"
Cohesion: 0.33
Nodes (1): EditorialEdgeTest

### Community 47 - "Community 47"
Cohesion: 0.4
Nodes (1): InstallRecoveryTest

### Community 48 - "Community 48"
Cohesion: 0.4
Nodes (1): ProducerContractTest

### Community 49 - "Community 49"
Cohesion: 0.83
Nodes (3): emit(), generateRSSFeed(), generateSiteMap()

### Community 51 - "Community 51"
Cohesion: 0.83
Nodes (3): changeTheme(), getThemeName(), getThemeUrl()

### Community 52 - "Community 52"
Cohesion: 0.83
Nodes (3): emitThemeChangeEvent(), switchTheme(), themeChange()

### Community 54 - "Community 54"
Cohesion: 0.67
Nodes (1): PerfTimer

### Community 55 - "Community 55"
Cohesion: 0.67
Nodes (1): EditorialMetadataContractTest

### Community 56 - "Community 56"
Cohesion: 0.67
Nodes (1): QuartzRetirementTest

### Community 57 - "Community 57"
Cohesion: 0.67
Nodes (1): SourceAdjacencyTest

### Community 60 - "Community 60"
Cohesion: 1
Nodes (2): emitReaderModeChangeEvent(), switchReaderMode()

### Community 63 - "Community 63"
Cohesion: 1
Nodes (2): credentials_at(), main()

## Knowledge Gaps
- **9 isolated node(s):** `Story`, `Parse editorial-v2 identity and compare accepted Markdown revisions.  This modul`, `Return unchanged legacy text, or ordered identified v2 story records.      Raise`, `Keep every published v2 ID and preserve prose when archiving a story.`, `Accepted fixture bytes served by the actual SSR build, then copied for negative` (+4 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **Thin community `Community 3`** (2 nodes): `Negative HTTP proofs preserve full prose, figures, discovery, RSS and real 404s.`, `ReleaseContractTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 10`** (2 nodes): `Code releases and accepted content have independent identities and failure gates`, `ReleaseTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 11`** (2 nodes): `LifecycleTest`, `R2PublicationTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 13`** (2 nodes): `renderPage()`, `renderTranscludes()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 15`** (2 nodes): `PlutoReleaseTest`, `Private credentials, pinned SSR builds, actual deployment versions and no delive`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 16`** (1 nodes): `PublishingTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 17`** (2 nodes): `buildQuartz()`, `startWatching()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 19`** (2 nodes): `DiagramPanZoom`, `hideMermaid()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 20`** (2 nodes): `RedirectTest`, `server()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 21`** (2 nodes): `Date()`, `formatDate()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 23`** (2 nodes): `edition()`, `EditorialFormatTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 24`** (1 nodes): `FileTrieNode`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 33`** (2 nodes): `CompatibilityTest`, `V2PublishingTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 38`** (1 nodes): `ArchiveSourcesTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 39`** (1 nodes): `NewDayPublishingTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 40`** (2 nodes): `fetchPath()`, `provenance()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 46`** (1 nodes): `EditorialEdgeTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 47`** (1 nodes): `InstallRecoveryTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 48`** (1 nodes): `ProducerContractTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 54`** (1 nodes): `PerfTimer`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 55`** (1 nodes): `EditorialMetadataContractTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 56`** (1 nodes): `QuartzRetirementTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 57`** (1 nodes): `SourceAdjacencyTest`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 60`** (2 nodes): `emitReaderModeChangeEvent()`, `switchReaderMode()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 63`** (2 nodes): `credentials_at()`, `main()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Publisher` connect `Community 1` to `Community 0`, `Community 10`, `Community 15`, `Community 11`, `Community 9`, `Community 4`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `FileTrieNode` connect `Community 24` to `Community 7`?**
  _High betweenness centrality (0.011) - this node is a cross-community bridge._
- **Why does `ReleaseTest` connect `Community 10` to `Community 1`?**
  _High betweenness centrality (0.010) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Publisher` (e.g. with `HistoryTest` and `InventoryStagingTest`) actually correct?**
  _`Publisher` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 10 inferred relationships involving `R2Publisher` (e.g. with `HistoryTest` and `InventoryStagingTest`) actually correct?**
  _`R2Publisher` has 10 INFERRED edges - model-reasoned connections that need verification._
- **Are the 2 inferred relationships involving `LifecycleTest` (e.g. with `Publisher` and `R2Publisher`) actually correct?**
  _`LifecycleTest` has 2 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Story`, `Parse editorial-v2 identity and compare accepted Markdown revisions.  This modul`, `Return unchanged legacy text, or ordered identified v2 story records.      Raise` to the rest of the system?**
  _9 weakly-connected nodes found - possible documentation gaps or missing edges._