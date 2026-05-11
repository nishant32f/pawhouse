---
title: "Graphify Vault Dashboard"
tags: [graphify, knowledge-graph, obsidian]
type: graph-dashboard
---

# Graphify Vault Dashboard

Graphify is set up for this vault.

## Backlinks

- [[Obsidian Value Map]]
- [[digests/AI X Digest Hub|AI X Digest Hub]]
- [[wisdom/Index|Wisdom Index]]
- [[bookmarks/inbox|Bookmark Inbox]]

## Outputs

- Interactive HTML graph: `.graphify/graph.html`
- Raw graph JSON: `.graphify/graph.json`
- Audit report: `.graphify/GRAPH_REPORT.md`
- SVG graph: `.graphify/graph.svg`
- Obsidian canvas export: `.graphify/obsidian/graph.canvas`
- Obsidian node export: `.graphify/obsidian/`

## Current graph stats

- Files: 193
- Nodes: 1525
- Edges: 2743
- Communities: 93
- Approx corpus words: 115351

## How to query

From terminal:

```bash
graphify summary --graph /Users/skypawalker/Dev/obsidian/.graphify/graph.json
graphify query "how do my wisdom notes connect to startup principles?" --graph /Users/skypawalker/Dev/obsidian/.graphify/graph.json
graphify path "Personal Beliefs & Life Principles" "AI X Digest Hub" --graph /Users/skypawalker/Dev/obsidian/.graphify/graph.json
graphify explain "wisdom/" --graph /Users/skypawalker/Dev/obsidian/.graphify/graph.json
```

## Rebuild

Manual rebuild:

```bash
/Users/skypawalker/.hermes/scripts/graphify-obsidian/rebuild-vault-graph.js /Users/skypawalker/Dev/obsidian /Users/skypawalker/Dev/obsidian/public
```

The graph scans `public/` as the content root while writing runtime outputs to `.graphify/` outside the hosted website tree.

Automation rebuilds the graph after the daily digest job.
