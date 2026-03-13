# promptlint

> Static analysis for LLM prompts — catch token waste, quality issues, and injection risks before they reach production.

[![npm version](https://img.shields.io/npm/v/promptlint.svg)](https://www.npmjs.com/package/promptlint)
[![License](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](LICENSE)

## Install

```bash
npm install -g promptlint
# or use without installing
npx promptlint --text "your prompt here"
```

## Usage

```bash
# Lint a file
promptlint prompt.txt

# Lint inline text
promptlint --text "Please kindly write me some code"

# Pipe from stdin
cat prompt.txt | promptlint

# Lint multiple files / globs
promptlint prompts/**/*.txt

# Apply auto-fixes
promptlint --fix prompt.txt

# JSON output (for CI integration)
promptlint --format json prompt.txt

# Show token savings dashboard
promptlint --show-dashboard prompt.txt

# CI mode — exit 1 on warnings
promptlint --fail-level warn prompt.txt
```

## Rules

| ID | Category | Severity | Auto-fix |
|----|----------|----------|----------|
| cost | Cost | INFO | — |
| cost-limit | Cost | WARN | — |
| prompt-injection | Security | CRITICAL | yes |
| structure-sections | Structure | WARN | yes |
| clarity-vague-terms | Quality | WARN | — |
| specificity-examples | Quality | INFO | — |
| specificity-constraints | Quality | INFO | — |
| politeness-bloat | Quality | WARN | yes |
| verbosity-sentence-length | Quality | INFO | — |
| verbosity-redundancy | Quality | INFO | yes |
| actionability-weak-verbs | Quality | INFO | — |
| consistency-terminology | Quality | INFO | — |
| completeness-edge-cases | Quality | INFO | — |

```bash
# List all rules
promptlint --list-rules

# Explain a rule
promptlint --explain prompt-injection
```

## Configuration

Generate a starter config:

```bash
promptlint --init
```

This creates a `.promptlintrc` (YAML) in your current directory:

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
  politeness_bloat:
    enabled: true
    words: [please, kindly, thank you]

fix:
  enabled: true
  politeness_bloat: true
  verbosity_redundancy: true
```

## Disable rules inline

```text
Please write some code  # promptlint-disable politeness-bloat
Some vague stuff        # promptlint-disable
```

## Programmatic API

```typescript
import { analyze, applyFixes, loadConfig } from "promptlint";

const config = loadConfig(); // reads .promptlintrc
const findings = analyze("Please kindly write some code", config);
const fixed = applyFixes("Please kindly write some code", config);

console.log(findings);
// [{ level: 'WARN', rule: 'politeness-bloat', message: '...' }]
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | No issues (or below fail-level) |
| 1 | Warnings found (with `--fail-level warn`) |
| 2 | Critical issues found |

## Links

- [Website](https://promptlint.dev)
- [VS Code Extension](https://marketplace.visualstudio.com/items?itemName=PromptLint.promptlint-vscode)
- [Python package (PyPI)](https://pypi.org/project/promptlint-cli/)
- [GitHub](https://github.com/AryaanSheth/promptlint)

## License

Apache-2.0
