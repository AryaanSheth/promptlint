# Exit Codes

PromptLint uses exit codes to communicate results to CI/CD pipelines.

## Code Reference

| Code | Meaning |
|:----:|---------|
| `0` | Clean — no findings at or above `--fail-level` |
| `1` | WARN-level findings detected |
| `2` | CRITICAL-level findings detected |

## `--fail-level` Mapping

| `--fail-level` | Exit 0 when | Exit 1 when | Exit 2 when |
|----------------|-------------|-------------|-------------|
| `critical` (default) | No CRITICAL findings | — | CRITICAL findings present |
| `warn` | No WARN or CRITICAL findings | WARN findings present | CRITICAL findings present |
| `info` | No findings at all | Any finding present | CRITICAL findings present |
| `none` | Always | Never | Never |

## Examples

```bash
# Default: fail only on CRITICAL
promptlint --file prompt.txt
echo $?  # 0 (clean), 1 (warn only), or 2 (critical)

# Strict: fail on any warning
promptlint --file prompt.txt --fail-level warn
echo $?  # 0 (clean), 1 (warn+), or 2 (critical)

# Informational: fail on any finding
promptlint --file prompt.txt --fail-level info
echo $?  # 0 (clean) or 1 (any finding)

# Never fail (report only)
promptlint --file prompt.txt --fail-level none
echo $?  # always 0
```

## In Shell Scripts

```bash
#!/bin/bash
set -e

promptlint --file prompt.txt --fail-level warn
# Script stops here if exit code != 0
echo "Prompt passed all checks"
```

## In Makefiles

```makefile
lint-prompts:
	promptlint --file "prompts/**/*.txt" --fail-level warn

.PHONY: lint-prompts
```

## In GitHub Actions

```yaml
- name: Lint prompts
  run: promptlint --file "prompts/**/*.txt" --fail-level warn
  # Step fails if exit code != 0
```

Or use the dedicated action which maps exit codes to annotations:

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
    fail-level: warn
```
