# Installation

PromptLint is available through four distribution channels.

## Python CLI (pip)

The Python package provides the most accurate token counting via `tiktoken`.

```bash
pip install promptlint-cli
```

**Requirements:** Python ≥ 3.9

**Optional — exact token counts:**

```bash
pip install "promptlint-cli[tiktoken]"
```

Without `tiktoken`, token counts fall back to a character-based heuristic (±15%).

**Verify:**

```bash
promptlint --version
```

## Node.js CLI (npm)

```bash
npm install -g promptlint-cli
```

**Requirements:** Node.js ≥ 16

The Node package uses a character-based token heuristic (chars ÷ 4, ±15%). For exact counts install the Python package.

**Verify:**

```bash
promptlint --version
```

## GitHub Action

No installation needed — reference the action directly in your workflow:

```yaml
# .github/workflows/lint-prompts.yml
name: Lint Prompts

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AryaanSheth/promptlint@v1
        with:
          path: prompts/
          fail-level: warn
```

See the [GitHub Actions integration guide](/integrations/github-actions) for all options.

## VS Code Extension

1. Open VS Code
2. Press `Ctrl+Shift+X` (or `Cmd+Shift+X` on macOS)
3. Search **"PromptLint"**
4. Click **Install**

The extension provides:
- Real-time linting as you type
- Quick-fix suggestions in the editor
- Status bar indicator
- Configuration panel

## Upgrading

::: code-group

```bash [pip]
pip install --upgrade promptlint-cli
```

```bash [npm]
npm update -g promptlint-cli
```

:::

## Uninstalling

::: code-group

```bash [pip]
pip uninstall promptlint-cli
```

```bash [npm]
npm uninstall -g promptlint-cli
```

:::

## Verifying Your Install

```bash
# Check version
promptlint --version

# Run a quick sanity check
promptlint --text "Hello, world!"

# List all available rules
promptlint --list-rules
```
