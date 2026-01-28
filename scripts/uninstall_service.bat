@echo off
REM PromptLint Hotkey Service - Windows Uninstaller
REM This script removes the PromptLint service from Windows startup

echo ============================================
echo PromptLint Hotkey Service Uninstaller
echo ============================================
echo.

REM Remove startup shortcut
set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\PromptLint.lnk"

if exist "%SHORTCUT_PATH%" (
    del "%SHORTCUT_PATH%"
    echo Startup shortcut removed.
) else (
    echo No startup shortcut found.
)

REM Kill any running instances
echo Stopping any running PromptLint processes...
taskkill /f /im pythonw.exe /fi "WINDOWTITLE eq *promptlint*" >nul 2>&1

echo.
echo ============================================
echo Uninstallation Complete!
echo ============================================
echo.
echo PromptLint service has been removed from startup.
echo The Python packages have NOT been uninstalled.
echo.
echo To completely remove, you can also run:
echo   pip uninstall keyboard pyautogui pyperclip plyer pystray Pillow pywin32 psutil
echo.
pause
