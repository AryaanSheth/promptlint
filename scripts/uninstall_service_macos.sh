#!/bin/bash
# PromptLint Hotkey Service - macOS Uninstaller
# This script removes the PromptLint service Launch Agent from macOS

echo "============================================"
echo "PromptLint Hotkey Service Uninstaller (macOS)"
echo "============================================"
echo

PLIST_FILE="$HOME/Library/LaunchAgents/com.promptlint.service.plist"

# Stop and unload the service
if [ -f "$PLIST_FILE" ]; then
    echo "Stopping service..."
    launchctl stop com.promptlint.service 2>/dev/null || true
    
    echo "Unloading Launch Agent..."
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
    
    echo "Removing plist file..."
    rm -f "$PLIST_FILE"
    
    echo "Launch Agent removed."
else
    echo "No Launch Agent found."
fi

# Clean up log files
echo "Cleaning up log files..."
rm -f /tmp/promptlint.log /tmp/promptlint.err 2>/dev/null || true

echo
echo "============================================"
echo "Uninstallation Complete!"
echo "============================================"
echo
echo "PromptLint service has been removed from startup."
echo "The Python packages have NOT been uninstalled."
echo
echo "To completely remove, you can also run:"
echo "  pip3 uninstall keyboard pyautogui pyperclip plyer pystray Pillow pyobjc-framework-Cocoa"
echo
