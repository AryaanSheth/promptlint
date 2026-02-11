#!/bin/bash
# Uninstall PromptLint Hotkey Service Launch Agent

set -e

PLIST_NAME="com.promptlint.hotkey.plist"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "🗑️  Uninstalling PromptLint Hotkey Service..."
echo ""

# Stop the service
if launchctl list | grep -q "com.promptlint.hotkey"; then
    echo "⏹️  Stopping service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Remove plist
if [ -f "$PLIST_DEST" ]; then
    echo "📋 Removing launch agent configuration..."
    rm "$PLIST_DEST"
fi

echo ""
echo "✅ PromptLint Hotkey Service uninstalled successfully!"
echo ""
echo "To reinstall:"
echo "  sh /Users/ary/Documents/promptlint/scripts/install_launch_agent.sh"
