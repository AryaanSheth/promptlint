#!/bin/bash
# Install PromptLint Hotkey Service as a Launch Agent
# This will make it run automatically on login without needing a terminal window

set -e

PLIST_NAME="com.promptlint.hotkey.plist"
PLIST_SOURCE="/Users/ary/Documents/promptlint/scripts/$PLIST_NAME"
PLIST_DEST="$HOME/Library/LaunchAgents/$PLIST_NAME"

echo "📦 Installing PromptLint Hotkey Service..."
echo ""

# Stop any running instance
if launchctl list | grep -q "com.promptlint.hotkey"; then
    echo "⏹️  Stopping existing service..."
    launchctl unload "$PLIST_DEST" 2>/dev/null || true
fi

# Copy plist to LaunchAgents
echo "📋 Copying launch agent configuration..."
cp "$PLIST_SOURCE" "$PLIST_DEST"

# Load the launch agent
echo "🚀 Starting service..."
launchctl load "$PLIST_DEST"

echo ""
echo "✅ PromptLint Hotkey Service installed successfully!"
echo ""
echo "The service will now:"
echo "  • Run automatically on login"
echo "  • Run in the background (no terminal window)"
echo "  • Restart automatically if it crashes"
echo ""
echo "Hotkey: Cmd+Option+L"
echo ""
echo "📝 Logs are saved to:"
echo "  /Users/ary/Documents/promptlint/logs/hotkey-service.log"
echo ""
echo "To check if it's running:"
echo "  launchctl list | grep promptlint"
echo ""
echo "To uninstall:"
echo "  sh /Users/ary/Documents/promptlint/scripts/uninstall_launch_agent.sh"
