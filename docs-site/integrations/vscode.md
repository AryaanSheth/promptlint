# VS Code Extension

PromptLint's VS Code extension provides real-time linting as you type.

## Installation

1. Open VS Code
2. Press `Ctrl+Shift+X` (macOS: `Cmd+Shift+X`)
3. Search **"PromptLint"**
4. Click **Install**

Or install from the command line:

```bash
code --install-extension AryaanSheth.promptlint
```

## Features

- **Real-time linting** — Findings appear as squiggly underlines as you type
- **Hover details** — Hover over underlined text for the full finding message
- **Quick fixes** — Click the lightbulb (or `Ctrl+.`) to apply auto-fixes
- **Status bar** — Shows pass/fail status and finding count
- **Config panel** — Edit `.promptlintrc` settings from a GUI panel

## Supported File Types

The extension activates on:
- `.txt`
- `.md` / `.mdx`
- `.prompt`
- `.promptlintrc`

## Quick Fixes

For auto-fixable rules, the quick fix menu offers:
- **Fix this finding** — Apply the fix for a single occurrence
- **Fix all in file** — Apply all auto-fixes in the current file

## Settings

Configure via VS Code settings (`Ctrl+,`):

| Setting | Default | Description |
|---------|---------|-------------|
| `promptlint.enable` | `true` | Enable/disable extension |
| `promptlint.configPath` | `.promptlintrc` | Path to config file |
| `promptlint.lintOnSave` | `true` | Re-lint on save |
| `promptlint.lintOnType` | `true` | Re-lint as you type (debounced) |
| `promptlint.failLevel` | `critical` | Minimum severity to show |

## Workspace Config

Add to `.vscode/settings.json`:

```json
{
  "promptlint.enable": true,
  "promptlint.failLevel": "warn",
  "promptlint.configPath": ".promptlintrc"
}
```

## Keyboard Shortcuts

| Action | Shortcut |
|--------|---------|
| Fix all in file | `Ctrl+Shift+P` → "PromptLint: Fix All" |
| Show dashboard | `Ctrl+Shift+P` → "PromptLint: Show Dashboard" |
| Toggle linting | `Ctrl+Shift+P` → "PromptLint: Toggle" |

## Tasks Integration

Add a lint task to `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "Lint Prompts",
      "type": "shell",
      "command": "promptlint",
      "args": ["--file", "${workspaceFolder}/prompts/**/*.txt", "--fail-level", "warn"],
      "group": "test",
      "problemMatcher": {
        "owner": "promptlint",
        "fileLocation": ["relative", "${workspaceFolder}"],
        "pattern": {
          "regexp": "^\\[ (CRITICAL|WARN|INFO) \\] (\\S+) \\(line (\\d+)\\) (.+)$",
          "severity": 1,
          "code": 2,
          "line": 3,
          "message": 4
        }
      }
    }
  ]
}
```
