---
title: "X-AI-2026-10-16"
date: 2026-10-16
tags: [AI, digest, x]
type: daily-digest
source: bird-cli-json
digest_format: editorial-v2
story_metadata:
  meta-muse-spark-open:
    section: Models
    deck: Downloadable weights, hosted APIs and a desktop demonstration using two M5 Ultra Mac Studios.
  perplexity-space:
    section: Infrastructure
  openai-live-voices:
    section: Models
  inbox-zero-mail:
    section: Applications
  rea-6-5-release:
    section: Project update
  goodfire-neuron-interpretation:
    section: Research
  harness-squared:
    section: Research catch-up
    visual:
      kind: bar
      title: Reported WorkBuddy-Bench scores
      unit: mean score
      caption: "Gemini 3.5 Flash with OpenCode, mean and standard deviation over three runs. Base: 72.4 ± 0.9. Harness²: 77.5 ± 2.5. Authors' results."
      source_url: https://arxiv.org/html/2610.14224v1
      points:
        - label: Base
          value: 72.4
          qualifier: exact
        - label: Harness²
          value: 77.5
          qualifier: exact
  anthropic-metr-access:
    section: Safety
  krea-3-editing:
    section: Image tools
  shopify-security-check:
    section: Developer tools
  pond-archiver:
    section: Open source
  hardware-reverse-engineering:
    section: Builder report
---

## Meta releases Muse Spark Open with downloadable weights
<!-- story-id: meta-muse-spark-open -->

Meta released Muse Spark Open on 15 October. The open-weight multimodal model has 816 billion parameters, 42 billion active parameters and a million-token context window. Meta built it for coding and long agent tasks.

Hosted APIs and downloadable weights are available. Meta lists vLLM, SGLang, MLX and llama.cpp among the supported inference engines. Weights are on Hugging Face. API partners include OpenRouter and Together AI.

Meta's desktop demonstration uses two M5 Ultra Mac Studios, each with up to 512 GB of unified memory. It depends on that pair of high-memory machines. Meta says it tested coding changes to Ice Cubes and frame-by-frame video work in DaVinci Resolve.

These are company demonstrations. The weights use the Muse Model License with limited commercial terms. The model card describes the company's evaluations and release conditions.

Sources: [Meta's announcement](https://research.meta.ai/blog/muse-spark-open), [model card](https://huggingface.co/meta-models/Muse-Spark-Open-816B-A42B). First-party release and evaluation claims.

## Perplexity open-sources SPACE for isolated agent code execution
<!-- story-id: perplexity-space -->

Perplexity open-sourced SPACE on 15 October. It says the platform runs every task in Perplexity Computer. Each task gets a Firecracker microVM. SPACE controls credentials and outbound traffic from outside the VM.

The Apache 2.0 repository includes an HTTP API. Local setup requires Linux x86_64 with KVM and privileged Docker. The guide uses Kind and Kubernetes, and does not run directly on macOS. Local setup uses development passwords and signing keys. The architecture also describes a direct worker adapter.

Sources: [Perplexity's announcement](https://x.com/perplexity_ai/status/2110778478312481167), [SPACE repository](https://github.com/perplexityai/SPACE), [installation guide](https://raw.githubusercontent.com/perplexityai/SPACE/main/docs/installation.md), [architecture](https://raw.githubusercontent.com/perplexityai/SPACE/main/docs/architecture.md). First-party release and documentation.

## OpenAI rolls out GPT-Live-1.1 voices, including Hindi
<!-- story-id: openai-live-voices -->

OpenAI announced GPT-Live-1.1 on 15 October for Voice in ChatGPT, Codex and dots. It says the update brings new voices and better accents. The rollout covers all users.

The announcement lists French, German, Hindi, Mexican Spanish, Korean and Japanese. It also promises less "checking..." during voice interactions, but gives no latency figures or language-by-language quality results.

If you build for Indian users, try the new Hindi voices in the consumer apps. API access is coming later, so developers must wait before integrating GPT-Live-1.1. OpenAI gives no API release date.

Source: [OpenAI's GPT-Live-1.1 announcement](https://x.com/OpenAI/status/2110797830361436604). First-party rollout and quality claims.

## Inbox Zero Mail adds a free Gmail and Outlook client
<!-- story-id: inbox-zero-mail -->

Elie Steinbock launched Inbox Zero Mail on 15 October, adding an email client to the existing AI assistant. The client combines Gmail and Outlook accounts and is free to use.

The website lists web, Mac, Windows and iPhone clients. The AI assistant is an optional paid service. The assistant, web app and desktop client have public source code; the website says the iPhone app is not open source yet.

The repository's license adds restrictions on commercial monetization to AGPLv3 wording. It also requires an enterprise license for business use by organizations with five or more employees, contractors or users.

Sources: [Launch announcement](https://x.com/elie2222/status/2110756359679426815), [product details](https://www.getinboxzero.com/), [repository](https://github.com/elie222/inbox-zero), [license](https://raw.githubusercontent.com/elie222/inbox-zero/main/LICENSE).

## REA 6.5 recovers relationships between JavaScript bundles
<!-- story-id: rea-6-5-release -->

Reverse Engineer Anything published release 6.5.0 on 14 October. It adds controls for inspecting JavaScript applications and retaining analysis results. This updates the project's earlier coverage in the 12 October digest.

The release lets agents select exact JavaScript files and recover relationships across selected bundles. Compact summaries let them page through retained evidence. The project verified cross-bundle recovery on named Linux x64 fixtures.

REA connects coding agents to inspection tools for applications and native binaries. Native analysis can use an existing Hopper, Ghidra or IDA installation. The release notes state the tested platforms and gaps for each provider.

Sources: [REA repository](https://github.com/morluto/rea), [6.5.0 release](https://github.com/morluto/rea/releases/tag/rea-agents-6.5.0). Project documentation and release notes. Catch-up from 14 October.

## Goodfire argues a network's own neurons are easier to interpret
<!-- story-id: goodfire-neuron-interpretation -->

In a Goodfire essay, Nick Cammarata argues that modern neural networks' own neurons are more interpretable than earlier studies suggested. He says older tools misread some apparent mixtures of concepts.

His team's preliminary audits of Qwen3-32B estimate that roughly 90% of neuron poles have one main job. Poles are the positive and negative sides of a neuron's response. That estimate depends on what counts as one job and how the researchers treat weak activations.

Cammarata argues for studying neurons and circuits directly, rather than first training a separate feature-decomposition model. The essay presents a working hypothesis. The technical companion paper is still forthcoming.

Source: [Neural Networks Are Already Clean](https://already-clean.goodfire.com/). Research essay and preliminary author estimates.

## Harness² tests recursive edits to agent instructions
<!-- story-id: harness-squared -->

First posted on 9 October, Harness² describes a method for improving the instructions and tools around an agent without changing its model weights. A 15 October discussion brought the paper back into view.

The method proposes instruction changes and runs candidate versions on the same task. It combines changes supported by those tests, then saves useful lessons for later tasks.

The authors test GLM-5 and Gemini 3.5 Flash across WorkBuddy-Bench, JobBench and LAB. Their task comparisons guide edits without a ground-truth verifier. The paper warns that execution randomness and shared model biases limit that evidence.

Sources: [Paper and submission date](https://arxiv.org/abs/2610.14224), [method and reported results](https://arxiv.org/html/2610.14224v1), [15 October discussion](https://x.com/dair_ai/status/2110755132548038788). Author-reported benchmark results. Research catch-up from 9 October.

## In brief

### Anthropic gives METR evaluators employee-like access
<!-- story-id: anthropic-metr-access -->

Anthropic said on 15 October that it has given a METR team employee-like access to assess its safety practices. It is discussing evaluation arrangements with other organizations. The announcement reports access, not completed findings or a safety certification.

Source: [Anthropic's evaluator-access announcement](https://x.com/AnthropicAI/status/2110784662071398807). First-party statement.

### Krea 3 targets regional image edits
<!-- story-id: krea-3-editing -->

Krea says its new image model locates the region to change and renders that area. Krea 3 is available through its app and API. Krea offers enterprise self-hosting under negotiated terms. The launch page's speed and quality comparisons are the company's own.

Source: [Krea 3 product and availability details](https://www.krea.ai/krea-3). First-party claims.

### Shopify adds a local app security check
<!-- story-id: shopify-security-check -->

Shopify added `shopify app security check` to AI Toolkit on 15 October. It scans app code, configuration and dependencies, then reports potential problems and how to fix them. Shopify says a clean report does not guarantee security.

Source: [Dated Shopify developer announcement](https://shopify.dev/changelog/blog/build-more-secure-apps-with-shopify-s-ai-toolkit-security-check).

### Pond brings a local archive to MCP clients
<!-- story-id: pond-archiver -->

Pond is a new MIT-licensed macOS archiver with a searchable local library. Its assistant can use cloud models or a local host. MCP clients can search the same library. Saving webpages requires its browser extension. Windows and Linux remain on the roadmap.

Sources: [15 October launch](https://x.com/raphaelsalaja/status/2110722616226914684), [repository and platform details](https://github.com/raphaelsalaja/pond), [license](https://raw.githubusercontent.com/raphaelsalaja/pond/main/LICENSE).

### hw-harness compares Windows and Linux device traces
<!-- story-id: hardware-reverse-engineering -->

Christian Schaller shared hw-harness after using agents to investigate scanner and camera drivers. It captures a working Windows device session and compares it with Linux behavior. His 15 October report says the published tool differs from the custom scripts he used in those investigations.

Sources: [Firsthand account](https://blogs.gnome.org/uraeus/2026/10/15/aiandreverseengineerhardware/), [hw-harness repository](https://github.com/cschalle/hw-harness). Builder report, not an independent replication.

## Navigation

- Previous: [[digests/x-ai-2026-10-15|X-AI-2026-10-15]]
- Next: None

## Backlinks

- [[index|Mindscape]]
- [[digests/x-ai-2026|X-AI 2026]]
- [[digests/x-ai-2026-10|X-AI-2026-10]]
