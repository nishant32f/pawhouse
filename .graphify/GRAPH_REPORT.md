# Graph Report - .  (2026-06-16)

## Corpus Check
- Large corpus: 473 files · ~287,314 words. Semantic extraction will be expensive (many Claude tokens). Consider running on a subfolder, or use --no-semantic to run AST-only.

## Summary
- 404 nodes · 756 edges · 14 communities detected
- Extraction: 100% EXTRACTED · 0% INFERRED · 0% AMBIGUOUS
- Token cost: 0 input · 0 output


## Input Scope
- Requested: auto
- Resolved: committed (source: default-auto)
- Included files: 473 · Candidates: 509
- Excluded: 0 untracked · 18711 ignored · 0 sensitive · 0 missing committed
- Recommendation: Use --scope all or graphify.yaml inputs.corpus for a knowledge-base folder.

## Graph Freshness
- Built from Git commit: `6c037c5`
- Compare this hash to `git rev-parse HEAD` before trusting freshness-sensitive graph output.
## God Nodes (most connected - your core abstractions)
1. `FileTrieNode` - 16 edges
2. `DiagramPanZoom` - 15 edges
3. `endsWith()` - 10 edges
4. `transformInternalLink()` - 9 edges
5. `transformLink()` - 8 edges
6. `parseMarkdown()` - 7 edges
7. `joinSegments()` - 7 edges
8. `slugifyFilePath()` - 6 edges
9. `resolveRelative()` - 6 edges
10. `stripSlashes()` - 6 edges

## Surprising Connections (you probably didn't know these)
- None detected - all connections are within the same source files.

## Communities

### Community 0 - "Community 0"
Cohesion: 0.05
Nodes (2): renderPage(), renderTranscludes()

### Community 2 - "Community 2"
Cohesion: 0.08
Nodes (11): clamp(), createFileParser(), createHtmlProcessor(), createMarkdownParser(), createMdProcessor(), parseMarkdown(), transpileWorkerScript(), buildQuartz() (+3 more)

### Community 3 - "Community 3"
Cohesion: 0.11
Nodes (23): _addRelativeToStart(), containsForbiddenCharacters(), endsWith(), getFileExtension(), _hasFileExtension(), isFilePath(), isFolderPath(), isFullSlug() (+15 more)

### Community 5 - "Community 5"
Cohesion: 0.12
Nodes (13): emit(), generateRSSFeed(), generateSiteMap(), createFileNode(), createFolderNode(), setFolderState(), setupExplorer(), toggleFolder() (+5 more)

### Community 6 - "Community 6"
Cohesion: 0.16
Nodes (2): DiagramPanZoom, hideMermaid()

### Community 7 - "Community 7"
Cohesion: 0.17
Nodes (10): addToVisited(), cleanupGlobalGraphs(), cleanupLocalGraphs(), getVisited(), handleThemeChange(), hideGlobalGraph(), renderGlobalGraph(), renderGraph() (+2 more)

### Community 8 - "Community 8"
Cohesion: 0.15
Nodes (8): Date(), formatDate(), emit(), generateSocialImage(), partialEmit(), processOgImage(), getIconCode(), toCodePoint()

### Community 9 - "Community 9"
Cohesion: 0.17
Nodes (1): FileTrieNode

### Community 10 - "Community 10"
Cohesion: 0.21
Nodes (5): formatFontSpecification(), getFontSpecificationName(), googleFontHref(), googleFontSubsetHref(), joinStyles()

### Community 11 - "Community 11"
Cohesion: 0.25
Nodes (6): getOpts(), isElement(), isLocalUrl(), _navigate(), notifyNav(), startLoading()

### Community 13 - "Community 13"
Cohesion: 0.48
Nodes (5): handleCreate(), handleRestore(), handleSync(), handleUpdate(), resolveContentPath()

### Community 15 - "Community 15"
Cohesion: 0.83
Nodes (3): changeTheme(), getThemeName(), getThemeUrl()

### Community 16 - "Community 16"
Cohesion: 0.83
Nodes (3): emitThemeChangeEvent(), switchTheme(), themeChange()

### Community 18 - "Community 18"
Cohesion: 1
Nodes (2): emitReaderModeChangeEvent(), switchReaderMode()

## Knowledge Gaps
- **Thin community `Community 0`** (2 nodes): `renderPage()`, `renderTranscludes()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 6`** (2 nodes): `DiagramPanZoom`, `hideMermaid()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 9`** (1 nodes): `FileTrieNode`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.
- **Thin community `Community 18`** (2 nodes): `emitReaderModeChangeEvent()`, `switchReaderMode()`
  Too small to be a meaningful cluster - may be noise or needs more connections extracted.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `FileTrieNode` connect `Community 9` to `Community 3`?**
  _High betweenness centrality (0.065) - this node is a cross-community bridge._
- **Should `Community 0` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 1` be split into smaller, more focused modules?**
  _Cohesion score 0.05 - nodes in this community are weakly interconnected._
- **Should `Community 2` be split into smaller, more focused modules?**
  _Cohesion score 0.08 - nodes in this community are weakly interconnected._
- **Should `Community 3` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._
- **Should `Community 4` be split into smaller, more focused modules?**
  _Cohesion score 0.11 - nodes in this community are weakly interconnected._
- **Should `Community 5` be split into smaller, more focused modules?**
  _Cohesion score 0.12 - nodes in this community are weakly interconnected._