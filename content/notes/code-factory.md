---
title: "Agent-written code merges only through deterministic gates"
date: "2026-11-13"
tags: ["ai-agents", "software-engineering", "code-review", "ci", "verification"]
author: "Ryan Carson"
description: "Ryan Carson's setup for a repo where agents write and review code and merge depends on auditable, current-commit checks."
source: "https://x.com/ryancarson/status/2023452909883609111"
derived_from:
  - "summaries/2026-06-03-code-factory.md"
---

# Agent-written code merges only through deterministic gates

Ryan Carson's "Code Factory" is a repository set up so agents implement code, have it reviewed, and merge only when deterministic, auditable standards are met.

The coding agent writes code, the repo enforces risk-aware checks before merge, a review agent validates the PR, evidence from tests, browser runs and review is machine-verifiable, and findings become repeatable harness cases. The review agent can be Greptile, CodeRabbit, CodeQL plus policy logic or a custom LLM reviewer. Any of them works if the control-plane semantics hold.

## Pattern

1. **One machine-readable contract.** It holds risk tiers by path, required checks by tier, docs drift rules for control-plane changes and evidence requirements for UI or critical flows, so policy docs, scripts and CI files cannot drift apart.
2. **Preflight before expensive CI.** Run `risk-policy-gate` first, checking policy and review-agent state before test, build and security jobs, so no CI minutes go to a blocked head.
3. **Current-head SHA discipline.** Carson's main lesson. Review state counts only if it matches the current PR head commit. Wait for the review check on `headSha`, ignore stale summary comments for older SHAs, fail if the latest review run fails or times out, rerun after each push, and clear stale gate failures by rerunning on the same head. Otherwise a PR can merge on stale clean evidence.
4. **One rerun-comment writer.** Several workflows requesting reruns cause duplicate bot comments and races. Use one requester, deduped by marker plus `sha:<head>`.
5. **Careful remediation.** A remediation agent reads review context, patches, runs focused validation and pushes to the same branch, which triggers the normal rerun. Pin model and effort, skip stale comments, never bypass policy gates.
6. **Auto-resolve bot-only threads after a clean rerun.** Threads with any human comment stay open. Rerun the policy gate afterward to refresh conversation-resolution state.
7. **Browser evidence as proof.** For UI changes, require evidence manifests and CI assertions. Screenshots in PR text do not count. Check that required flows exist, the expected entrypoint was used, the right account identity is present for logged-in flows, and artifacts are fresh and valid.
8. **Harness-gap loop.** Production regressions create harness-gap issues, which become added cases with tracked SLAs.

## Related

- [[software-factories|A software factory is defined by who takes the call when production breaks]]. Chamath's accountability tests, where this note supplies the repo mechanics.
- [[ambition-with-ai-models|Use AI models to raise speed, altitude, depth and range]]. Its acceptance test that can fail independently is what these gates provide.
- [[startup-operating-principles|Startup operating principles]]. Product accountability and speed with accuracy.

Map: [[map-startups-and-ai|Startups, leadership and AI]]
