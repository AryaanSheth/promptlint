"""
PromptLint Hotkey Service

A background service that monitors a global hotkey to trigger PromptLint
analysis on typed text in Cursor IDE.

Usage:
    # Run with system tray
    python -m promptlint.hotkey

    # Or import components
    from promptlint.hotkey import PromptLintService, show_results_dialog
"""

from .service import (
    PromptLintService,
    ServiceConfig,
    LintResult,
    ClipboardManager,
    WindowDetector,
    check_dependencies,
)
from .dialog import (
    show_notification,
    show_results_dialog,
    show_results_dialog_async,
    show_quick_popup,
    ResultsDialog,
    DialogResult,
)
from .tray import (
    TrayApplication,
    TraylessApplication,
    create_application,
)

__all__ = [
    # Service
    "PromptLintService",
    "ServiceConfig",
    "LintResult",
    "ClipboardManager",
    "WindowDetector",
    "check_dependencies",
    # Dialog
    "show_notification",
    "show_results_dialog",
    "show_results_dialog_async",
    "show_quick_popup",
    "ResultsDialog",
    "DialogResult",
    # Tray
    "TrayApplication",
    "TraylessApplication",
    "create_application",
]
