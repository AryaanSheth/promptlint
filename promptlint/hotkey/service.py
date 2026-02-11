#!/usr/bin/env python3
"""
PromptLint Hotkey Service

A background service that monitors a global hotkey (Ctrl+Shift+L) to trigger
PromptLint analysis on typed text in Cursor IDE.

Cross-platform support: Windows, macOS, Linux
"""

from __future__ import annotations

import json
import platform
import subprocess
import sys
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional

# Platform detection
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == "windows"
IS_MACOS = PLATFORM == "darwin"
IS_LINUX = PLATFORM == "linux"

# Conditional imports based on platform
# Prefer pynput on macOS as it works with accessibility permissions
PYNPUT_AVAILABLE = False
KEYBOARD_AVAILABLE = False

if IS_MACOS:
    try:
        from pynput import keyboard as pynput_keyboard
        PYNPUT_AVAILABLE = True
    except ImportError:
        pass

if not PYNPUT_AVAILABLE:
    try:
        import keyboard
        KEYBOARD_AVAILABLE = True
    except ImportError:
        pass

try:
    import pyautogui
    pyautogui.FAILSAFE = False  # Disable fail-safe for automation
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False

# Windows-specific imports
if IS_WINDOWS:
    try:
        import win32gui
        import win32process
        import psutil
        WIN32_AVAILABLE = True
    except ImportError:
        WIN32_AVAILABLE = False
else:
    WIN32_AVAILABLE = False

# macOS-specific imports
if IS_MACOS:
    try:
        from AppKit import NSWorkspace
        APPKIT_AVAILABLE = True
    except ImportError:
        APPKIT_AVAILABLE = False
else:
    APPKIT_AVAILABLE = False


def _get_config_path() -> Path:
    """Get the path to the config file."""
    return Path(__file__).parent / "config.json"


@dataclass
class ServiceConfig:
    """Configuration for the PromptLint hotkey service."""
    hotkey: str = "ctrl+shift+l"
    auto_copy: bool = True
    show_info_level: bool = True
    notification_duration: int = 10
    promptlint_path: str = "python -m promptlint.cli"
    verify_cursor_active: bool = True
    min_text_length: int = 5
    max_text_length: int = 10000
    copy_delay_ms: int = 100
    selection_delay_ms: int = 50
    
    @classmethod
    def load(cls, path: Optional[Path] = None) -> "ServiceConfig":
        """Load configuration from JSON file."""
        config_path = path or _get_config_path()
        if not config_path.exists():
            return cls()
        
        try:
            data = json.loads(config_path.read_text(encoding="utf-8"))
            return cls(
                hotkey=data.get("hotkey", cls.hotkey),
                auto_copy=data.get("auto_copy", cls.auto_copy),
                show_info_level=data.get("show_info_level", cls.show_info_level),
                notification_duration=data.get("notification_duration", cls.notification_duration),
                promptlint_path=data.get("promptlint_path", cls.promptlint_path),
                verify_cursor_active=data.get("verify_cursor_active", cls.verify_cursor_active),
                min_text_length=data.get("min_text_length", cls.min_text_length),
                max_text_length=data.get("max_text_length", cls.max_text_length),
                copy_delay_ms=data.get("copy_delay_ms", cls.copy_delay_ms),
                selection_delay_ms=data.get("selection_delay_ms", cls.selection_delay_ms),
            )
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load config: {e}")
            return cls()
    
    def save(self, path: Optional[Path] = None) -> None:
        """Save configuration to JSON file."""
        config_path = path or _get_config_path()
        data = {
            "hotkey": self.hotkey,
            "auto_copy": self.auto_copy,
            "show_info_level": self.show_info_level,
            "notification_duration": self.notification_duration,
            "promptlint_path": self.promptlint_path,
            "verify_cursor_active": self.verify_cursor_active,
            "min_text_length": self.min_text_length,
            "max_text_length": self.max_text_length,
            "copy_delay_ms": self.copy_delay_ms,
            "selection_delay_ms": self.selection_delay_ms,
        }
        config_path.write_text(json.dumps(data, indent=2), encoding="utf-8")


@dataclass
class LintResult:
    """Result from PromptLint analysis."""
    success: bool
    findings: list[dict] = field(default_factory=list)
    optimized_prompt: Optional[str] = None
    dashboard: Optional[dict] = None
    error: Optional[str] = None
    original_text: str = ""
    
    @property
    def issue_count(self) -> int:
        return len(self.findings)
    
    @property
    def critical_count(self) -> int:
        return sum(1 for f in self.findings if f.get("level") == "CRITICAL")
    
    @property
    def warning_count(self) -> int:
        return sum(1 for f in self.findings if f.get("level") == "WARN")
    
    @property
    def info_count(self) -> int:
        return sum(1 for f in self.findings if f.get("level") == "INFO")
    
    @property
    def summary(self) -> str:
        if not self.success:
            return f"Error: {self.error}"
        if not self.findings:
            return "No issues found!"
        
        parts = []
        if self.critical_count:
            parts.append(f"{self.critical_count} critical")
        if self.warning_count:
            parts.append(f"{self.warning_count} warnings")
        if self.info_count:
            parts.append(f"{self.info_count} info")
        
        return f"Found {self.issue_count} issues: {', '.join(parts)}"
    
    @property
    def tokens_saved(self) -> int:
        if self.dashboard:
            return self.dashboard.get("tokens_saved", 0)
        return 0


class ClipboardManager:
    """Cross-platform clipboard management with backup/restore."""
    
    def __init__(self):
        self._backup: Optional[str] = None
    
    def backup(self) -> None:
        """Backup current clipboard content."""
        try:
            if PYPERCLIP_AVAILABLE:
                self._backup = pyperclip.paste()
            elif IS_MACOS:
                result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                self._backup = result.stdout
            elif IS_WINDOWS:
                # Use pyperclip fallback or win32clipboard
                pass
        except Exception:
            self._backup = None
    
    def restore(self) -> None:
        """Restore backed up clipboard content."""
        if self._backup is not None:
            self.set(self._backup)
            self._backup = None
    
    def get(self) -> str:
        """Get current clipboard content."""
        try:
            if PYPERCLIP_AVAILABLE:
                return pyperclip.paste()
            elif IS_MACOS:
                result = subprocess.run(["pbpaste"], capture_output=True, text=True)
                return result.stdout
            elif IS_WINDOWS:
                # Fallback for Windows
                pass
        except Exception:
            pass
        return ""
    
    def set(self, text: str) -> None:
        """Set clipboard content."""
        try:
            if PYPERCLIP_AVAILABLE:
                pyperclip.copy(text)
            elif IS_MACOS:
                process = subprocess.Popen(["pbcopy"], stdin=subprocess.PIPE)
                process.communicate(text.encode("utf-8"))
            elif IS_WINDOWS:
                # Fallback for Windows
                pass
        except Exception as e:
            print(f"Failed to set clipboard: {e}")


class WindowDetector:
    """Cross-platform active window detection."""
    
    @staticmethod
    def get_active_window_title() -> str:
        """Get the title of the currently active window."""
        try:
            if IS_WINDOWS and WIN32_AVAILABLE:
                hwnd = win32gui.GetForegroundWindow()
                return win32gui.GetWindowText(hwnd)
            elif IS_MACOS:
                if APPKIT_AVAILABLE:
                    workspace = NSWorkspace.sharedWorkspace()
                    active_app = workspace.frontmostApplication()
                    return active_app.localizedName() if active_app else ""
                else:
                    # Fallback using AppleScript
                    script = 'tell application "System Events" to get name of first application process whose frontmost is true'
                    result = subprocess.run(
                        ["osascript", "-e", script],
                        capture_output=True,
                        text=True
                    )
                    return result.stdout.strip()
            elif IS_LINUX:
                # Use xdotool on Linux
                result = subprocess.run(
                    ["xdotool", "getactivewindow", "getwindowname"],
                    capture_output=True,
                    text=True
                )
                return result.stdout.strip()
        except Exception:
            pass
        return ""
    
    @staticmethod
    def is_cursor_active() -> bool:
        """Check if Cursor IDE is the active window."""
        title = WindowDetector.get_active_window_title().lower()
        return "cursor" in title


class PromptLintService:
    """Main service for hotkey-triggered PromptLint analysis."""
    
    def __init__(
        self,
        config: Optional[ServiceConfig] = None,
        on_result: Optional[Callable[[LintResult], None]] = None,
        on_error: Optional[Callable[[str], None]] = None,
        on_status_change: Optional[Callable[[str], None]] = None,
    ):
        self.config = config or ServiceConfig.load()
        self.on_result = on_result
        self.on_error = on_error
        self.on_status_change = on_status_change
        
        self.clipboard = ClipboardManager()
        self._enabled = True
        self._running = False
        self._hotkey_registered = False
        self._last_lint_time: Optional[float] = None
        self._lint_history: list[LintResult] = []
    
    @property
    def enabled(self) -> bool:
        return self._enabled
    
    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = value
        if self.on_status_change:
            status = "enabled" if value else "disabled"
            self.on_status_change(f"Service {status}")
    
    @property
    def last_lint_time(self) -> Optional[float]:
        return self._last_lint_time
    
    @property
    def lint_history(self) -> list[LintResult]:
        return self._lint_history.copy()
    
    def _notify_status(self, message: str) -> None:
        """Notify status change."""
        if self.on_status_change:
            self.on_status_change(message)
    
    def _notify_error(self, message: str) -> None:
        """Notify error."""
        if self.on_error:
            self.on_error(message)
        else:
            print(f"Error: {message}")
    
    def register_hotkey(self) -> bool:
        """Register the global hotkey."""
        if PYNPUT_AVAILABLE:
            return self._register_hotkey_pynput()
        elif KEYBOARD_AVAILABLE:
            return self._register_hotkey_keyboard()
        else:
            self._notify_error("No hotkey library available. Install with: pip install pynput")
            return False
    
    def _register_hotkey_pynput(self) -> bool:
        """Register hotkey using pynput (preferred on macOS)."""
        try:
            # Parse hotkey string (e.g., "ctrl+shift+l")
            hotkey_parts = self.config.hotkey.lower().split("+")
            
            # Map modifier names to pynput keys
            modifier_map = {
                "ctrl": pynput_keyboard.Key.ctrl,
                "control": pynput_keyboard.Key.ctrl,
                "shift": pynput_keyboard.Key.shift,
                "alt": pynput_keyboard.Key.alt,
                "option": pynput_keyboard.Key.alt,
                "cmd": pynput_keyboard.Key.cmd,
                "command": pynput_keyboard.Key.cmd,
            }
            
            self._pynput_modifiers = set()
            self._pynput_key = None
            
            for part in hotkey_parts:
                part = part.strip()
                if part in modifier_map:
                    self._pynput_modifiers.add(modifier_map[part])
                else:
                    # It's the main key
                    self._pynput_key = part
            
            self._pressed_modifiers = set()
            
            def on_press(key):
                try:
                    # Check if it's a modifier
                    if hasattr(key, 'name') or key in self._pynput_modifiers:
                        if key in self._pynput_modifiers:
                            self._pressed_modifiers.add(key)
                        # Also handle Key.ctrl_l, Key.ctrl_r etc.
                        for mod in self._pynput_modifiers:
                            if hasattr(key, 'name') and mod.name in str(key):
                                self._pressed_modifiers.add(mod)
                    
                    # Check if it's our target key
                    key_char = None
                    if hasattr(key, 'char') and key.char:
                        key_char = key.char.lower()
                    elif hasattr(key, 'name'):
                        key_char = key.name.lower()
                    
                    if key_char == self._pynput_key:
                        # Check if all modifiers are pressed
                        if self._pynput_modifiers.issubset(self._pressed_modifiers):
                            self._on_hotkey_pressed()
                except Exception:
                    pass
            
            def on_release(key):
                try:
                    if key in self._pressed_modifiers:
                        self._pressed_modifiers.discard(key)
                    # Handle ctrl_l, ctrl_r, etc.
                    for mod in list(self._pressed_modifiers):
                        if hasattr(key, 'name') and mod.name in str(key):
                            self._pressed_modifiers.discard(mod)
                except Exception:
                    pass
            
            self._pynput_listener = pynput_keyboard.Listener(
                on_press=on_press,
                on_release=on_release
            )
            self._pynput_listener.start()
            self._hotkey_registered = True
            self._notify_status(f"Hotkey registered: {self.config.hotkey}")
            return True
            
        except Exception as e:
            self._notify_error(f"Failed to register hotkey with pynput: {e}")
            return False
    
    def _register_hotkey_keyboard(self) -> bool:
        """Register hotkey using keyboard library."""
        try:
            keyboard.add_hotkey(
                self.config.hotkey,
                self._on_hotkey_pressed,
                suppress=False
            )
            self._hotkey_registered = True
            self._notify_status(f"Hotkey registered: {self.config.hotkey}")
            return True
        except Exception as e:
            self._notify_error(f"Failed to register hotkey: {e}")
            return False
    
    def unregister_hotkey(self) -> None:
        """Unregister the global hotkey."""
        if PYNPUT_AVAILABLE and hasattr(self, '_pynput_listener'):
            try:
                self._pynput_listener.stop()
                self._hotkey_registered = False
            except Exception:
                pass
        elif KEYBOARD_AVAILABLE and self._hotkey_registered:
            try:
                keyboard.remove_hotkey(self.config.hotkey)
                self._hotkey_registered = False
            except Exception:
                pass
    
    def _on_hotkey_pressed(self) -> None:
        """Handle hotkey press event."""
        if not self._enabled:
            return
        
        # Run in separate thread to not block
        thread = threading.Thread(target=self._process_hotkey, daemon=True)
        thread.start()
    
    def _process_hotkey(self) -> None:
        """Process the hotkey press."""
        try:
            # Check if Cursor is active
            if self.config.verify_cursor_active and not WindowDetector.is_cursor_active():
                self._notify_status("Cursor is not the active window")
                return
            
            # Capture text
            text = self._capture_text()
            if not text:
                self._notify_error("No text captured")
                return
            
            # Validate text length
            if len(text) < self.config.min_text_length:
                self._notify_error(f"Text too short (min {self.config.min_text_length} chars)")
                return
            
            if len(text) > self.config.max_text_length:
                self._notify_error(f"Text too long (max {self.config.max_text_length} chars)")
                return
            
            self._notify_status("Running PromptLint analysis...")
            
            # Run PromptLint
            result = self._run_promptlint(text)
            result.original_text = text
            
            # Store in history
            self._lint_history.append(result)
            self._last_lint_time = time.time()
            
            # Notify result
            if self.on_result:
                self.on_result(result)
            else:
                print(f"Result: {result.summary}")
                
        except Exception as e:
            self._notify_error(f"Processing error: {e}")
    
    def _capture_text(self) -> str:
        """Capture text from the active window."""
        if not self.config.auto_copy:
            return self.clipboard.get()
        
        # Backup clipboard
        self.clipboard.backup()
        
        try:
            if PYAUTOGUI_AVAILABLE:
                # Select all text in the active field
                if IS_MACOS:
                    pyautogui.hotkey("command", "a")
                else:
                    pyautogui.hotkey("ctrl", "a")
                
                time.sleep(self.config.selection_delay_ms / 1000.0)
                
                # Copy to clipboard
                if IS_MACOS:
                    pyautogui.hotkey("command", "c")
                else:
                    pyautogui.hotkey("ctrl", "c")
                
                time.sleep(self.config.copy_delay_ms / 1000.0)
            else:
                # Fallback using keyboard library
                if KEYBOARD_AVAILABLE:
                    if IS_MACOS:
                        keyboard.send("command+a")
                        time.sleep(self.config.selection_delay_ms / 1000.0)
                        keyboard.send("command+c")
                    else:
                        keyboard.send("ctrl+a")
                        time.sleep(self.config.selection_delay_ms / 1000.0)
                        keyboard.send("ctrl+c")
                    
                    time.sleep(self.config.copy_delay_ms / 1000.0)
            
            return self.clipboard.get()
            
        except Exception as e:
            self._notify_error(f"Failed to capture text: {e}")
            self.clipboard.restore()
            return ""
    
    def _run_promptlint(self, text: str) -> LintResult:
        """Run PromptLint CLI on the given text."""
        try:
            # Build command
            cmd_parts = self.config.promptlint_path.split()
            cmd = cmd_parts + [
                "--text", text,
                "--format", "json",
                "--fix",
                "--show-dashboard"
            ]
            
            # Run PromptLint
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode not in (0, 1, 2):  # 1 and 2 are valid exit codes for warnings/critical
                return LintResult(
                    success=False,
                    error=f"PromptLint failed: {result.stderr or 'Unknown error'}"
                )
            
            # Parse JSON output
            try:
                data = json.loads(result.stdout)
                return LintResult(
                    success=True,
                    findings=data.get("findings", []),
                    optimized_prompt=data.get("optimized_prompt"),
                    dashboard=data.get("dashboard"),
                )
            except json.JSONDecodeError as e:
                return LintResult(
                    success=False,
                    error=f"Failed to parse PromptLint output: {e}"
                )
                
        except subprocess.TimeoutExpired:
            return LintResult(success=False, error="PromptLint timed out")
        except FileNotFoundError:
            return LintResult(success=False, error="PromptLint CLI not found")
        except Exception as e:
            return LintResult(success=False, error=str(e))
    
    def run_lint_on_text(self, text: str) -> LintResult:
        """Public method to run lint on arbitrary text."""
        result = self._run_promptlint(text)
        result.original_text = text
        self._lint_history.append(result)
        self._last_lint_time = time.time()
        return result
    
    def copy_fixed_to_clipboard(self, result: LintResult) -> bool:
        """Copy the fixed/optimized prompt to clipboard."""
        if result.optimized_prompt:
            self.clipboard.set(result.optimized_prompt)
            return True
        return False
    
    def start(self) -> None:
        """Start the service."""
        if self._running:
            return
        
        if not self.register_hotkey():
            return
        
        self._running = True
        self._notify_status("PromptLint service started")
    
    def stop(self) -> None:
        """Stop the service."""
        self.unregister_hotkey()
        self._running = False
        self._notify_status("PromptLint service stopped")
    
    def run_forever(self) -> None:
        """Run the service until interrupted."""
        self.start()
        
        if not self._running:
            return
        
        print(f"PromptLint Hotkey Service running...")
        print(f"Press {self.config.hotkey} in Cursor to analyze your prompt")
        print("Press Ctrl+C to exit")
        
        try:
            if PYNPUT_AVAILABLE and hasattr(self, '_pynput_listener'):
                # pynput listener runs in background, just wait
                while self._running:
                    time.sleep(0.5)
            elif KEYBOARD_AVAILABLE:
                keyboard.wait()
            else:
                while self._running:
                    time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()


def check_dependencies() -> list[str]:
    """Check for missing dependencies."""
    missing = []
    
    # Need either pynput or keyboard for hotkey support
    if not PYNPUT_AVAILABLE and not KEYBOARD_AVAILABLE:
        missing.append("pynput")  # Prefer pynput, especially on macOS
    if not PYAUTOGUI_AVAILABLE:
        missing.append("pyautogui")
    if not PYPERCLIP_AVAILABLE:
        missing.append("pyperclip")
    
    if IS_WINDOWS and not WIN32_AVAILABLE:
        missing.extend(["pywin32", "psutil"])
    
    return missing


def main():
    """Main entry point for the service."""
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        sys.exit(1)
    
    # Import dialog module for result handling
    try:
        from .dialog import show_results_dialog, show_notification
        
        def handle_result(result: LintResult):
            show_notification(
                title="PromptLint Analysis",
                message=result.summary
            )
            # Show detailed dialog if issues found
            if result.findings:
                show_results_dialog(result)
        
        def handle_error(message: str):
            show_notification(
                title="PromptLint Error",
                message=message
            )
        
        service = PromptLintService(
            on_result=handle_result,
            on_error=handle_error,
            on_status_change=lambda msg: print(f"Status: {msg}")
        )
    except ImportError:
        # Fallback to console output
        service = PromptLintService(
            on_result=lambda r: print(f"Result: {r.summary}"),
            on_error=lambda e: print(f"Error: {e}"),
            on_status_change=lambda msg: print(f"Status: {msg}")
        )
    
    service.run_forever()


if __name__ == "__main__":
    main()
