# PromptLint Cursor Hotkey Integration Guide

This guide explains how to set up and use the PromptLint hotkey service for seamless prompt linting directly in Cursor IDE.

## Overview

The PromptLint hotkey service provides a non-blocking way to lint your prompts before sending them to AI:

1. Type your prompt in Cursor chat
2. Press **Ctrl+Shift+L** (before hitting Enter)
3. View findings and choose to use the optimized version or keep original
4. Continue chatting normally

This is completely **opt-in per message** - you can always just press Enter to send without linting.

## Quick Start

### Installation

```bash
# Install PromptLint with hotkey service dependencies
pip install promptlint keyboard pyautogui pyperclip plyer pystray Pillow
```

### Platform-Specific Setup

<details>
<summary><strong>macOS</strong></summary>

1. Install additional macOS dependencies:
   ```bash
   pip install pyobjc-framework-Cocoa
   ```

2. **Grant Accessibility Permissions** (Required!):
   - Go to **System Preferences** → **Security & Privacy** → **Privacy** → **Accessibility**
   - Click the lock icon to make changes
   - Add and enable **Terminal.app** (or your terminal application)
   - Add and enable **Python** (usually at `/usr/local/bin/python3` or similar)

3. Run the installer:
   ```bash
   cd promptlint/scripts
   chmod +x install_service_macos.sh
   ./install_service_macos.sh
   ```

4. The service will now start automatically on login.

</details>

<details>
<summary><strong>Windows</strong></summary>

1. Install additional Windows dependencies:
   ```bash
   pip install pywin32 psutil
   ```

2. Run the installer (as Administrator for best results):
   ```batch
   cd promptlint\scripts
   install_service.bat
   ```

3. The service will now start automatically on Windows startup.

</details>

<details>
<summary><strong>Linux</strong></summary>

1. Install system dependencies:
   ```bash
   # Debian/Ubuntu
   sudo apt install xdotool libnotify-bin
   
   # Fedora
   sudo dnf install xdotool libnotify
   ```

2. Run the service manually:
   ```bash
   python -m promptlint.hotkey
   ```

3. Add to your desktop environment's startup applications for auto-start.

</details>

### Manual Start

If you prefer not to use auto-start, you can run the service manually:

```bash
# With system tray icon (recommended)
python -m promptlint.hotkey

# Or import and use programmatically
from promptlint.hotkey import PromptLintService
service = PromptLintService()
service.run_forever()
```

## Usage

### Basic Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. Type your prompt in Cursor chat                     │
│                                                         │
│  2. Press Ctrl+Shift+L (before pressing Enter)          │
│     ↓                                                   │
│  3. Service captures your text automatically            │
│     ↓                                                   │
│  4. PromptLint analyzes and shows results               │
│     ↓                                                   │
│  5. Choose action:                                      │
│     • "Use Fixed" → Optimized text copied to clipboard  │
│     • "Keep Original" → Nothing changes                 │
│     • "Cancel" → Dismiss and continue editing           │
│     ↓                                                   │
│  6. If "Use Fixed": Press Ctrl+V then Enter             │
│     Otherwise: Just press Enter (or keep editing)       │
└─────────────────────────────────────────────────────────┘
```

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| `Ctrl+Shift+L` | Trigger PromptLint analysis (in Cursor) |
| `Ctrl+V` | Paste fixed prompt (after selecting "Use Fixed") |
| `Enter` | Send message normally (with or without linting) |

### Results Dialog

When PromptLint finds issues, you'll see:

1. **Summary Header**: Issue count by severity (critical, warnings, info)
2. **Token Savings**: How many tokens you'll save with the optimized version
3. **Tabs**:
   - **Findings**: Detailed list of all issues found
   - **Fixed Prompt**: The optimized prompt text
   - **Compare**: Side-by-side view of original vs fixed

### Action Buttons

| Button | Description |
|--------|-------------|
| **Use Fixed** | Copies optimized prompt to clipboard, ready to paste |
| **Keep Original** | Dismisses dialog, your original text is preserved |
| **Cancel** | Closes dialog, continue editing |

## Configuration

### Service Configuration

Edit `promptlint/hotkey/config.json`:

```json
{
  "hotkey": "ctrl+shift+l",      // Hotkey combination
  "auto_copy": true,             // Automatically select and copy text
  "show_info_level": true,       // Show INFO-level findings
  "notification_duration": 10,   // Toast notification duration (seconds)
  "promptlint_path": "python -m promptlint.cli",
  "verify_cursor_active": true,  // Only activate when Cursor is focused
  "min_text_length": 5,          // Minimum text length to lint
  "max_text_length": 10000,      // Maximum text length to lint
  "copy_delay_ms": 100,          // Delay after copy command
  "selection_delay_ms": 50       // Delay after select-all command
}
```

### Custom Hotkey

Change the `hotkey` field to use a different key combination:

```json
{
  "hotkey": "ctrl+alt+p"
}
```

Supported modifiers: `ctrl`, `alt`, `shift`, `cmd` (macOS only)

### PromptLint Configuration

The service uses your existing `.promptlintrc` file for linting rules. See the main PromptLint documentation for rule configuration.

## System Tray

When running with the tray application, you'll see a "PL" icon in your system tray.

**Right-click menu options:**
- **Status**: Shows last lint time
- **Enabled/Disabled**: Toggle monitoring on/off
- **Hotkey**: Shows current hotkey
- **View History**: See recent lint results
- **Settings**: Open configuration
- **Exit**: Stop the service

**Icon colors:**
- 🟢 Green: Service enabled and ready
- ⚫ Gray: Service disabled

## Troubleshooting

### Hotkey Not Working

1. **Check if service is running**: Look for the tray icon or check terminal output
2. **Verify Cursor is focused**: The hotkey only works when Cursor is the active window
3. **Check accessibility permissions** (macOS): The service needs permission to simulate keyboard events
4. **Run as Administrator** (Windows): Some keyboard hooks require elevated privileges

### Text Not Being Captured

1. **Increase delays**: Edit config to increase `selection_delay_ms` and `copy_delay_ms`
2. **Check cursor position**: Make sure your cursor is in the chat input field
3. **Disable auto_copy**: Set `"auto_copy": false` and manually select text before pressing the hotkey

### Service Crashes

1. **Check logs**:
   - macOS: `/tmp/promptlint.log` and `/tmp/promptlint.err`
   - Windows: Check console output
2. **Run in console mode** for debugging:
   ```bash
   python -m promptlint.promptlint_service
   ```

### Missing Dependencies

Install all required packages:

```bash
# All platforms
pip install keyboard pyautogui pyperclip plyer pystray Pillow

# macOS additional
pip install pyobjc-framework-Cocoa

# Windows additional  
pip install pywin32 psutil
```

## Uninstallation

### macOS
```bash
cd promptlint/scripts
./uninstall_service_macos.sh
```

### Windows
```batch
cd promptlint\scripts
uninstall_service.bat
```

### Manual
1. Remove from startup applications
2. Kill any running processes
3. Optionally uninstall packages:
   ```bash
   pip uninstall keyboard pyautogui pyperclip plyer pystray Pillow
   ```

## Privacy & Security

- **Local only**: All processing happens on your machine
- **No data transmission**: PromptLint doesn't send your prompts anywhere
- **User-triggered**: Text is only captured when you press the hotkey
- **Clipboard safety**: Original clipboard content is backed up and can be restored
- **Open source**: Full source code available for audit

## Performance

- **Memory**: ~20-30 MB when idle
- **CPU**: Negligible (< 1% when waiting)
- **Latency**: 
  - Hotkey detection: < 1ms
  - Text capture: ~150ms
  - Linting: 500-2000ms depending on text length
  - **Total**: 1-2.5 seconds from hotkey to results

## Known Limitations

1. **Window focus required**: Only works when Cursor is the active window
2. **Clipboard modification**: Temporarily uses clipboard for text capture
3. **macOS permissions**: Requires explicit accessibility permissions
4. **Cannot intercept Enter**: By design - you maintain full control over sending
5. **Single application**: Designed specifically for Cursor IDE

## Getting Help

- Check the [PromptLint documentation](docs/)
- File issues on GitHub
- Review source code in `promptlint/hotkey/` directory
