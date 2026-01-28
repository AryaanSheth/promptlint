@echo off
REM PromptLint Hotkey Service - Windows Installer
REM This script registers the PromptLint service to run on Windows startup

setlocal enabledelayedexpansion

echo ============================================
echo PromptLint Hotkey Service Installer
echo ============================================
echo.

REM Check for Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/
    pause
    exit /b 1
)

REM Get the project root directory (parent of scripts folder)
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

echo Checking dependencies...
echo.

REM Install required packages
echo Installing required Python packages...
pip install keyboard pyautogui pyperclip plyer pystray Pillow --quiet
if errorlevel 1 (
    echo WARNING: Some packages may not have installed correctly
    echo Please manually install: pip install keyboard pyautogui pyperclip plyer pystray Pillow
)

REM Check for pywin32 specifically on Windows
pip install pywin32 psutil --quiet

echo.
echo Dependencies installed.
echo.

REM Create startup shortcut
echo Creating startup shortcut...

set "STARTUP_FOLDER=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_FOLDER%\PromptLint.lnk"
set "VBS_SCRIPT=%TEMP%\create_shortcut.vbs"

REM Create VBScript to create shortcut
(
echo Set oWS = WScript.CreateObject^("WScript.Shell"^)
echo sLinkFile = "%SHORTCUT_PATH%"
echo Set oLink = oWS.CreateShortcut^(sLinkFile^)
echo oLink.TargetPath = "pythonw"
echo oLink.Arguments = "-m promptlint.hotkey"
echo oLink.WorkingDirectory = "%PROJECT_DIR%"
echo oLink.Description = "PromptLint Hotkey Service"
echo oLink.WindowStyle = 7
echo oLink.Save
) > "%VBS_SCRIPT%"

cscript //nologo "%VBS_SCRIPT%"
del "%VBS_SCRIPT%"

if exist "%SHORTCUT_PATH%" (
    echo Startup shortcut created successfully!
) else (
    echo WARNING: Could not create startup shortcut
    echo You can manually add the service to startup
)

echo.
echo ============================================
echo Installation Complete!
echo ============================================
echo.
echo The PromptLint service will now:
echo   - Start automatically when Windows starts
echo   - Show an icon in the system tray
echo   - Listen for Ctrl+Shift+L hotkey in Cursor
echo.
echo To start the service now, run:
echo   python -m promptlint.hotkey
echo.
echo To uninstall, run uninstall_service.bat
echo.

REM Ask if user wants to start now
set /p START_NOW="Start the service now? (Y/N): "
if /i "%START_NOW%"=="Y" (
    echo Starting PromptLint service...
    start "" pythonw -m promptlint.hotkey
    echo Service started! Check your system tray.
)

echo.
pause
