# Changelog

All notable changes to PromptLint are documented here.

## v1.4.0

**Released:** April 2026

### New Rule
- `output-length-missing` — INFO-level completeness rule that fires when a prompt contains a task verb (`write`, `generate`, `list`, etc.) but no length constraint (word count, sentence limit, brevity directive). Total: **21 rules**, **5 auto-fixable**.

### New CLI Features

| Flag | Description |
|------|-------------|
| `--show-score` | Display health score (0–100) + letter grade (A–F) and per-category breakdown |
| `--badge` | Output a Shields.io badge URL + markdown snippet for the health score |
| `--compare FILE_A FILE_B` | Lint two prompts and show score delta per category — useful for validating rewrites |
| `--update-baseline` | Write current findings to `.promptlintbaseline`; future runs suppress known issues |
| `--install-hooks` | Install a pre-commit git hook that lints staged `.txt`/`.md`/`.prompt` files |

### Improvements
- **Message array input** — both CLIs now accept OpenAI/Anthropic `[{role, content}…]` JSON arrays via `--text` or stdin; `content` fields are joined and linted as a single prompt
- **TS autofix parity** — `verbosity-redundancy` auto-fix expanded from 7 to 41 replacement patterns to match the Python implementation
- Docs site redesigned to match the main landing page (black/green terminal aesthetic, JetBrains Mono, film grain overlay)
- New [Config Examples](/guide/config-examples) page with 10 ready-to-copy `.promptlintrc` starters for common use cases

---

## v1.3.0

**Released:** 2024

### New Rules
- `jailbreak-pattern` — Detects jailbreak attempts and persona hijacking
- `secret-in-prompt` — Detects hardcoded API keys, passwords, connection strings
- `pii-in-prompt` — Detects emails, phone numbers, SSNs, credit card numbers
- `context-injection-boundary` — Enforces trust boundaries on user-injected content
- `role-clarity` — Checks for missing role/persona definitions
- `output-format-missing` — Checks for missing output format specification
- `hallucination-risk` — Detects patterns that increase hallucination likelihood

### Improvements
- SARIF v2.1.0 output format for GitHub Security tab integration
- VS Code extension with real-time linting and quick-fix support
- GitHub Action with PR annotations and SARIF upload
- Python/TypeScript parity tests in CI
- Score (0–100) and grade (A–F) in all output formats

### Rule Count
Total: **20 rules**, **5 auto-fixable**

---

## v1.2.0

### New Features
- `--show-dashboard` flag for cost savings visualization
- Monthly and annual cost projection in dashboard
- `--rule` flag to run a single rule
- `--explain` flag for rule documentation in the terminal

---

## v1.1.0

### New Features
- `--format sarif` output (v2.1.0)
- Score and grade calculation
- `calls_per_day` config for cost projection

### New Rules
- `completeness-edge-cases`
- `consistency-terminology`

---

## v1.0.0

### Initial Stable Release

- 13 rules across security, cost, quality, and structure
- `--fix` auto-fix with 5 fixable issues
- `--format json` for CI/CD
- `.promptlintrc` YAML configuration
- Python CLI (pip) and TypeScript CLI (npm)
- GitHub Action (`AryaanSheth/promptlint@v1`)

### Rules at Launch
- `cost`, `cost-limit`
- `prompt-injection`
- `structure-sections`
- `clarity-vague-terms`
- `specificity-examples`, `specificity-constraints`
- `politeness-bloat`
- `verbosity-redundancy`, `verbosity-sentence-length`
- `actionability-weak-verbs`
- `consistency-terminology`, `completeness-edge-cases`

---

## v0.2.0

- Structure flexibility: XML, headings, and Markdown all recognized
- Politeness configuration: `allow_politeness: true` demotes to INFO
- Improved auto-fix: structure scaffold respects `structure_style` config

## v0.1.0

- Initial release with 13 rules and 5 auto-fixes
