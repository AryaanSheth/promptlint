---
layout: home

hero:
  name: "PromptLint"
  text: "Lint your LLM prompts"
  tagline: Catch cost waste, security risks, PII leaks, and quality issues before they reach production. 20 intelligent rules, 5 auto-fixes, zero API calls.
  image:
    src: /logo.svg
    alt: PromptLint logo
  actions:
    - theme: brand
      text: Get Started →
      link: /guide/getting-started
    - theme: alt
      text: View on GitHub
      link: https://github.com/AryaanSheth/promptlint
    - theme: alt
      text: Browse Rules
      link: /rules/

features:
  - icon: 🔒
    title: Security First
    details: Detect prompt injection, jailbreak attempts, hardcoded secrets, PII exposure, and context boundary violations — all at CRITICAL severity with zero false negatives in production.
    link: /rules/#security
    linkText: Security rules

  - icon: 💰
    title: Cost Analytics
    details: Count tokens with tiktoken, project monthly spend, and quantify savings before you deploy. See exactly how much a fix saves at your call volume.
    link: /rules/cost
    linkText: Cost rules

  - icon: ✨
    title: Quality Checks
    details: Catch vague language, missing examples, weak verbs, politeness bloat, and terminological inconsistency — the subtle issues that degrade model output quality.
    link: /rules/#quality
    linkText: Quality rules

  - icon: 🔧
    title: Auto-Fix
    details: Five rules can automatically rewrite your prompt — remove politeness bloat, collapse redundant phrases, strip injections, scaffold structure, and normalize spacing.
    link: /guide/auto-fix
    linkText: Auto-fix guide

  - icon: ⚡
    title: CI/CD Ready
    details: JSON, SARIF v2.1, and colored terminal output. Exit codes map directly to fail levels. Drop into GitHub Actions, GitLab CI, or any pipeline in under 5 minutes.
    link: /integrations/github-actions
    linkText: GitHub Actions

  - icon: 🏗️
    title: Structure Analysis
    details: Ensure prompts have task, context, and output sections. Detect missing role definitions, absent output format specs, and conditions that increase hallucination risk.
    link: /rules/#structure
    linkText: Structure rules
---

## Quick Start

Install via pip or npm, then lint your first prompt:

::: code-group

```bash [pip]
pip install promptlint-cli
promptlint --file prompt.txt
```

```bash [npm]
npm install -g promptlint-cli
promptlint --file prompt.txt
```

```bash [GitHub Action]
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
    fail-level: warn
```

:::

---

## Example Output

```
  PromptLint v1.3.0

  ┌─────────────────────────────────────────────────────────────┐
  │  File: prompts/system_prompt.txt  (97 tokens · ~$0.0005)   │
  └─────────────────────────────────────────────────────────────┘

  [ CRITICAL ] prompt-injection (line 3)
    Injection pattern detected: 'ignore previous instructions'

  [ CRITICAL ] pii-in-prompt (line 7)
    Email address detected: us**@example.com

  [ WARN ] structure-sections (line -)
    No explicit sections detected (Task / Context / Output)

  [ WARN ] politeness-bloat (line 1)
    Consider removing 'Please' — models don't need it

  [ INFO ] specificity-examples (line -)
    No examples provided — add 1-2 to improve consistency

  ────────────────────────────────────────────────────────────────
  Score: 42/100  Grade: F   5 findings  (2 critical · 2 warn · 1 info)
  Run with --fix to auto-resolve 3 of these issues
```

---

## Install via Multiple Channels

| Channel | Command | When to use |
|---------|---------|-------------|
| **pip** | `pip install promptlint-cli` | Python projects & scripts |
| **npm** | `npm install -g promptlint-cli` | Node.js projects & pipelines |
| **GitHub Action** | `AryaanSheth/promptlint@v1` | Any GitHub-hosted CI |
| **VS Code** | Search "PromptLint" in Extensions | Real-time editor feedback |

---

## 20 Rules, 5 Auto-Fixes

| Category | Rules | Auto-fixable |
|----------|-------|:---:|
| 💰 Cost & Tokens | `cost`, `cost-limit` | — |
| 🔒 Security | `prompt-injection`, `jailbreak-pattern`, `secret-in-prompt`, `pii-in-prompt`, `context-injection-boundary` | ✅ 1 |
| 🏗️ Structure | `structure-sections`, `role-clarity`, `output-format-missing`, `hallucination-risk` | ✅ 1 |
| ✨ Clarity | `clarity-vague-terms` | — |
| 🎯 Specificity | `specificity-examples`, `specificity-constraints` | — |
| 📝 Verbosity | `politeness-bloat`, `verbosity-redundancy`, `verbosity-sentence-length` | ✅ 2 |
| 💪 Actionability | `actionability-weak-verbs` | — |
| 🔄 Consistency | `consistency-terminology` | — |
| ✅ Completeness | `completeness-edge-cases` | — |

[Browse all rules →](/rules/)
