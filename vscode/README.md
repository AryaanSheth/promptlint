# PromptLint VS Code Extension

A VS Code extension that runs the [PromptLint CLI](../cli/) to surface diagnostics, quick fixes, and token cost information for LLM prompts directly in your editor.

## Features

- **Real-time diagnostics** — squiggly underlines for prompt injection, vague terms, missing structure, politeness bloat, and more
- **Quick fixes** — one-click auto-fix for fixable rules (politeness-bloat, verbosity-redundancy, structure-sections, prompt-injection)
- **Inline disable** — add `# promptlint-disable <rule>` comments from the lightbulb menu
- **Token & cost status bar** — live token count and cost-per-call in the bottom status bar
- **Dashboard** — view token savings breakdown from the command palette
- **Magic comment markers** — lint prompt regions inside `.py`, `.ts`, `.js` files using `# promptlint-start` / `# promptlint-end`

## Requirements

- Python 3.8+
- `promptlint-cli` installed: `pip install promptlint-cli`

The extension will prompt you to install the CLI if it is not found.

## Supported File Types

| File type | Behavior |
|-----------|----------|
| `.txt`, `.md`, `.prompt` | Entire file is linted |
| `.py`, `.ts`, `.js`, etc. | Only `promptlint-start` / `promptlint-end` regions are linted |

### Magic Comment Markers

Wrap prompt strings in code files with markers:

```python
# promptlint-start
SYSTEM_PROMPT = """
You are a helpful assistant that summarizes articles.
"""
# promptlint-end
```

```typescript
// promptlint-start
const prompt = `You are a helpful assistant.`;
// promptlint-end
```

## Extension Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `promptlint.pythonPath` | `"python"` | Python interpreter path |
| `promptlint.lintOnSave` | `true` | Lint when a file is saved |
| `promptlint.lintOnType` | `false` | Lint as you type (debounced) |
| `promptlint.lintOnTypeDelay` | `500` | Debounce delay in ms |
| `promptlint.languages` | `["plaintext","markdown",...]` | VS Code language IDs to activate on |
| `promptlint.configPath` | `""` | Explicit path to `.promptlintrc` |
| `promptlint.failLevel` | `"critical"` | Severity threshold (`none`, `warn`, `critical`) |
| `promptlint.showStatusBar` | `true` | Show token/cost status bar |

## Commands

| Command | Description |
|---------|-------------|
| `PromptLint: Lint File` | Lint the active file |
| `PromptLint: Fix File` | Apply all auto-fixes |
| `PromptLint: Show Dashboard` | Token savings breakdown |
| `PromptLint: Explain Rule` | Pick a rule and see its explanation |
| `PromptLint: Initialize Config` | Generate `.promptlintrc` in workspace |

## Development

```bash
cd vscode
npm install
npm run compile
```

To test locally, press **F5** in VS Code to launch the Extension Development Host.
