# Pre-commit Hooks

Lint prompts automatically before each git commit.

## Setup

Install the pre-commit framework:

```bash
pip install pre-commit
```

Add to `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: promptlint
        name: PromptLint
        entry: promptlint
        args: [--fail-level, warn]
        language: system
        files: \.(txt|md|prompt)$
        pass_filenames: true
```

Install the hooks:

```bash
pre-commit install
```

## How It Works

On `git commit`, pre-commit runs PromptLint against all staged files matching the `files` pattern. If any finding exceeds `--fail-level`, the commit is blocked with an error message.

## Custom Config per Hook

```yaml
repos:
  - repo: local
    hooks:
      - id: promptlint-security
        name: PromptLint Security
        entry: promptlint
        args: [--config, .promptlintrc.security, --fail-level, critical]
        language: system
        files: prompts/.*\.(txt|md)$
        pass_filenames: true
```

## Manual Run

```bash
# Run on all files (not just staged)
pre-commit run promptlint --all-files

# Run on specific files
pre-commit run promptlint --files prompts/system.txt
```

## Git Hook (Without pre-commit Framework)

If you prefer a raw git hook, add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
set -e

# Find staged .txt and .md files
STAGED=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(txt|md|prompt)$' || true)

if [ -n "$STAGED" ]; then
  echo "Running PromptLint on staged prompt files..."
  for file in $STAGED; do
    promptlint --file "$file" --fail-level warn
  done
fi
```

Make it executable:

```bash
chmod +x .git/hooks/pre-commit
```

::: tip
The pre-commit framework approach is preferred because it's committed to the repo and works for all contributors automatically.
:::
