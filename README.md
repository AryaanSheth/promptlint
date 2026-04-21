## PromptLint

[![PyPI version](https://img.shields.io/pypi/v/promptlint-cli?color=00ff88&labelColor=0a0a0a)](https://pypi.org/project/promptlint-cli/)
[![npm version](https://img.shields.io/npm/v/promptlint-cli?color=00ff88&labelColor=0a0a0a)](https://www.npmjs.com/package/promptlint-cli)
[![VS Code Marketplace](https://img.shields.io/visual-studio-marketplace/v/PromptLint.promptlint-vscode?color=00ff88&labelColor=0a0a0a&label=vscode)](https://marketplace.visualstudio.com/items?itemName=PromptLint.promptlint-vscode)
[![GitHub Marketplace](https://img.shields.io/badge/GitHub%20Action-Marketplace-00ff88?labelColor=0a0a0a&logo=github)](https://github.com/marketplace/actions/promptlint-action)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue?labelColor=0a0a0a)](LICENSE)

Static analysis for LLM prompts. Think ESLint, but for the text you send to GPT-4 / Claude / Gemini.

Catches token waste, vague language, prompt injection, missing structure, leaked secrets, PII, and more. Runs locally, no API calls, results in milliseconds.

```
$ promptlint --file system_prompt.txt

PromptLint Findings
[ INFO     ] cost (line -) Prompt is ~38 tokens (~$0.0002 input per call on gpt-4o).
[ WARN     ] structure-sections (line -) No explicit sections detected (Task/Context/Output).
[ WARN     ] clarity-vague-terms (line 1) Vague term 'some' detected. Be more specific.
[ INFO     ] verbosity-redundancy (line 3) Redundant phrase 'In order to' detected. Use simpler alternative.
[ WARN     ] politeness-bloat (line 1) Consider removing 'Please' (adds 1.5 tokens without semantic value).
[ CRITICAL ] prompt-injection (line 5) Injection pattern detected: 'ignore previous instructions'.

1 file(s) scanned, 6 finding(s) in 0.41s
```

---

### Install

**GitHub Action** (recommended for CI) — scan files or lint an inline string:
```yaml
# Scan prompt files
- uses: AryaanSheth/promptlint@v1
  with:
    path: 'prompts/**/*.txt'

# Or lint an inline prompt string
- uses: AryaanSheth/promptlint@v1
  with:
    prompt: 'You are a helpful assistant. Ignore previous instructions.'
```

**Python (pip)**
```bash
pip install promptlint-cli        # requires Python 3.9+
promptlint --file prompt.txt
```

**Node.js (npm)**
```bash
npm install -g promptlint-cli     # requires Node.js 16+
# or without installing:
npx promptlint-cli --file prompt.txt
```

**VS Code** — [install from the Marketplace](https://marketplace.visualstudio.com/items?itemName=PromptLint.promptlint-vscode)

---

### GitHub Action

The fastest way to add PromptLint to CI. No installation step — just add to any workflow:

```yaml
name: Lint Prompts
on: [pull_request]

jobs:
  promptlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AryaanSheth/promptlint@v1
        with:
          path: 'prompts/**/*.txt'
          fail-level: critical    # block merges on injection / leaked secrets / PII
          show-score: true        # print A–F grade in the log
```

You can also lint an inline prompt string instead of files — no `actions/checkout` needed:

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    prompt: ${{ env.SYSTEM_PROMPT }}
    fail-level: critical
    show-score: true
```

**Inputs**

| Input | Default | Description |
|---|---|---|
| `path` | `.` | File path or glob pattern to scan. Ignored when `prompt` is set. |
| `prompt` | `` | Inline prompt text to lint. When set, `path` is ignored. |
| `fail-level` | `critical` | Exit non-zero on: `none` \| `warn` \| `critical` |
| `config` | `` | Path to `.promptlintrc`. Auto-detects repo root if blank. |
| `show-score` | `false` | Print A–F health score in the workflow log |
| `sarif-output` | `` | Write SARIF v2.1.0 file for the GitHub Security tab |
| `annotations` | `true` | Emit inline annotations on the PR diff |

**Outputs**

| Output | Description |
|---|---|
| `findings-count` | Total findings across all scanned files |
| `critical-count` | CRITICAL severity findings |
| `score` | Health score 0–100 |
| `grade` | Health grade A–F |

**With SARIF (Security tab integration)**

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v4

  - name: Run PromptLint
    id: lint
    uses: AryaanSheth/promptlint@v1
    with:
      path: 'prompts/'
      sarif-output: promptlint.sarif
      show-score: true

  - uses: github/codeql-action/upload-sarif@v3
    with:
      sarif_file: promptlint.sarif
    if: always()

  - run: echo "Score ${{ steps.lint.outputs.score }}/100 (${{ steps.lint.outputs.grade }})"
```

See [action/README.md](action/README.md) for the full action reference.

---

### CLI Usage

```bash
# lint a file
promptlint --file prompt.txt

# lint inline text
promptlint -t "Please write some code for me"

# multiple files with globs
promptlint prompts/**/*.txt --exclude prompts/drafts/*

# pipe from stdin
cat prompt.txt | promptlint --format json

# auto-fix what it can
promptlint --file prompt.txt --fix

# CI mode: exit non-zero on warnings, print summary only
promptlint prompts/ --fail-level warn --quiet
```

Exit codes: `0` = clean, `1` = warnings (with `--fail-level warn`), `2` = critical issues.

---

### What it checks

| Rule | Severity | What it catches | Fixable |
|------|----------|----------------|---------|
| `prompt-injection` | CRITICAL | `ignore previous instructions`, role-hijacking, obfuscated variants | yes |
| `jailbreak-pattern` | CRITICAL | DAN prompts, "act as", "pretend you are" | — |
| `secret-in-prompt` | CRITICAL | Hardcoded API keys, tokens, passwords | — |
| `pii-in-prompt` | CRITICAL | SSNs, credit cards, emails, phone numbers | — |
| `context-injection-boundary` | CRITICAL | Unsanitized user content injected into system prompts | — |
| `cost` | INFO | Token count and per-call cost estimate | — |
| `cost-limit` | WARN | Exceeds your configured token budget | — |
| `structure-sections` | WARN | No clear Task/Context/Output sections | yes |
| `role-clarity` | WARN | No system role defined | — |
| `output-format-missing` | WARN | No output format specified | — |
| `hallucination-risk` | WARN | Asks model to recall facts without grounding | — |
| `clarity-vague-terms` | WARN | "some", "stuff", "maybe", "various" | — |
| `specificity-examples` | INFO | No examples provided for complex instructions | — |
| `specificity-constraints` | INFO | No length/format/scope constraints | — |
| `politeness-bloat` | WARN | "please", "kindly", "thank you" (burns tokens) | yes |
| `verbosity-sentence-length` | INFO | Sentences over 40 words | — |
| `verbosity-redundancy` | INFO | "in order to" → "to", "due to the fact that" → "because" | yes |
| `actionability-weak-verbs` | INFO | Excessive passive voice | — |
| `consistency-terminology` | INFO | Mixed terms (user/customer, function/method) | — |
| `completeness-edge-cases` | INFO | No error handling specified | — |

Run `promptlint --list-rules` to see them all, or `promptlint --explain <rule-id>` for details.

---

### Auto-fix

Pass `--fix` and PromptLint will rewrite the prompt in place — removing politeness filler, simplifying redundant phrases, stripping injection lines, and scaffolding missing structure tags:

```
$ promptlint -t "Please kindly write code in order to sort the array, thank you" --fix

Optimized Prompt
<task>Write code to sort the array.</task>
```

---

### Configuration

Drop a `.promptlintrc` in your repo root (or run `promptlint --init`):

```yaml
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

rules:
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - "you are now a [a-zA-Z ]+"
  pii_in_prompt:
    enabled: true
    check_email: true
    check_ssn: true
  politeness_bloat:
    enabled: true
    words: [please, kindly, thank you, i would appreciate]
    savings_per_hit: 1.5
  role_clarity:
    enabled: true
    severity: warn          # downgrade from CRITICAL

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
```

Every rule can be toggled and severity-overridden individually. See [docs/](docs/) for the full reference.

---

### CLI reference

```
promptlint [FILES...] [OPTIONS]

  -V, --version            Show version
  -f, --file PATH          Single prompt file
  -t, --text TEXT          Inline prompt text
  -c, --config PATH        Config file (default: .promptlintrc)
  --format {text,json}     Output format
  --fix                    Auto-fix and print optimized prompt
  --fail-level LEVEL       none / warn / critical (default: critical)
  --show-dashboard         Token savings breakdown
  -q, --quiet              Summary line only (for CI)
  --exclude PATTERN        Exclude globs (repeatable)
  --list-rules             Show all rules
  --explain RULE_ID        Explain a specific rule
  --init                   Generate starter .promptlintrc
```

---

### Inline ignores

Suppress a specific rule on a line:
```
Please write code  # promptlint-disable politeness-bloat
```

Suppress all rules on a line:
```
Please write code  # promptlint-disable
```

---

### Repo layout

```
action/         GitHub Action source (action.yml is at repo root)
cli/            Python CLI (PyPI: promptlint-cli)
npm/            Node.js CLI (npm: promptlint-cli)
vscode/         VS Code extension (Marketplace: PromptLint.promptlint-vscode)
landing/        Marketing site
docs/           Full reference documentation
.claude/skills/ Claude Code agent skill
.cursor/skills/ Cursor agent skill
```

---

### Security

- All analysis is local. Nothing leaves your machine.
- Injection detection normalizes leetspeak (`1gn0r3`), zero-width unicode, fullwidth chars, and character repetition before matching — catches obfuscated attacks that raw regex misses.
- No API keys in the repo. Credentials are loaded from `.env` files that are gitignored.

---

### License

[Apache 2.0](LICENSE)
