#!/bin/bash
# Wrapper script for PromptLint Hotkey Service
# This helps with macOS permissions when running from Launch Agent

cd /Users/ary/Documents/promptlint
exec /usr/bin/python3 /Users/ary/Documents/promptlint/run_cursor_hotkey.py
