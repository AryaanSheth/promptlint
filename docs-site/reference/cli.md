# CLI Reference

Complete reference for the `promptlint` command-line interface.

## Synopsis

```bash
promptlint [OPTIONS] [FILES...]
```

## Input Options

### `--file PATH`, `-f PATH`

Lint a prompt file. Supports glob patterns.

```bash
promptlint --file prompt.txt
promptlint --file "prompts/**/*.txt"
promptlint -f system_prompt.md
```

### `--text TEXT`, `-t TEXT`

Lint an inline string. Use quotes for multi-line text.

```bash
promptlint --text "Write a Python function"
promptlint -t "Task: Summarize the document
Output: 3 bullet points"
```

### Stdin

Pipe text via stdin:

```bash
cat prompt.txt | promptlint
echo "Write a function" | promptlint
```

::: warning
Either `--file`, `--text`, or stdin is required. Combining `--file` and `--text` raises an error.
:::

## Output Options

### `--format FORMAT`

**Values:** `text` (default), `json`, `sarif`

```bash
promptlint --file prompt.txt --format json
promptlint --file prompt.txt --format sarif > results.sarif
```

**JSON output structure:**
```json
{
  "version": "1.3.0",
  "file": "prompt.txt",
  "token_count": 97,
  "score": 72,
  "grade": "C",
  "findings": [
    {
      "rule_id": "prompt-injection",
      "level": "CRITICAL",
      "line": 3,
      "message": "Injection pattern detected: 'ignore previous instructions'"
    }
  ],
  "summary": {
    "total": 3,
    "critical": 1,
    "warn": 1,
    "info": 1
  }
}
```

### `--show-dashboard`

Display a cost savings dashboard after linting.

```bash
promptlint --file prompt.txt --show-dashboard
```

### `--show-score`

Display a prompt health score (0–100) with a letter grade and per-category breakdown.

```bash
promptlint --file prompt.txt --show-score
```

Example output:
```
Prompt Health Score
Overall: 78/100 (B)
  Security:     100
  Cost:         90
  Quality:      65
  Completeness: 70
```

### `--badge`

Output a Shields.io badge URL for the prompt health score. Requires `--show-score`.

```bash
promptlint --file prompt.txt --show-score --badge
```

Example output:
```
Badge URL: https://img.shields.io/badge/promptlint%3A78%2F100%20(B)-green
Markdown:  ![PromptLint Score](https://img.shields.io/badge/...)
```

## Fix Options

### `--fix`

Apply auto-fixes and print the optimized prompt to stdout.

```bash
promptlint --file prompt.txt --fix
promptlint --file prompt.txt --fix > prompt_fixed.txt
```

See the [Auto-Fix guide](/guide/auto-fix) for details.

## Baseline Options

### `--update-baseline`

Write the current set of findings to `.promptlintbaseline`. On subsequent runs, findings already in the baseline are silently suppressed. Useful for brownfield codebases where you want to fix new issues without being blocked by pre-existing ones.

```bash
# Capture all current issues as "known"
promptlint --file "prompts/**/*.txt" --update-baseline

# Future runs only report NEW issues
promptlint --file "prompts/**/*.txt"
```

The baseline file is a JSON fingerprint list and is safe to commit to git. Delete it to reset.

## Comparison

### `--compare FILE_A FILE_B`

Lint two prompt files and show a side-by-side score comparison with deltas for each category.

```bash
promptlint --compare prompt_v1.txt prompt_v2.txt
```

Example output:
```
Compare: prompt_v1.txt  vs  prompt_v2.txt
  Overall:      62 → 78  (+16)
  Security:     100 → 100  (0)
  Cost:         80 → 90   (+10)
  Quality:      50 → 65   (+15)
  Completeness: 60 → 70   (+10)
  Findings:     12 → 7

prompt_v2.txt scores higher (+16 pts)
```

Also works with `--format json` for pipeline integration.

## Exit Code Options

### `--fail-level LEVEL`

**Values:** `critical` (default), `warn`, `none`

Set the minimum severity that causes a non-zero exit code.

```bash
promptlint --file prompt.txt --fail-level warn   # exit 1 on WARN+
promptlint --file prompt.txt --fail-level critical  # exit 2 on CRITICAL
promptlint --file prompt.txt --fail-level none   # always exit 0
```

## Configuration Options

### `--config PATH`

Use a specific config file instead of searching for `.promptlintrc`.

```bash
promptlint --file prompt.txt --config /path/to/security.yaml
```

### `--init`

Generate a starter `.promptlintrc` in the current directory with all defaults documented.

```bash
promptlint --init
```

## Setup Commands

### `--install-hooks`

Install a pre-commit git hook that automatically lints staged `.txt`, `.md`, and `.prompt` files before each commit.

```bash
promptlint --install-hooks
```

Creates `.git/hooks/pre-commit` with:
```sh
#!/bin/sh
staged=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(txt|md|prompt)$')
if [ -n "$staged" ]; then
  promptlint $staged --fail-level critical
fi
```

## Information Commands

### `--list-rules`

Print all available rules with their severity and category.

```bash
promptlint --list-rules
```

### `--explain RULE_ID`

Print detailed documentation for a rule.

```bash
promptlint --explain prompt-injection
promptlint --explain pii-in-prompt
promptlint --explain output-length-missing
```

### `--version`

Print version and exit.

```bash
promptlint --version
```

## Message Array Input

PromptLint accepts OpenAI/Anthropic-style messages arrays directly as stdin or `--text` input. The content fields are concatenated and linted as a single prompt.

```bash
cat messages.json | promptlint
```

Where `messages.json` contains:
```json
[
  {"role": "system", "content": "You are a helpful assistant."},
  {"role": "user", "content": "Write a summary of the document."}
]
```

PromptLint joins the `content` values and lints the combined text.

## Complete Options Table

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--file` | `-f` | — | Prompt file path (glob supported) |
| `--text` | `-t` | — | Inline prompt text |
| `--format` | — | `text` | Output format: `text`, `json`, `sarif` |
| `--fix` | — | off | Auto-fix and print to stdout |
| `--show-dashboard` | — | off | Show cost savings dashboard |
| `--show-score` | — | off | Show health score (0-100) and grade |
| `--badge` | — | off | Output Shields.io badge URL |
| `--fail-level` | — | `critical` | Minimum severity for non-zero exit |
| `--config` | — | `.promptlintrc` | Config file path |
| `--init` | — | — | Create starter `.promptlintrc` |
| `--update-baseline` | — | off | Write findings to `.promptlintbaseline` |
| `--compare A B` | — | — | Compare two files by score |
| `--install-hooks` | — | — | Install pre-commit git hook |
| `--list-rules` | — | — | List all rules and exit |
| `--explain` | — | — | Explain a rule and exit |
| `--quiet` | `-q` | off | Suppress findings; summary only |
| `--exclude` | — | — | Glob pattern to exclude (repeatable) |
| `--version` | `-V` | — | Print version and exit |
| `--help` | `-h` | — | Show help |

## Common Recipes

```bash
# Lint everything under prompts/
promptlint "prompts/**/*.txt"

# CI — fail on any warning
promptlint "prompts/**/*.txt" --fail-level warn --format json

# Fix and review diff
promptlint prompt.txt --fix > fixed.txt && diff prompt.txt fixed.txt

# Get health score with badge URL
promptlint prompt.txt --show-score --badge

# Compare prompt versions
promptlint --compare prompt_v1.txt prompt_v2.txt

# Suppress known issues (brownfield adoption)
promptlint "prompts/**/*.txt" --update-baseline
promptlint "prompts/**/*.txt"  # only new issues

# Lint messages.json (API format)
cat messages.json | promptlint

# Pipe through jq for CI integration
promptlint "prompts/**/*.txt" --format json | jq '.findings[] | select(.level == "CRITICAL")'

# SARIF for GitHub Security tab
promptlint "prompts/**/*.txt" --format sarif > results.sarif
```
