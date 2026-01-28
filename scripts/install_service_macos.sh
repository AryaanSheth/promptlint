#!/bin/bash
# PromptLint Hotkey Service - macOS Installer
# This script installs the PromptLint service as a Launch Agent on macOS

set -e

echo "============================================"
echo "PromptLint Hotkey Service Installer (macOS)"
echo "============================================"
echo

# Check for Python
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from https://www.python.org/ or use Homebrew"
    exit 1
fi

PYTHON_PATH=$(which python3)
echo "Found Python: $PYTHON_PATH"
echo

# Get the project root directory (parent of scripts folder)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "Project directory: $PROJECT_DIR"
echo

echo "Installing required Python packages..."
pip3 install keyboard pyautogui pyperclip plyer pystray Pillow pyobjc-framework-Cocoa 2>/dev/null || {
    echo "WARNING: Some packages may require manual installation"
    echo "Try: pip3 install keyboard pyautogui pyperclip plyer pystray Pillow pyobjc-framework-Cocoa"
}

echo
echo "Creating Launch Agent..."

# Create LaunchAgent plist
PLIST_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$PLIST_DIR/com.promptlint.service.plist"

mkdir -p "$PLIST_DIR"

cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.promptlint.service</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>-m</string>
        <string>promptlint.hotkey</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/promptlint.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/promptlint.err</string>
</dict>
</plist>
EOF

echo "Launch Agent created at: $PLIST_FILE"
echo

# Load the Launch Agent
echo "Loading Launch Agent..."
launchctl unload "$PLIST_FILE" 2>/dev/null || true
launchctl load "$PLIST_FILE"

echo
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo
echo "The PromptLint service will now:"
echo "  - Start automatically when you log in"
echo "  - Listen for Ctrl+Shift+L hotkey in Cursor"
echo
echo "IMPORTANT: macOS requires accessibility permissions!"
echo "Go to System Preferences > Security & Privacy > Privacy > Accessibility"
echo "And add Terminal.app (or your terminal) and Python to the allowed list."
echo
echo "To manually start the service:"
echo "  python3 -m promptlint.hotkey"
echo
echo "To stop the service:"
echo "  launchctl stop com.promptlint.service"
echo
echo "To uninstall, run: ./uninstall_service_macos.sh"
echo
echo "Logs are written to /tmp/promptlint.log"
echo

read -p "Start the service now? (y/n): " START_NOW
if [ "$START_NOW" = "y" ] || [ "$START_NOW" = "Y" ]; then
    launchctl start com.promptlint.service
    echo "Service started!"
fi
