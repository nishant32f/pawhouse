---
title: "Software Factories"
tags: ["startups", "software", "ai", "enterprise-software", "operations", "accountability"]
description: "Chamath's definition of a software factory: not a coding tool, but an accountable production system that preserves coherence, traceability, and quality under continuous change."
author: "Chamath"
source: "What Is a Software Factory?"
draft: false
---

# Software Factories

> Source: Chamath, “What Is a Software Factory?”

A software factory is not a coding agent, dashboard, benchmark, or productivity tool. It is an accountable production system that starts from business intent, turns that intent into working software, preserves coherence under change, and stands behind the output when production breaks.

## Core argument

AI is collapsing the cost of producing software. When production becomes cheap, value moves to whoever can guarantee the output.

That is why the phrase “software factory” is being grabbed by AI tooling companies. The phrase carries industrial credibility: repeatable production, quality control, traceability, and accountability. But most products using the term are still tools, not factories, because they hand verification and responsibility back to the customer.

Chamath’s standard is blunt: a real factory ships a finished product and takes the call when it fails.

## Historical frame

The idea is older than the current AI wave:

- Hitachi opened “Software Works” in 1969 as a literal software factory using statistical quality control and standardized production processes.
- Toshiba, NEC, and Fujitsu followed, producing long-lived systems for banking, rail, and power infrastructure.
- Microsoft architects revived the term in 2004, comparing software production to car manufacturing: proven components, repeatable lines, controlled variation.
- The US Air Force’s Kessel Run is a modern example: it builds, operates, and owns mission software.

Across these examples, the factory was never merely a better tool. It was a system that accepted inputs, produced finished goods, and stood behind quality.

## The five tests of a software factory

### 1. It starts from business intent

The input should be business language: requirements, rules, constraints, outcomes, and regulatory obligations.

If the input is only an engineering ticket for another engineer, it is a developer tool attached to the old process. A factory should let the customer describe the desired product while the production system figures out the build path.

### 2. It maintains coherence under continuous change

Enterprise software rarely fails because nobody can write new code. It fails because many people change a live system over years while requirements, documentation, code, tests, and production behavior drift apart.

AI code generation can accelerate that drift. Ten times more code against stale specs creates entropy faster, not leverage.

A real software factory keeps intent, specification, code, tests, and runtime behavior synchronized as one governed object:

- change the requirement, and the implementation follows
- hotfix the code, and the requirement/spec updates
- tests stay tied to both business rules and deployed behavior

If a vendor cannot show this loop closed on a real system, they are selling code generation, not a factory.

### 3. It operates independent of any specific person

Tools vary with the operator. The same coding agent in two engineers’ hands will produce different outcomes depending on prompt quality, review discipline, and judgment.

A factory should produce predictable speed and quality regardless of who is on shift. Knowledge must compound inside the system, not only inside individuals. When people join, the system hands them accumulated context. When people leave, the understanding does not walk out with them.

A hero-dependent system is not a factory. It is a liability with a charismatic interface.

### 4. Every unit of output is traceable

In a physical factory, failed parts can be traced to lot, batch, machine, and shift. Regulated software needs the same discipline.

“The model wrote it” is not an audit trail.

A software factory should produce provenance as a byproduct of production:

- this rule came from this requirement
- approved by this person
- implemented in this change
- verified by this test
- deployed at this time

Documentation written after the fact does not count. Traceability has to be embedded in the line.

### 5. Someone is accountable for the finished product

This is the cleanest separation between a factory and a tool.

Most AI tooling contracts say the output is provided as-is and verification is the customer’s problem. That is disqualifying for a factory.

A real factory is on the hook when the system fails: wrong claim, wrong trade, bad validation, broken workflow. Someone specific answers, fixes it, and absorbs the cost.

## What is not a factory

- **Coding agents:** useful tools that produce code but transfer verification and accountability to the customer.
- **Agent orchestration dashboards:** supervision layers for watching agents work.
- **Benchmarks:** measurement harnesses that say whether a tool performs well on benchmarked tasks, not whether an enterprise system remains coherent after years of mixed human-agent change.

## Practical takeaway

Do not evaluate “software factory” claims by demos, agent counts, or benchmark scores. Ask one question:

> When the system breaks in production, who takes the call?

If the answer is not “we do,” it is not a software factory. It may still be useful, but it is a tool with a different obligation.

## Related notes

- [[startup-operating-principles|Startup Operating Principles]]
- [[leadership|Leadership]]
