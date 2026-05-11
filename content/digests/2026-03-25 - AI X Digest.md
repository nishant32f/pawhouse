---
title: "AI X Digest — March 25, 2026"
date: 2026-03-25
tags: [AI, digest, x]
type: daily-digest
source: bird-cli-json-and-imported-digests
aliases:
  - "2026-03-25-evening"
  - "2026-03-25-morning"
  - "AI Digest — Mar 25, 2026 Evening"
  - "AI Digest — Mar 26, 2026 Morning"
---

# AI X Digest — March 25, 2026

> Clinical daily digest note. Historical morning/evening imports have been normalized into this single daily artifact.

## Backlinks

- [[Obsidian Value Map]]
- [[digests/AI X Digest Hub|AI X Digest Hub]]
- [[digests/2026-03|2026-03 Digest Index]]

## Navigation

- Previous: [[digests/2026-03-24 - AI X Digest|2026-03-24 - AI X Digest]]
- Next: [[digests/2026-03-26 - AI X Digest|2026-03-26 - AI X Digest]]

## Digest

## Morning signal

**TL;DR:** Supply chain attacks are becoming catastrophic (litellm compromised entire dependency trees in under an hour), frontier AI capabilities are accelerating (1T-parameter models running on MacBooks, ARC-AGI shows human-winnable benchmarks), and the industry is consolidating around safety infrastructure, agent memory systems, and robotics scaling from human video data.

## Security & Infrastructure Nightmares

[LiteLLM PyPI supply chain attack exfiltrates all credentials in under an hour](https://x.com/karpathy/status/2036487306585268612) — A single poisoned package version (1.82.8) stole SSH keys, AWS creds, API keys, crypto wallets via transitive dependencies; only caught because attacker code was buggy and crashed a machine, suggesting undetected attacks could run for weeks.

[Supply chain attacks demand fundamental rethinking of dependencies](https://x.com/karpathy/status/2036487306585268612) — Andrej Karpathy argues classical software engineering's "pyramid of bricks" dependency model is broken; proposes using LLMs to yoink functionality when possible rather than importing risky packages.

[Agents as attack surfaces require "de-vibing" infrastructure](https://x.com/DrJimFan/status/2036494601750716711) — Jim Fan warns filesystem-wide contamination vectors; every PDF, skill file, and context window becomes an attack surface; need layered shells/guardrails around agentic frameworks.

## Model Personalization & Behavior Issues

[LLM personalization memory is distracted and overfitted](https://x.com/karpathy/status/2036836816654147718) — All frontier LLMs seem to obsess over single past questions, creating false signal of deep interests; likely caused by training-time context relevance bias.

[Hypothesis: models overfit to RAG-retrieved memory at test time](https://x.com/karpathy/status/2036841069636370467) — During training, most context window information is relevant, so models develop bias to use what's given; then at inference, they overfit to anything that happens to trigger memory features.

## AI Safety & Governance

[OpenAI Foundation launching with $1B+ to address systemic risks](https://x.com/sama/status/2036488680769241223) — New focus on novel bioweapon threats, economic disruption, and emergent societal effects; Wojciech Zaremba leading "AI Resilience" approach; Jacob Trefethen heading Life Sciences/disease curing.

[Anthropic engaging with Department of War on AI security](https://x.com/DarioAmodei/status/2027152488659394660) — Dario Amodei statement signals formal government coordination on defense applications.

## Benchmarking & Reasoning

[ARC-AGI-3 is human-winnable with proper tooling](https://x.com/emollick/status/2036865990282092940) — Ethan Mollick confirms benchmark beatable by humans; unclear how much frontier model underperformance is due to harness/vision limitations vs. fundamental LLM reasoning gaps.

[ARC-AGI requires language-agnostic reasoning](https://x.com/fchollet/status/2036889580084101324) — An alien species with zero human language knowledge could ace it on day one; emphasizes pure adaptive reasoning capability.

## Model Scaling & Hardware

[1T-parameter Mixture-of-Experts models run on MacBook Pro](https://x.com/simonw/status/2036524171325563001) — Kimi K2.5 (1.026T params) streaming expert weights from SSD achieves 1.7 tok/s on M4 Max; only 32B active parameters in memory at once.

[397B model runs on iPhone with MoE streaming](https://x.com/simonw/status/2036296019835756929) — Qwen3.5-397B achieves 0.6 tok/s on mobile by streaming expert weights; demonstrates extreme edge deployment feasibility.

## Agent Memory Systems

[Andrew Ng's Context Hub solves outdated API hallucination](https://x.com/AndrewYNg/status/2031051809499054099) — Open CLI tool gives coding agents up-to-date API docs; agents annotate with workarounds for persistent learning across sessions; 6K+ GitHub stars in one week.

[New course: Agent Memory with persistent cross-session learning](https://x.com/AndrewYNg/status/2034314027678192114) — Teaching Memory Managers for semantic tool retrieval at scale; agents autonomously refine knowledge over time; built with Oracle partnership.

[Stack Overflow for AI agents to share learnings](https://x.com/AndrewYNg/status/2033577583200354812) — Context Hub agents can share documentation feedback; early-stage social platform for agent knowledge transfer.

## Robotics & Embodied AI

[EgoScale: 22-DoF humanoid learns from 20K hours human video](https://x.com/DrJimFan/status/2036136375494517142) — GR00T N1.5 trained on egocentric human data with near-perfect log-linear scaling (R²=0.998); assembles cars, operates syringes, folds shirts with zero robot-in-loop pre-training.

[Humanoid endgame due to minimal embodiment gap from humans](https://x.com/DrJimFan/status/2036136375494517142) — Simple kinematic retargeting of human finger motion to dexterous hands; no learned embeddings needed; unified action space transfers directly from video to robot.

[Dream2Flow: object-centered spatial information for robot generalization](https://x.com/drfeifei/status/2035067763048554579) — Using 3D object flow from video generation to improve robot manipulation in open-world scenarios.

## Community & Events

[AIE London event selling out; organizers still unprofitable](https://x.com/swyx/status/2036918746854678830) — First international AI Engineers conference sold out booths/tickets but logistical complexity curves are brutal; grateful for sponsor support from OpenAI, Braintrust, WorkOS.

## Platform Observations

[Sam Altman seeks single word for "throw all context at it"](https://x.com/sama/status/2036489823792607273) — GPT-5.4 Pro continues elite performance on hard/complex tasks; reflects broader pattern of context-maximization as frontier capability.

[Apple distilling Google Gemini for on-device Siri](https://x.com/emollick/status/2036845759283220546) — Ethan Mollick skeptical distilled models won't achieve generally capable agents users expect; knowledge distillation tradeoffs becoming critical.

---

## Evening signal

**TL;DR:** Supply chain attacks are the new existential threat to AI infrastructure (LiteLLM poisoning exposed credentials across 97M monthly users), while OpenAI launches a $1B+ nonprofit focused on safety and resilience. Meanwhile, the industry is cracking efficient inference—trillion-parameter models now run on MacBooks via MoE streaming—and agents are becoming the new attack surface for credential theft and filesystem contamination.

---

## Security & Supply Chain Risks

[LiteLLM PyPI Supply Chain Attack Exfiltrated Credentials at Scale](https://x.com/karpathy/status/2036487306585268612) — Single package poisoning exposed SSH keys, cloud credentials, wallets, and secrets across 97M monthly downloads; the attack was only caught due to a bug causing OOM crash, highlighting how undetected compromise could persist for weeks.

[Vibe Agents Create Filesystem-Scale Attack Vectors](https://x.com/DrJimFan/status/2036494601750716711) — With agents accessing entire filesystems, credentials can hide in ~/.claude, PDFs, skill directories, or context windows; base64-encoded contamination becomes the new malware delivery mechanism, requiring "de-vibing" layers of accountability.

---

## AI Safety & Governance

[OpenAI Foundation Commits $1B+ to AI Resilience and Science](https://x.com/sama/status/2036488680769241223) — Sam Altman announced new nonprofit leadership focused on novel biorisks, economic disruption, and emergent societal effects; Wojciech Zaremba shifted to Head of AI Resilience to reframe safety through a new lens beyond traditional approaches.

[Anthropic Engages Department of War on AI Deployment](https://x.com/DarioAmodei/status/2027152488659394660) — Dario Amodei confirmed direct discussions on national security implications, signaling mainstream AI labs now operating within defense/governance frameworks.

[Congress Signaling Broad AI Policy Direction](https://x.com/jackclarkSF/status/2035107315112976588) — White House movement on data centers, child protection, and security issues should break legislative logjams; stakeholder debates are now at scale.

---

## Intelligence vs. Knowledge

[Fluid Intelligence is a Multiplier, Not a Substitute](https://x.com/fchollet/status/2036549765471805564) — François Chollet argues memorized templates can fake competence temporarily, but true intelligence lets systems scale knowledge more cheaply; when high-fluid-intelligence systems emerge, they'll outcompete knowledge-dependent ones regardless of preparation.

[Distinguishing Adaptation from Preparation](https://x.com/fchollet/status/2036551534549643444) — Systems with actual fluid intelligence will dominate those relying on exhaustive training data, since knowledge gathering is trivial but recombination and application require real reasoning.

---

## Agent Infrastructure & Development

[Context Hub Gives Agents Fresh API Documentation](https://x.com/AndrewYNg/status/2031051809499054099) — Open CLI tool solves hallucination and outdated API calls in coding agents; agents can annotate docs with workarounds and eventually share learnings, creating a "Stack Overflow for agents."

[Memory-Aware Agents Persist Learning Across Sessions](https://x.com/AndrewYNg/status/2034314027678192114) — New course teaches Memory Manager design for persistent agent knowledge; semantic tool retrieval scales without context bloat, enabling autonomous refinement over time.

[Devin Code Review Catches Bugs Better Than Competitors](https://x.com/swyx/status/2036565584515899445) — Devin agents reviewing Devin-generated code catches mistakes through "fresh eyes" pattern; this "smart friend" subagent design is becoming the standard for high-capability peer review.

---

## Model Efficiency & Edge Deployment

[1T-Parameter Models Run on MacBooks via MoE Streaming](https://x.com/simonw/status/2036524171325563001) — Kimi K2's 1T params with only 32B active fit on M4 Max at 1.7 tok/s by streaming expert weights from SSD; eliminates full model RAM requirements.

[400B Parameter Model Running on iPhone](https://x.com/simonw/status/2036296019835756929) — Qwen3.5-397B-A17B achieves 0.6 tok/s on mobile using the same MoE streaming trick, making edge deployment of massive models viable.

---

## Robotics & Embodied AI

[EgoScale Behavior Cloning Breaks Teleoperator Dependency](https://x.com/DrJimFan/status/2036494601750716711) — Shifting from teleoperation to direct behavior cloning from video; 2026 focus is scaling robot learning without requiring physical robots.

[Dream2Flow Bridges Video Generation and Robot Control](https://x.com/drfeifei/status/2035067763048554579) — Object-centered spatial information from generated video improves robot manipulation generalization via 3D object flow representation.

---

## Content Creation & Experimentation

[Sora Compute Redirected from Creative Exploration](https://x.com/emollick/status/2036609949577413085) — Ethan Mollick's viral "duck hats + llama flute" Sora video highlights OpenAI's shift away from creative tool testing toward production prioritization.

[Lab Strategy Divergence: Focus vs. Breadth](https://x.com/emollick/status/2036573117431095665) — Anthropic maintains focus; OpenAI tests then abandons concepts (GPT Store, Sora); Google does everything simultaneously—outcome still unclear.

---

## Culture & Commentary

[Dependency Hell as an Engineering Paradigm Shift](https://x.com/karpathy/status/2036487306585268612) — Andrej Karpathy argues classical "dependencies are good" thinking needs reevaluation; prefers using LLMs to directly implement simple functionality rather than chaining risky packages.

[Media Still References Ex-Husbands Over Women's Work](https://x.com/AmandaAskell/status/2034690963696967822) — Amanda Askell's wry observation on persistent biographical framing bias in tech journalism.

[Project Hail Mary Film Honors Alien Worldbuilding](https://x.com/karpathy/status/2034865693544604001) — Karpathy praises Andy Weir adaptation for maintaining scientific rigor in alternate biochemistry, psychology, and tech trees—rare depth in fictional alien portrayal.

## Source provenance

- Original title: AI Digest — Mar 26, 2026 Morning
- Original title: AI Digest — Mar 25, 2026 Evening
- Normalized from old import files backed up outside the vault at: `/Users/skypawalker/.hermes/backups/obsidian-digests-pre-normalize-2026-05-10`
