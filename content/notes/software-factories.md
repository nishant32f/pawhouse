---
title: "A software factory is defined by who takes the call when production breaks"
date: "2026-11-13"
tags: ["startups", "software", "ai", "operations", "accountability"]
author: "Chamath"
description: "Chamath defines a software factory as an accountable production system, and gives five tests that separate it from an AI coding tool."
derived_from:
  - "wisdom/business-and-startups/operating-principles/software-factories.md"
---

# A software factory is defined by who takes the call when production breaks

By Chamath, from "What Is a Software Factory?"

A software factory turns business intent into working software, keeps it coherent under change, and stands behind the output when production breaks. Coding agents hand verification to the customer. Dashboards supervise agents. Benchmarks measure set tasks rather than whether a system stays coherent after years of mixed human and agent changes. AI sharply lowers the cost of producing software, so value moves to whoever guarantees the output. Most AI tooling firms borrow the phrase for its industrial credibility but sell tools.

## History

- Hitachi opened "Software Works" in 1969 with statistical quality control and standardized production.
- Toshiba, NEC and Fujitsu followed with long-lived systems for banking, rail and power.
- Microsoft architects revived the term in 2004, comparing software to car manufacturing with proven components, repeatable lines and controlled variation.
- The US Air Force's Kessel Run builds, operates and owns mission software.

## Five tests

1. **Business intent in.** The input is requirements, rules, constraints, outcomes and regulatory obligations. A ticket for another engineer makes it a developer tool.
2. **Coherence under change.** Years of many people changing a live system pull requirements, docs, code, tests and behavior apart, and ten times more code against stale specs adds entropy faster. A factory keeps them one governed object. Change the requirement and the code follows. Hotfix the code and the spec updates. A vendor that cannot show this loop closed on a real system sells code generation.
3. **Independent of any person.** The same agent gives different results in different hands. A factory gives predictable speed and quality whoever is on shift and keeps context when people leave.
4. **Traceable output.** Failed physical parts trace to lot, batch, machine and shift. "The model wrote it" is no audit trail. Provenance comes out of production and never from later documentation. It says this rule came from this requirement, approved by this person, implemented in this change, verified by this test, deployed at this time.
5. **Someone is accountable.** Most AI tooling contracts give output as-is and leave verification to the customer. A factory answers for a wrong claim, wrong trade or broken workflow, fixes it and absorbs the cost.

## The one question

Demos, agent counts and benchmark scores do not show whether something is a factory.

> When the system breaks in production, who takes the call?

If the answer is not "we do", it may be useful, but it is a tool.

## Related

- [[code-factory|Agent-written code merges only through deterministic gates]]. The repo-side mechanics for checks and evidence, where this note covers vendor accountability.
- [[ambition-with-ai-models|Use AI models to raise speed, altitude, depth and range]]. Delegating higher-level outcomes needs the same independent verification.
- [[startup-operating-principles|Startup operating principles]]. Product accountability is one of its four anchors.
- [[executive-responsibilities|An executive charts the course, sets the pace and holds the line]]. Holding the line is the human version of owning the output.

Map: [[map-startups-and-ai|Startups, leadership and AI]]
