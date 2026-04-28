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

### `--no-color`

Disable ANSI color codes (useful for logging).

```bash
promptlint --file prompt.txt --no-color
```

## Fix Options

### `--fix`

Apply auto-fixes and print the optimized prompt to stdout.

```bash
promptlint --file prompt.txt --fix
promptlint --file prompt.txt --fix > prompt_fixed.txt
```

See the [Auto-Fix guide](/guide/auto-fix) for details.

## Exit Code Options

### `--fail-level LEVEL`

**Values:** `critical` (default), `warn`, `info`, `none`

Set the minimum severity that causes a non-zero exit code.

```bash
promptlint --file prompt.txt --fail-level warn   # exit 1 on WARN+
promptlint --file prompt.txt --fail-level info   # exit 1 on any finding
promptlint --file prompt.txt --fail-level none   # always exit 0
```

## Configuration Options

### `--config PATH`

Use a specific config file instead of searching for `.promptlintrc`.

```bash
promptlint --file prompt.txt --config /path/to/security.yaml
```

### `--rule RULE_ID`

Run only a specific rule.

```bash
promptlint --file prompt.txt --rule prompt-injection
promptlint --file prompt.txt --rule cost
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
```

### `--version`

Print version and exit.

```bash
promptlint --version
# PromptLint v1.3.0
```

## Complete Options Table

| Option | Short | Default | Description |
|--------|-------|---------|-------------|
| `--file` | `-f` | — | Prompt file path (glob supported) |
| `--text` | `-t` | — | Inline prompt text |
| `--format` | — | `text` | Output format: `text`, `json`, `sarif` |
| `--fix` | — | off | Auto-fix and print to stdout |
| `--show-dashboard` | — | off | Show cost savings dashboard |
| `--fail-level` | — | `critical` | Minimum severity for non-zero exit |
| `--config` | — | `.promptlintrc` | Config file path |
| `--rule` | — | all | Run only this rule |
| `--no-color` | — | off | Disable ANSI color |
| `--list-rules` | — | — | List all rules and exit |
| `--explain` | — | — | Explain a rule and exit |
| `--version` | — | — | Print version and exit |

## Common Recipes

```bash
# Lint everything under prompts/
promptlint --file "prompts/**/*.txt"

# CI — fail on any warning
promptlint --file "prompts/**/*.txt" --fail-level warn --format json

# Fix and review diff
promptlint --file prompt.txt --fix > fixed.txt && diff prompt.txt fixed.txt

# Security-only scan
promptlint --file prompt.txt --rule prompt-injection
promptlint --file prompt.txt --rule pii-in-prompt

# Pipe through jq for CI integration
promptlint --file "prompts/**/*.txt" --format json | jq '.findings[] | select(.level == "CRITICAL")'

# SARIF for GitHub Security tab
promptlint --file "prompts/**/*.txt" --format sarif > results.sarif
```
