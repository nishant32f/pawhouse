---
title: "X-AI-2026-10-15"
date: 2026-10-15
tags: [AI, digest, x]
type: daily-digest
source: bird-cli-json
digest_format: editorial-v2
---

## Anthropic says it migrated its monorepo from Git
<!-- story-id: anthropic-monorepo -->

Anthropic said on October 13 that it built an in-house version control system and fully migrated its monorepo from Git in five months. Its reported daily merge volume increased over that period.

The company reports around 2,500 merged code changes per day in May and more than 30,000 per day in September. It says developer infrastructure built for human rather than agent scale became a bottleneck. The announcement links to an engineering account of the migration. The post does not establish that another team's bottleneck is Git.

Source: [Anthropic's migration announcement](https://x.com/AnthropicAI/status/2110047081414987957).

## Hang Huang announces invite-only cloud computers for agents
<!-- story-id: cloud-computers -->

Hang Huang announced an invite-only beta on October 14 for cloud computers for AI agents. He claims a machine with 4 vCPU and 8 GB RAM starts in under one second.

The announcement lists built-in computer use, snapshots for cloning, persistent files, packages and configuration, and public URLs for local ports. Interested users are asked to comment or send a direct message for access. The post does not describe credential isolation or network controls. Neither can be assumed from the feature list.

Source: [Hang Huang's beta announcement](https://x.com/hanghuang_/status/2110349488200057326). Vendor claim.

## Gloss requires supplied text for X posts
<!-- story-id: gloss-x-import -->

Hassan's October 14 launch post describes Gloss as a free, open-source reader for articles, PDFs and X bookmarks. The official README and MCP implementation describe limits on importing X content.

The README says social posts and videos are turned away with a pointer to Paste text. The MCP instructions tell agents to send an article's own link through `save_articles`, not the social post linking to it. For X Articles, long posts, threads, video transcripts and pages behind a login, the agent must read the material itself. It then sends the full Markdown through `save_text`. The tool description asks for the text word for word, not a summary. That documents an agent-assisted text handoff, not direct X bookmark import.

Sources: [Hassan's launch post](https://x.com/nutlope/status/2110385721391366263), [official README](https://raw.githubusercontent.com/Nutlope/gloss/main/README.md), [MCP implementation](https://raw.githubusercontent.com/Nutlope/gloss/main/lib/mcp.ts).

## tanelog reports output-shape limits in Claude Code hooks
<!-- story-id: claude-code-hooks -->

tanelog reported on October 15 that a top-level `updatedInput` in a Claude Code `PreToolUse` hook was ignored without an error. Missing required keys caused calls to be rejected in the tested cases.

The developer compared nine output shapes in versions 2.1.296, 2.1.299 and 2.1.300. They reported that the same shapes worked or failed across all three versions. Testing covered only Bash and Read in `-p` non-interactive mode. They said 2.1.296 and 2.1.300 differed only by one sentence at the end of the rejection message.

Sources: [tanelog's version comparison](https://x.com/tane_log/status/2110594237389750419), [top-level updatedInput report](https://x.com/tane_log/status/2110594197313233276). Community tests.

## Navigation

- Previous: [[digests/x-ai-2026-10-14|X-AI-2026-10-14]]
- Next: None

## Backlinks

- [[index|Mindscape]]
- [[digests/x-ai-2026|X-AI 2026]]
- [[digests/x-ai-2026-10|X-AI-2026-10]]
- [[wisdom/personal-growth/self-worth-and-identity/the-inner-citadel|The Inner Citadel]]
