#!/usr/bin/env python3
"""
PromptLint System Tray Application

Provides a system tray icon and menu for managing the PromptLint hotkey service.
Cross-platform support: Windows, macOS, Linux
"""

from __future__ import annotations

import platform
import sys
import threading
import time
from typing import Callable, Optional, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .service import PromptLintService, LintResult

# Platform detection
PLATFORM = platform.system().lower()
IS_WINDOWS = PLATFORM == "windows"
IS_MACOS = PLATFORM == "darwin"
IS_LINUX = PLATFORM == "linux"

# Try to import pystray for system tray functionality
try:
    import pystray
    from PIL import Image, ImageDraw
    PYSTRAY_AVAILABLE = True
except ImportError:
    PYSTRAY_AVAILABLE = False


def create_tray_icon(color: str = "#3498db") -> "Image.Image":
    """
    Create a simple tray icon image.
    
    Args:
        color: Hex color for the icon
        
    Returns:
        PIL Image object
    """
    if not PYSTRAY_AVAILABLE:
        raise ImportError("pystray and Pillow are required for tray functionality")
    
    # Create a simple circular icon with "PL" text
    size = 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    
    # Convert hex to RGB
    color = color.lstrip("#")
    rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
    
    # Draw filled circle
    margin = 2
    draw.ellipse(
        [margin, margin, size - margin, size - margin],
        fill=rgb + (255,),
        outline=(255, 255, 255, 255),
        width=2
    )
    
    # Draw "PL" text
    try:
        from PIL import ImageFont
        # Try to use a system font
        font = ImageFont.truetype("arial.ttf", 24)
    except Exception:
        font = ImageFont.load_default()
    
    text = "PL"
    # Get text bounding box
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 2
    
    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
    
    return image


class TrayApplication:
    """
    System tray application for PromptLint service management.
    
    Provides:
    - Enable/disable monitoring
    - Hotkey display and configuration
    - Lint history view
    - Status display
    - Exit option
    """
    
    def __init__(
        self,
        service: Optional["PromptLintService"] = None,
        on_settings: Optional[Callable] = None,
        on_history: Optional[Callable] = None,
    ):
        self.service = service
        self.on_settings = on_settings
        self.on_history = on_history
        
        self._icon: Optional[pystray.Icon] = None
        self._running = False
        self._last_status = "Idle"
    
    def _create_menu(self) -> "pystray.Menu":
        """Create the tray menu."""
        if not PYSTRAY_AVAILABLE:
            raise ImportError("pystray required for tray menu")
        
        from pystray import Menu, MenuItem
        
        # Dynamic items
        def get_status_text() -> str:
            if self.service and self.service.last_lint_time:
                elapsed = time.time() - self.service.last_lint_time
                if elapsed < 60:
                    return f"Last lint: {int(elapsed)}s ago"
                elif elapsed < 3600:
                    return f"Last lint: {int(elapsed / 60)}m ago"
                else:
                    return f"Last lint: {int(elapsed / 3600)}h ago"
            return "Status: Ready"
        
        def is_enabled() -> bool:
            return self.service.enabled if self.service else False
        
        def toggle_enabled(icon, item):
            if self.service:
                self.service.enabled = not self.service.enabled
                self._update_icon()
        
        def open_settings(icon, item):
            if self.on_settings:
                self.on_settings()
        
        def open_history(icon, item):
            if self.on_history:
                self.on_history()
            elif self.service:
                self._show_history_dialog()
        
        def exit_app(icon, item):
            self.stop()
        
        # Build menu
        hotkey_text = f"Hotkey: {self.service.config.hotkey}" if self.service else "Hotkey: Not configured"
        
        menu = Menu(
            MenuItem(
                lambda text: get_status_text(),
                None,
                enabled=False
            ),
            Menu.SEPARATOR,
            MenuItem(
                lambda text: "Enabled" if is_enabled() else "Disabled",
                toggle_enabled,
                checked=lambda item: is_enabled()
            ),
            MenuItem(hotkey_text, None, enabled=False),
            Menu.SEPARATOR,
            MenuItem("View History", open_history),
            MenuItem("Settings", open_settings),
            Menu.SEPARATOR,
            MenuItem("Exit", exit_app)
        )
        
        return menu
    
    def _update_icon(self) -> None:
        """Update the tray icon based on service state."""
        if not self._icon:
            return
        
        # Change icon color based on state
        if self.service and self.service.enabled:
            color = "#27ae60"  # Green when enabled
        else:
            color = "#95a5a6"  # Gray when disabled
        
        self._icon.icon = create_tray_icon(color)
    
    def _show_history_dialog(self) -> None:
        """Show a simple history dialog."""
        if not self.service or not self.service.lint_history:
            from .dialog import show_notification
            show_notification("PromptLint", "No lint history available")
            return
        
        # Show last 5 lint results
        import tkinter as tk
        from tkinter import ttk
        
        root = tk.Tk()
        root.title("PromptLint History")
        root.geometry("500x400")
        
        # Create treeview for history
        columns = ("Time", "Issues", "Tokens Saved")
        tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
        
        for col in columns:
            tree.heading(col, text=col)
            tree.column(col, width=150)
        
        # Populate with history
        for result in reversed(self.service.lint_history[-10:]):
            time_str = datetime.now().strftime("%H:%M:%S")  # Simplified
            tree.insert("", tk.END, values=(
                time_str,
                result.issue_count,
                result.tokens_saved
            ))
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Close button
        close_btn = ttk.Button(root, text="Close", command=root.destroy)
        close_btn.pack(pady=10)
        
        root.mainloop()
    
    def start(self) -> None:
        """Start the tray application."""
        if not PYSTRAY_AVAILABLE:
            print("System tray not available. Install pystray and Pillow:")
            print("  pip install pystray Pillow")
            return
        
        # Create icon
        icon_image = create_tray_icon("#27ae60" if self.service and self.service.enabled else "#3498db")
        
        self._icon = pystray.Icon(
            "PromptLint",
            icon_image,
            "PromptLint Service",
            menu=self._create_menu()
        )
        
        self._running = True
        
        # Run icon in separate thread
        def run_icon():
            self._icon.run()
        
        self._icon_thread = threading.Thread(target=run_icon, daemon=True)
        self._icon_thread.start()
    
    def stop(self) -> None:
        """Stop the tray application."""
        self._running = False
        if self._icon:
            self._icon.stop()
        if self.service:
            self.service.stop()
    
    def update_status(self, status: str) -> None:
        """Update the status displayed in the tray menu."""
        self._last_status = status
        # Menu will auto-update on next open


class TraylessApplication:
    """
    Fallback application when system tray is not available.
    
    Runs the service with console-based status updates.
    """
    
    def __init__(self, service: "PromptLintService"):
        self.service = service
        self._running = False
    
    def start(self) -> None:
        """Start the application."""
        print("=" * 50)
        print("PromptLint Hotkey Service")
        print("=" * 50)
        print(f"Hotkey: {self.service.config.hotkey}")
        print(f"Status: {'Enabled' if self.service.enabled else 'Disabled'}")
        print("-" * 50)
        print("Commands:")
        print("  Ctrl+C - Exit")
        print("=" * 50)
        print()
        
        self._running = True
        self.service.start()
        
        try:
            while self._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
    
    def stop(self) -> None:
        """Stop the application."""
        self._running = False
        self.service.stop()
        print("\nService stopped.")


def create_application(
    service: Optional["PromptLintService"] = None,
    use_tray: bool = True,
) -> TrayApplication | TraylessApplication:
    """
    Create the appropriate application based on platform and availability.
    
    Args:
        service: PromptLintService instance
        use_tray: Whether to use system tray (if available)
        
    Returns:
        TrayApplication or TraylessApplication instance
    """
    # Import service if not provided
    if service is None:
        from .service import PromptLintService
        service = PromptLintService()
    
    if use_tray and PYSTRAY_AVAILABLE:
        return TrayApplication(service)
    else:
        return TraylessApplication(service)


def main():
    """Main entry point for the tray application."""
    # Import service
    from .service import PromptLintService, check_dependencies
    from .dialog import show_results_dialog, show_notification
    
    # Check dependencies
    missing = check_dependencies()
    if missing:
        print("Missing dependencies:")
        for dep in missing:
            print(f"  - {dep}")
        print(f"\nInstall with: pip install {' '.join(missing)}")
        sys.exit(1)
    
    # Check for tray dependencies
    if not PYSTRAY_AVAILABLE:
        print("Note: System tray not available. Install for tray support:")
        print("  pip install pystray Pillow")
        print()
    
    # Create and configure service
    def handle_result(result):
        show_notification("PromptLint", result.summary)
        if result.findings:
            show_results_dialog(result)
    
    def handle_error(message: str):
        show_notification("PromptLint Error", message)
        print(f"Error: {message}")
    
    def handle_status(message: str):
        print(f"[{datetime.now().strftime('%H:%M:%S')}] {message}")
    
    service = PromptLintService(
        on_result=handle_result,
        on_error=handle_error,
        on_status_change=handle_status
    )
    
    # Create application
    app = create_application(service, use_tray=True)
    
    # Start service
    service.start()
    
    # Start tray/console application
    if isinstance(app, TrayApplication):
        app.start()
        print("PromptLint running in system tray.")
        print(f"Press {service.config.hotkey} in Cursor to analyze your prompt.")
        print("Right-click tray icon for options, or press Ctrl+C to exit.")
        
        try:
            while app._running:
                time.sleep(1)
        except KeyboardInterrupt:
            pass
        finally:
            app.stop()
    else:
        app.start()


if __name__ == "__main__":
    main()
