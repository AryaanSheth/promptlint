#!/usr/bin/env python3
"""
Simple PromptLint Hotkey Script for macOS

Press Cmd+Shift+L to lint clipboard contents.
"""

import subprocess
import json
import sys

print("=" * 50)
print("PromptLint Hotkey Service")
print("=" * 50)
print()

try:
    from pynput import keyboard
except ImportError:
    print("ERROR: pynput not installed")
    print("Run: pip3 install pynput")
    sys.exit(1)

# Track pressed keys
pressed_keys = set()

def on_press(key):
    global pressed_keys
    
    try:
        # Get key identifier
        key_id = None
        
        if hasattr(key, 'char') and key.char:
            key_id = key.char.lower()
        elif hasattr(key, 'name'):
            name = key.name.lower()
            if 'cmd' in name or name == 'cmd':
                key_id = 'cmd'
            elif 'shift' in name:
                key_id = 'shift'
            elif 'ctrl' in name:
                key_id = 'ctrl'
            elif 'alt' in name:
                key_id = 'alt'
            else:
                key_id = name
        
        if key_id:
            pressed_keys.add(key_id)
        
        # Check for Cmd+Shift+L
        if {'cmd', 'shift', 'l'}.issubset(pressed_keys):
            run_promptlint()
            pressed_keys.clear()
            
    except Exception as e:
        print(f"Key error: {e}")

def on_release(key):
    global pressed_keys
    
    try:
        key_id = None
        
        if hasattr(key, 'char') and key.char:
            key_id = key.char.lower()
        elif hasattr(key, 'name'):
            name = key.name.lower()
            if 'cmd' in name:
                key_id = 'cmd'
            elif 'shift' in name:
                key_id = 'shift'
            elif 'ctrl' in name:
                key_id = 'ctrl'
            elif 'alt' in name:
                key_id = 'alt'
            else:
                key_id = name
        
        if key_id:
            pressed_keys.discard(key_id)
            
    except Exception:
        pass

def run_promptlint():
    """Run PromptLint on clipboard contents."""
    print()
    print("🔍 Hotkey detected! Running PromptLint...")
    print("-" * 40)
    
    # Get clipboard
    try:
        result = subprocess.run(['pbpaste'], capture_output=True, text=True, timeout=5)
        text = result.stdout.strip()
    except Exception as e:
        print(f"❌ Could not read clipboard: {e}")
        return
    
    if not text:
        print("❌ Clipboard is empty!")
        print("   Copy some text first, then press Cmd+Shift+L")
        return
    
    print(f"📋 Clipboard: \"{text[:50]}{'...' if len(text) > 50 else ''}\"")
    print()
    
    # Run PromptLint
    try:
        lint_result = subprocess.run(
            [sys.executable, '-m', 'promptlint.cli', 
             '--text', text, 
             '--format', 'json', 
             '--fix',
             '--show-dashboard'],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        data = json.loads(lint_result.stdout)
        findings = data.get('findings', [])
        
        print(f"📊 Found {len(findings)} issues:")
        for f in findings[:5]:
            level = f.get('level', 'INFO')
            icon = '🔴' if level == 'CRITICAL' else '🟡' if level == 'WARN' else '🔵'
            print(f"   {icon} [{level}] {f.get('rule')}")
            msg = f.get('message', '')[:60]
            print(f"      {msg}...")
        
        if len(findings) > 5:
            print(f"   ... and {len(findings) - 5} more")
        
        # Show dashboard
        dashboard = data.get('dashboard', {})
        if dashboard:
            print()
            print(f"💰 Tokens: {dashboard.get('current_tokens', 0)} → {dashboard.get('optimized_tokens', 0)}")
            print(f"   Saved: {dashboard.get('tokens_saved', 0)} ({dashboard.get('reduction_percentage', 0):.1f}%)")
        
        # Copy fixed version
        optimized = data.get('optimized_prompt')
        if optimized:
            p = subprocess.Popen(['pbcopy'], stdin=subprocess.PIPE)
            p.communicate(optimized.encode('utf-8'))
            print()
            print("✅ Fixed prompt copied to clipboard!")
            print("   Press Cmd+V to paste it")
        
    except json.JSONDecodeError:
        print("❌ Could not parse PromptLint output")
        print(lint_result.stdout[:200] if lint_result.stdout else "No output")
    except subprocess.TimeoutExpired:
        print("❌ PromptLint timed out")
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print("-" * 40)
    print()

def main():
    print("✅ Service started!")
    print()
    print("📌 Hotkey: Cmd+Shift+L (⌘⇧L)")
    print()
    print("How to use:")
    print("  1. Copy text to clipboard (Cmd+C)")
    print("  2. Press Cmd+Shift+L")
    print("  3. Fixed version auto-copied!")
    print("  4. Paste with Cmd+V")
    print()
    print("Press Ctrl+C to stop")
    print("=" * 50)
    print()
    
    try:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            listener.join()
    except KeyboardInterrupt:
        print("\n👋 Stopped!")

if __name__ == '__main__':
    main()
