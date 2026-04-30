# What is PromptLint?

PromptLint is a **static analysis tool for LLM prompts** — like ESLint for the text you send to GPT-4, Claude, Gemini, or any other model. It catches problems locally before they reach your AI API.

## The Problem

Prompt engineering is a first-class engineering discipline, but most teams treat prompts as throwaway strings. This leads to:

- **Wasted money** — redundant phrasing, politeness tokens, and bloated context add up at scale
- **Security vulnerabilities** — injection attacks, embedded secrets, and PII exposure
- **Inconsistent output** — vague instructions, missing output format specs, and undefined roles cause hallucinations
- **Unmaintainable prompts** — no structure, inconsistent terminology, missing edge case coverage

PromptLint makes these problems visible before they ship.

## What It Checks

PromptLint runs **21 rules** across five categories:

| Category | What it catches |
|----------|----------------|
| **Security** | Injection attacks, jailbreak patterns, hardcoded secrets, PII, boundary violations |
| **Cost** | Token count, budget enforcement, cost projection |
| **Structure** | Missing sections, undefined roles, absent output formats, hallucination-inducing patterns |
| **Quality** | Vague language, missing examples/constraints, weak verbs, politeness bloat, redundancy |
| **Completeness** | Missing edge case coverage, terminological inconsistency |

## How It Works

1. **Parse** — PromptLint reads your prompt from a file, stdin, or an inline `--text` argument
2. **Analyze** — Each rule scans the text using regex patterns and heuristics
3. **Report** — Findings are output as colored terminal text, JSON, or SARIF
4. **Fix** (optional) — 5 rules can automatically rewrite the prompt

All processing happens **locally**. No data is ever sent to an external service.

## Severity Levels

Every finding has a severity level that maps to exit codes:

| Severity | Meaning | Exit code trigger |
|----------|---------|:-----------------:|
| `CRITICAL` | Security risk or hard constraint violation — must fix | `--fail-level critical` (default) |
| `WARN` | Quality or structural issue — should fix | `--fail-level warn` |
| `INFO` | Optimization suggestion — consider fixing | `--fail-level info` |

## Distribution

PromptLint ships as four separate packages from the same codebase:

- **`promptlint-cli` (PyPI)** — Full-featured Python CLI using `tiktoken` for exact token counts
- **`promptlint-cli` (npm)** — TypeScript CLI using a character-based heuristic (±15%)
- **GitHub Action** — `AryaanSheth/promptlint@v1` — wraps the npm CLI for CI/CD
- **VS Code Extension** — Real-time linting in the editor with quick-fix support

## Who Should Use It

- **AI engineers** shipping prompts to production
- **Backend teams** integrating LLMs into their APIs
- **Security teams** auditing AI features for injection/PII risks
- **Cost-conscious teams** running high-volume inference workloads
- **Platform teams** enforcing prompt quality standards in CI/CD

## Next Steps

- [Install and run your first lint →](/guide/getting-started)
- [Browse all 21 rules →](/rules/)
- [Set up GitHub Actions integration →](/integrations/github-actions)
