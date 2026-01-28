#!/usr/bin/env python3
"""
Entry point for running the hotkey service as a module.

Usage:
    python -m promptlint.hotkey
"""

from .tray import main

if __name__ == "__main__":
    main()
