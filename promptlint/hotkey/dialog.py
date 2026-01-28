#!/usr/bin/env python3
"""
PromptLint Dialog System

Provides notification and results UI for PromptLint hotkey service.
Supports both quick toast notifications and detailed dialog windows.
"""

from __future__ import annotations

import platform
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from typing import TYPE_CHECKING, Optional, Callable
from dataclasses import dataclass

if TYPE_CHECKING:
    from .service import LintResult

# Platform detection
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == "windows"
IS_MACOS = PLATFORM == "darwin"
IS_LINUX = PLATFORM == "linux"

# Optional notification library
try:
    from plyer import notification as plyer_notification
    PLYER_AVAILABLE = True
except ImportError:
    PLYER_AVAILABLE = False


@dataclass
class DialogResult:
    """Result of user interaction with dialog."""
    action: str  # "use_fixed", "keep_original", "cancel"
    text: Optional[str] = None


def show_notification(
    title: str,
    message: str,
    duration: int = 10,
    on_click: Optional[Callable] = None,
) -> None:
    """
    Show a system notification.
    
    Args:
        title: Notification title
        message: Notification message
        duration: Duration in seconds
        on_click: Callback when notification is clicked
    """
    try:
        if PLYER_AVAILABLE:
            plyer_notification.notify(
                title=title,
                message=message,
                timeout=duration,
                app_name="PromptLint"
            )
        elif IS_MACOS:
            # Use osascript for macOS notifications
            script = f'''
            display notification "{message}" with title "{title}"
            '''
            subprocess.run(["osascript", "-e", script], capture_output=True)
        elif IS_LINUX:
            # Use notify-send on Linux
            subprocess.run(
                ["notify-send", title, message, f"--expire-time={duration * 1000}"],
                capture_output=True
            )
        elif IS_WINDOWS:
            # Fallback Windows notification using PowerShell
            script = f'''
            [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null
            $template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
            $textNodes = $template.GetElementsByTagName("text")
            $textNodes.Item(0).AppendChild($template.CreateTextNode("{title}"))
            $textNodes.Item(1).AppendChild($template.CreateTextNode("{message}"))
            $toast = [Windows.UI.Notifications.ToastNotification]::new($template)
            [Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier("PromptLint").Show($toast)
            '''
            subprocess.run(["powershell", "-Command", script], capture_output=True)
    except Exception as e:
        print(f"Notification failed: {e}")


class ResultsDialog:
    """
    Detailed results dialog for PromptLint findings.
    
    Provides a tabbed interface showing:
    - Summary of findings
    - All findings with details
    - Fixed/optimized prompt
    - Side-by-side comparison
    """
    
    def __init__(self, result: "LintResult"):
        self.result = result
        self.dialog_result: Optional[DialogResult] = None
        self.root: Optional[tk.Tk] = None
    
    def show(self) -> DialogResult:
        """Show the dialog and return user's choice."""
        self.root = tk.Tk()
        self.root.title("PromptLint Results")
        self.root.geometry("800x600")
        self.root.minsize(600, 400)
        
        # Configure style
        style = ttk.Style()
        style.theme_use("clam" if not IS_WINDOWS else "vista")
        
        # Create main container
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Summary header
        self._create_summary_header(main_frame)
        
        # Notebook for tabs
        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # Create tabs
        self._create_findings_tab(notebook)
        if self.result.optimized_prompt:
            self._create_fixed_tab(notebook)
            self._create_comparison_tab(notebook)
        
        # Action buttons
        self._create_action_buttons(main_frame)
        
        # Handle window close
        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)
        
        # Center window
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() - self.root.winfo_width()) // 2
        y = (self.root.winfo_screenheight() - self.root.winfo_height()) // 2
        self.root.geometry(f"+{x}+{y}")
        
        # Run dialog
        self.root.mainloop()
        
        return self.dialog_result or DialogResult(action="cancel")
    
    def _create_summary_header(self, parent: ttk.Frame) -> None:
        """Create the summary header section."""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        # Title with icon based on severity
        if self.result.critical_count > 0:
            icon = "!"
            color = "#e74c3c"
        elif self.result.warning_count > 0:
            icon = "!"
            color = "#f39c12"
        else:
            icon = "i"
            color = "#27ae60"
        
        title_label = ttk.Label(
            header_frame,
            text=f"[{icon}] {self.result.summary}",
            font=("Helvetica", 14, "bold")
        )
        title_label.pack(anchor=tk.W)
        
        # Token savings if available
        if self.result.dashboard:
            savings_text = (
                f"Tokens: {self.result.dashboard.get('current_tokens', 0)} -> "
                f"{self.result.dashboard.get('optimized_tokens', 0)} "
                f"({self.result.dashboard.get('tokens_saved', 0)} saved, "
                f"{self.result.dashboard.get('reduction_percentage', 0):.1f}% reduction)"
            )
            savings_label = ttk.Label(
                header_frame,
                text=savings_text,
                font=("Helvetica", 10)
            )
            savings_label.pack(anchor=tk.W, pady=(5, 0))
    
    def _create_findings_tab(self, notebook: ttk.Notebook) -> None:
        """Create the findings tab."""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text=f"Findings ({self.result.issue_count})")
        
        # Scrollable list of findings
        canvas = tk.Canvas(frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor=tk.NW)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # Populate findings
        level_colors = {
            "CRITICAL": "#e74c3c",
            "WARN": "#f39c12",
            "INFO": "#3498db"
        }
        
        for i, finding in enumerate(self.result.findings):
            finding_frame = ttk.Frame(scrollable_frame, padding="5")
            finding_frame.pack(fill=tk.X, pady=2)
            
            level = finding.get("level", "INFO")
            color = level_colors.get(level, "#95a5a6")
            
            # Level badge
            level_label = tk.Label(
                finding_frame,
                text=f" {level} ",
                bg=color,
                fg="white",
                font=("Helvetica", 9, "bold")
            )
            level_label.pack(side=tk.LEFT, padx=(0, 10))
            
            # Rule and message
            info_frame = ttk.Frame(finding_frame)
            info_frame.pack(side=tk.LEFT, fill=tk.X, expand=True)
            
            rule = finding.get("rule", "unknown")
            message = finding.get("message", "No message")
            line = finding.get("line", "-")
            
            rule_label = ttk.Label(
                info_frame,
                text=f"{rule} (line {line})",
                font=("Helvetica", 10, "bold")
            )
            rule_label.pack(anchor=tk.W)
            
            message_label = ttk.Label(
                info_frame,
                text=message,
                wraplength=600
            )
            message_label.pack(anchor=tk.W)
            
            # Context if available
            context = finding.get("context")
            if context:
                context_label = ttk.Label(
                    info_frame,
                    text=context,
                    font=("Courier", 9),
                    foreground="#666666"
                )
                context_label.pack(anchor=tk.W, pady=(5, 0))
        
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def _create_fixed_tab(self, notebook: ttk.Notebook) -> None:
        """Create the fixed prompt tab."""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Fixed Prompt")
        
        # Text area with fixed prompt
        text_area = scrolledtext.ScrolledText(
            frame,
            wrap=tk.WORD,
            font=("Courier", 11),
            height=20
        )
        text_area.pack(fill=tk.BOTH, expand=True)
        text_area.insert(tk.END, self.result.optimized_prompt or "")
        text_area.configure(state=tk.DISABLED)
        
        # Copy button
        copy_btn = ttk.Button(
            frame,
            text="Copy to Clipboard",
            command=lambda: self._copy_to_clipboard(self.result.optimized_prompt)
        )
        copy_btn.pack(pady=(10, 0))
    
    def _create_comparison_tab(self, notebook: ttk.Notebook) -> None:
        """Create the side-by-side comparison tab."""
        frame = ttk.Frame(notebook, padding="10")
        notebook.add(frame, text="Compare")
        
        # Split view
        paned = ttk.PanedWindow(frame, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True)
        
        # Original
        original_frame = ttk.LabelFrame(paned, text="Original", padding="5")
        original_text = scrolledtext.ScrolledText(
            original_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            height=15,
            width=40
        )
        original_text.pack(fill=tk.BOTH, expand=True)
        original_text.insert(tk.END, self.result.original_text)
        original_text.configure(state=tk.DISABLED)
        paned.add(original_frame, weight=1)
        
        # Fixed
        fixed_frame = ttk.LabelFrame(paned, text="Fixed", padding="5")
        fixed_text = scrolledtext.ScrolledText(
            fixed_frame,
            wrap=tk.WORD,
            font=("Courier", 10),
            height=15,
            width=40
        )
        fixed_text.pack(fill=tk.BOTH, expand=True)
        fixed_text.insert(tk.END, self.result.optimized_prompt or "")
        fixed_text.configure(state=tk.DISABLED)
        paned.add(fixed_frame, weight=1)
    
    def _create_action_buttons(self, parent: ttk.Frame) -> None:
        """Create the action buttons."""
        btn_frame = ttk.Frame(parent)
        btn_frame.pack(fill=tk.X, pady=(10, 0))
        
        # Use Fixed button (primary action)
        if self.result.optimized_prompt:
            use_fixed_btn = ttk.Button(
                btn_frame,
                text="Use Fixed (Copy to Clipboard)",
                command=self._on_use_fixed,
                style="Accent.TButton"
            )
            use_fixed_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Keep Original button
        keep_original_btn = ttk.Button(
            btn_frame,
            text="Keep Original",
            command=self._on_keep_original
        )
        keep_original_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # Cancel button
        cancel_btn = ttk.Button(
            btn_frame,
            text="Cancel",
            command=self._on_cancel
        )
        cancel_btn.pack(side=tk.RIGHT)
    
    def _copy_to_clipboard(self, text: Optional[str]) -> None:
        """Copy text to clipboard."""
        if text and self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            messagebox.showinfo("Copied", "Text copied to clipboard!")
    
    def _on_use_fixed(self) -> None:
        """Handle 'Use Fixed' button click."""
        if self.result.optimized_prompt and self.root:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.result.optimized_prompt)
        
        self.dialog_result = DialogResult(
            action="use_fixed",
            text=self.result.optimized_prompt
        )
        if self.root:
            self.root.destroy()
    
    def _on_keep_original(self) -> None:
        """Handle 'Keep Original' button click."""
        self.dialog_result = DialogResult(
            action="keep_original",
            text=self.result.original_text
        )
        if self.root:
            self.root.destroy()
    
    def _on_cancel(self) -> None:
        """Handle cancel/close."""
        self.dialog_result = DialogResult(action="cancel")
        if self.root:
            self.root.destroy()


def show_results_dialog(result: "LintResult") -> DialogResult:
    """
    Show the results dialog and return user's choice.
    
    Args:
        result: LintResult from PromptLint analysis
        
    Returns:
        DialogResult with user's action choice
    """
    dialog = ResultsDialog(result)
    return dialog.show()


def show_results_dialog_async(
    result: "LintResult",
    callback: Optional[Callable[[DialogResult], None]] = None
) -> None:
    """
    Show the results dialog asynchronously.
    
    Args:
        result: LintResult from PromptLint analysis
        callback: Function to call with the DialogResult
    """
    def run():
        dialog_result = show_results_dialog(result)
        if callback:
            callback(dialog_result)
    
    thread = threading.Thread(target=run, daemon=True)
    thread.start()


class QuickActionPopup:
    """
    A quick action popup that appears near the cursor.
    
    Provides quick buttons for common actions without opening
    a full dialog.
    """
    
    def __init__(
        self,
        result: "LintResult",
        x: int,
        y: int,
        on_action: Optional[Callable[[str], None]] = None
    ):
        self.result = result
        self.x = x
        self.y = y
        self.on_action = on_action
        self.root: Optional[tk.Toplevel] = None
    
    def show(self) -> None:
        """Show the quick action popup."""
        # Create a hidden root window if needed
        try:
            root = tk._default_root
            if root is None:
                root = tk.Tk()
                root.withdraw()
        except Exception:
            root = tk.Tk()
            root.withdraw()
        
        self.root = tk.Toplevel(root)
        self.root.overrideredirect(True)  # No window decorations
        self.root.geometry(f"+{self.x}+{self.y}")
        self.root.attributes("-topmost", True)
        
        # Frame with border
        frame = ttk.Frame(self.root, padding="10", relief="raised", borderwidth=2)
        frame.pack()
        
        # Summary label
        summary_label = ttk.Label(
            frame,
            text=self.result.summary,
            font=("Helvetica", 10, "bold")
        )
        summary_label.pack(anchor=tk.W, pady=(0, 10))
        
        # Button frame
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        # Use Fixed button
        if self.result.optimized_prompt:
            use_fixed_btn = ttk.Button(
                btn_frame,
                text="Use Fixed",
                command=lambda: self._action("use_fixed"),
                width=12
            )
            use_fixed_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # View Details button
        details_btn = ttk.Button(
            btn_frame,
            text="Details",
            command=lambda: self._action("view_details"),
            width=10
        )
        details_btn.pack(side=tk.LEFT, padx=(0, 5))
        
        # Dismiss button
        dismiss_btn = ttk.Button(
            btn_frame,
            text="x",
            command=lambda: self._action("dismiss"),
            width=3
        )
        dismiss_btn.pack(side=tk.RIGHT)
        
        # Auto-dismiss after 10 seconds
        self.root.after(10000, self._dismiss)
        
        # Close on focus loss
        self.root.bind("<FocusOut>", lambda e: self._dismiss())
    
    def _action(self, action: str) -> None:
        """Handle action button click."""
        if self.on_action:
            self.on_action(action)
        self._dismiss()
    
    def _dismiss(self) -> None:
        """Dismiss the popup."""
        if self.root:
            try:
                self.root.destroy()
            except Exception:
                pass
            self.root = None


def show_quick_popup(
    result: "LintResult",
    x: Optional[int] = None,
    y: Optional[int] = None,
    on_action: Optional[Callable[[str], None]] = None
) -> None:
    """
    Show a quick action popup near the cursor.
    
    Args:
        result: LintResult from PromptLint analysis
        x: X position (defaults to mouse position)
        y: Y position (defaults to mouse position)
        on_action: Callback for action selection
    """
    # Get mouse position if not specified
    if x is None or y is None:
        try:
            import pyautogui
            pos = pyautogui.position()
            x = x or pos[0]
            y = y or pos[1] + 20  # Slightly below cursor
        except ImportError:
            x = x or 100
            y = y or 100
    
    popup = QuickActionPopup(result, x, y, on_action)
    popup.show()
