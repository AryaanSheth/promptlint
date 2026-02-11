# PromptLint Extension Installation Guide

## Quick Install (Recommended)

### Step 1: Install Dependencies

```bash
cd /Users/ary/Documents/promptlint/vscode-extension
npm install
```

### Step 2: Package the Extension

```bash
npx vsce package
```

This creates `promptlint-1.0.0.vsix`

### Step 3: Install in Cursor/VS Code

**Option A: Via Command Palette**
1. Open Cursor or VS Code
2. Press `Cmd+Shift+P` (macOS) or `Ctrl+Shift+P` (Windows/Linux)
3. Type "Install from VSIX"
4. Select `promptlint-1.0.0.vsix`
5. Reload the window when prompted

**Option B: Via Command Line**
```bash
# For VS Code
code --install-extension promptlint-1.0.0.vsix

# For Cursor
cursor --install-extension promptlint-1.0.0.vsix
```

### Step 4: Configure

1. Open Settings (`Cmd+,` or `Ctrl+,`)
2. Search for "PromptLint"
3. Set `promptlint.promptlintPath` to: `/Users/ary/Documents/promptlint`
4. Verify `promptlint.pythonPath` is set to `python3`

### Step 5: Test

1. Create a new file or open Cursor chat
2. Type: `Please kindly help me write some code. Thank you!`
3. Select the text
4. Press `Cmd+Option+L` (macOS) or `Ctrl+Alt+L` (Windows/Linux)
5. You should see PromptLint analysis results!

## Development Setup

If you want to develop or debug the extension:

### Step 1: Open in VS Code

```bash
cd /Users/ary/Documents/promptlint/vscode-extension
code .
```

### Step 2: Install Dependencies

```bash
npm install
```

### Step 3: Run Extension (Debug Mode)

1. Press `F5` or go to Run > Start Debugging
2. A new VS Code window opens with the extension loaded
3. Test the extension in this window
4. View logs in the Debug Console

### Step 4: Make Changes

1. Edit `extension.js` or `package.json`
2. Save files
3. In the debug window: `Cmd+R` to reload
4. Test your changes

## Troubleshooting

### Extension doesn't load
- Check Developer Tools: `Help > Toggle Developer Tools`
- Look for errors in the Console tab

### Commands not working
- Verify the extension is enabled: Extensions panel, search "PromptLint"
- Reload window: `Cmd+Shift+P` > "Reload Window"

### PromptLint not found
- Ensure PromptLint Python module is installed:
  ```bash
  cd /Users/ary/Documents/promptlint
  python3 -m promptlint.cli --version
  ```
- Set correct path in settings

### Status bar not showing
- Enable in settings: `promptlint.showTokenCount = true`
- Or run command: "PromptLint: Toggle Status Bar"

## Uninstall

1. Open Extensions panel (`Cmd+Shift+X`)
2. Search for "PromptLint"
3. Click gear icon > Uninstall

---

**Need help?** Open an issue on GitHub or check the README.md
