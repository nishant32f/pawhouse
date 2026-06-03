---
title: "Code Factory"
tags: ["summary", "ai-agents", "software-engineering"]
description: "Ryan Carson's pattern for setting up a repo so coding agents can write, review, and validate code through deterministic gates."
---

# Code Factory

Source: <https://x.com/ryancarson/status/2023452909883609111>
Summarized: 2026-06-03 10:03 IST
Tool: bird source extraction; steipete/summarize CLI invoked for URL extraction

## Brief

- Ryan Carson's "Code Factory" pattern is a repo control plane for agent-written code: the coding agent writes code, the repo enforces risk-aware checks, a review agent validates the PR, evidence is machine-verifiable, and findings become repeatable harness cases.
- The core move is one machine-readable contract for risk tiers, required checks, docs drift rules, and evidence requirements. This prevents silent drift between scripts, workflows, and policy docs.
- The practical failure mode is stale evidence. Review state is only valid when it matches the current PR head SHA; old clean comments or approvals cannot be allowed to pass a newer commit.
- The durable loop is: policy gate first, expensive CI second, review-agent validation on current head, remediation in-branch when findings are actionable, browser evidence for UI flows, and production regressions converted into harness cases.

## Full Summary

Ryan Carson describes a "Code Factory" setup: a repository designed so agents can implement code, have that code reviewed, and merge only when deterministic, auditable standards are satisfied.

The desired loop:

1. The coding agent writes code.
2. The repo enforces risk-aware checks before merge.
3. A code review agent validates the PR.
4. Evidence from tests, browser runs, and review is machine-verifiable.
5. Findings turn into repeatable harness cases.

The review agent can be Greptile, CodeRabbit, CodeQL plus policy logic, a custom LLM reviewer, or something else. The important part is the control-plane semantics, not the vendor.

## Operating pattern

### 1. Keep one machine-readable contract

Define risk tiers by path, required checks by tier, docs drift rules for control-plane changes, and evidence requirements for UI or critical flows. This removes ambiguity and prevents silent drift between policy docs, scripts, and CI workflow files.

### 2. Gate preflight before expensive CI

Run `risk-policy-gate` first. Verify deterministic policy and review-agent state before starting `test/build/security` fanout jobs. This avoids burning CI minutes on PR heads already blocked by policy or unresolved review findings.

### 3. Enforce current-head SHA discipline

This is Carson's biggest practical lesson. Treat review state as valid only when it matches the current PR head commit:

- wait for the review check run on `headSha`
- ignore stale summary comments tied to older SHAs
- fail if the latest review run is non-success or times out
- require reruns after each push/synchronize
- clear stale gate failures by rerunning the policy gate on the same head

If this is skipped, a PR can merge using stale "clean" evidence.

### 4. Use a single rerun-comment writer

When multiple workflows can request review reruns, duplicate bot comments and races appear. Use one canonical rerun requester and dedupe by marker plus `sha:<head>`.

### 5. Add remediation carefully

If review findings are actionable, a remediation agent can read review context, patch code, run focused validation, and push a fix commit to the same PR branch. The normal PR synchronize event should then trigger the rerun path. Guardrails still matter: pin the model and effort, skip stale comments, and never bypass policy gates.

### 6. Auto-resolve bot-only threads only after clean rerun

After clean current-head evidence, unresolved threads where every comment came from the review bot can be auto-resolved. Human-participated threads should not be auto-resolved. Then rerun the policy gate so conversation-resolution state reflects the cleanup.

### 7. Treat browser evidence as first-class proof

For UI or user-flow changes, require evidence manifests and CI assertions, not just screenshots in PR text. The checks should verify that required flows exist, the expected entrypoint was used, expected account identity is present for logged-in flows, and artifacts are fresh and valid.

### 8. Preserve incident memory with a harness-gap loop

Production regressions should create harness-gap issues, which become added cases and tracked SLAs. The point is to turn fixes into compounding coverage instead of one-off patches.

## Final pattern to copy

1. Put risk and merge policy into one contract.
2. Enforce preflight gate before expensive CI.
3. Require clean code-review-agent state for the current head SHA.
4. If findings exist, remediate in-branch and rerun deterministically.
5. Auto-resolve only bot-only stale threads after clean rerun.
6. Require browser evidence for UI/flow changes.
7. Convert incidents into harness cases and track loop SLOs.

