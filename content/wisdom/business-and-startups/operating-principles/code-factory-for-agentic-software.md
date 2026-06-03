---
title: "Code Factory for Agentic Software"
tags: ["ai-agents", "software-engineering", "operating-principles", "quality"]
description: "Agentic coding only becomes safe when the repository becomes a deterministic control plane for risk, evidence, review, and incident memory."
---

# Code Factory for Agentic Software

Source: Ryan Carson, ["Code Factory"](https://x.com/ryancarson/status/2023452909883609111)
Summary: [[Code Factory]]

Agentic coding scales only when the repository stops depending on human vibes and starts enforcing a deterministic contract.

The useful pattern is not "let the agent write 100% of the code." The useful pattern is: let agents write code inside a system where risk, evidence, review, and regression memory are machine-checkable.

## The loop

A working code factory has one loop:

1. A coding agent writes code.
2. The repo enforces risk-aware checks before merge.
3. A review agent validates the PR.
4. Evidence from tests, browser flows, and review is machine-verifiable.
5. Findings become repeatable harness cases.

The specific tools matter less than the control plane. Greptile, CodeRabbit, CodeQL, custom LLM review, or another reviewer can fit the pattern if they obey the same semantics.

## The contract

Keep one machine-readable policy contract for:

- risk tiers by path
- required checks by tier
- docs drift rules for control-plane changes
- evidence requirements for UI and critical flows

The contract prevents silent drift between CI files, scripts, and policy docs. If the rules live in many informal places, agents will eventually optimize around the wrong version of reality.

## Current-head evidence is non-negotiable

The subtle failure mode is stale evidence.

A review, approval, screenshot, or clean summary is only valid when it matches the current PR head SHA. After every push, the system must treat old evidence as expired.

Practical rules:

- wait for the review check run on the current `headSha`
- ignore stale comments from older SHAs
- fail if the latest review run is non-success or times out
- require reruns after each synchronize/push
- rerun the policy gate on the same head to clear stale failures

Without this, an agentic repo can merge a new commit using an old "clean" signal. That is worse than no automation because it creates false confidence.

## Browser evidence should be proof, not decoration

For UI or user-flow changes, screenshots in PR text are weak evidence. The repo should require evidence manifests and CI assertions:

- required flows exist
- the expected entrypoint was used
- the expected account identity is present for logged-in flows
- artifacts are fresh and valid

The principle: if a human would ask "did this actually work in the browser?", the repo should be able to answer with a check, not a promise.

## Incident memory compounds quality

Production regression should not end at a patch. It should create a harness-gap issue, become a test case, and be tracked until the loop is closed.

`production regression -> harness gap issue -> case added -> SLA tracked`

This is how an agentic codebase gets safer over time instead of merely faster.

## Practical rule

Use agents for speed, but make the repository responsible for truth.

The code factory is not an autonomy fantasy. It is a quality system: policy first, current-head evidence, deterministic reruns, careful remediation, bot-only cleanup after clean proof, browser evidence for user flows, and incident memory that turns every miss into a stronger harness.

## Related Concepts

- [[Startup Operating Principles]] - operating systems beat informal heroics as work scales.
- [[Executive Responsibilities]] - "hold the line" becomes more important when implementation is delegated to agents.
- [[The Eliza Effect]] - useful reminder not to mistake fluent agent output for verified understanding.
