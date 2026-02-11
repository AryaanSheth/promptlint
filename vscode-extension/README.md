# PromptLint for VS Code & Cursor

Analyze and optimize AI prompts for quality, clarity, and cost-efficiency **BEFORE** sending them to LLMs.

## Features

✨ **Pre-Send Analysis** - Lint prompts before sending to save tokens and improve quality  
📊 **Real-time Token Count** - See token estimates in the status bar  
🔄 **One-Click Optimization** - Automatically fix common issues  
📝 **Detailed Findings** - View all issues with severity levels and suggestions  
⚡ **Fast** - Runs locally, no external API calls  
🎨 **Diff View** - Compare original vs optimized prompts side-by-side  

## Installation

### Option 1: From VSIX (Recommended)

1. Open VS Code or Cursor
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Install from VSIX" and select it
4. Navigate to `promptlint-1.0.0.vsix` and install

### Option 2: From Source

1. Clone or download the PromptLint repository
2. Navigate to the `vscode-extension` folder
3. Run:
   ```bash
   npm install
   code --install-extension .
   ```

### Prerequisites

- Python 3.9+ installed
- PromptLint Python package installed:
  ```bash
  pip install -r requirements.txt
  ```

## Usage

### Quick Start

1. **Select text** in your editor (or place cursor in prompt)
2. **Press `Cmd+Option+L`** (macOS) or **`Ctrl+Alt+L`** (Windows/Linux)
3. **View results** in the notification and output panel
4. **Choose action:**
   - Replace with Optimized
   - Show Diff
   - Copy Optimized

### Commands

- **PromptLint: Analyze Selection** - Analyze selected text and show findings
- **PromptLint: Optimize & Replace** - Analyze and directly replace with optimized version
- **PromptLint: Show Optimized Diff** - Show side-by-side comparison
- **PromptLint: Toggle Status Bar** - Show/hide token count

### Keyboard Shortcuts

| Command | macOS | Windows/Linux |
|---------|-------|---------------|
| Analyze Selection | `Cmd+Option+L` | `Ctrl+Alt+L` |
| Optimize & Replace | `Cmd+Shift+Option+L` | `Ctrl+Shift+Alt+L` |

### Context Menu

Right-click on selected text to access PromptLint commands:
- Analyze Selection
- Optimize & Replace  
- Show Optimized Diff

## Configuration

Access settings via `Preferences > Settings > PromptLint`:

| Setting | Default | Description |
|---------|---------|-------------|
| `promptlint.enabled` | `true` | Enable/disable PromptLint |
| `promptlint.showTokenCount` | `true` | Show token count in status bar |
| `promptlint.autoAnalyze` | `false` | Auto-analyze while typing (experimental) |
| `promptlint.pythonPath` | `python3` | Path to Python executable |
| `promptlint.promptlintPath` | (auto) | Path to PromptLint installation |
| `promptlint.showInfoLevel` | `true` | Show INFO level findings |

## What PromptLint Checks

### 🔴 Critical Issues
- **Prompt Injection** - Detects malicious patterns like "ignore previous instructions"

### ⚠️ Warnings
- **Politeness Bloat** - Unnecessary "please", "kindly", "thank you"
- **Vague Terms** - "some", "stuff", "things", "maybe"
- **Redundancy** - "due to the fact that" → "because"
- **Weak Verbs** - Suggests stronger alternatives
- **Missing Structure** - No clear Task/Context/Output sections

### ℹ️ Info
- **Token Cost** - Estimates API costs
- **Structure Recommendations** - Suggests using XML tags or markdown
- **Specificity** - Recommends adding constraints and examples

## Example

**Before (79 tokens):**
```
Please kindly write a function that does some stuff with various inputs. 
Maybe it could handle several edge cases, perhaps using appropriate error 
handling that would be nice and good. Thank you for implementing this due 
to the fact that it is important at this point in time.
```

**After (44 tokens, 44% reduction):**
```xml
<task>
Write a function that handles [specific inputs].
Must validate inputs and handle [specific edge cases] with error handling.
</task>
```

**Savings:** 35 tokens per call = $127.75/year @ 10 calls/day on GPT-4o

## Workflow for Cursor Users

### Recommended: Lint Before Sending

1. Type your prompt in Cursor chat
2. **Press `Cmd+Option+L` BEFORE hitting Enter**
3. Review findings
4. Click "Replace with Optimized"
5. Now send to Claude/GPT

This ensures you only send optimized prompts, saving tokens on every message!

## Troubleshooting

### "Command not found: python3"
- Install Python 3.9+ or update `promptlint.pythonPath` in settings

### "Module not found: promptlint"
- Ensure PromptLint is installed: `pip install -r requirements.txt`
- Or set `promptlint.promptlintPath` to your PromptLint directory

### "No output"
- Check the Output panel: `View > Output > PromptLint`
- Verify Python and PromptLint are working: `python3 -m promptlint.cli --version`

### Extension not loading
- Check Extensions panel for errors
- Reload VS Code: `Cmd+Shift+P` > "Reload Window"

## Contributing

Found a bug or have a feature request? Open an issue on [GitHub](https://github.com/yourusername/promptlint).

## License

MIT - See LICENSE file for details

## Credits

Created to help developers write better AI prompts and save on API costs.

---

**Happy prompting! 🚀**
