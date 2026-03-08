#!/usr/bin/env python3
"""
PromptLint Demo Script
Demonstrates all 15+ quality checks and auto-fix capabilities
"""

import sys
import subprocess
from pathlib import Path

def run_command(cmd, description):
    """Run a command and display the results."""
    print("\n" + "=" * 80)
    print(f"  {description}")
    print("=" * 80)
    print(f"$ {cmd}\n")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0 and result.returncode != 2:
        print(f"Error: {result.stderr}")
    return result.returncode

def main():
    print("=" * 80)
    print()
    print("  PromptLint - Comprehensive Prompt Quality Analyzer".center(80))
    print("  15+ Quality Checks | 5 Auto-Fix Capabilities".center(80))
    print()
    print("=" * 80)

    # Test 1: Bad prompt analysis
    run_command(
        "python -m promptlint.cli --file demo/example_bad_prompt.txt",
        "TEST 1: Analyzing a poorly-written prompt (20+ issues expected)"
    )

    # Test 2: Bad prompt with dashboard
    run_command(
        "python -m promptlint.cli --file demo/example_bad_prompt.txt --show-dashboard",
        "TEST 2: Same prompt with savings dashboard"
    )

    # Test 3: Auto-fix demonstration
    run_command(
        "python -m promptlint.cli --file demo/example_bad_prompt.txt --fix",
        "TEST 3: Auto-fix optimization (removes bloat, fixes redundancy, adds structure)"
    )

    # Test 4: Good prompt analysis
    run_command(
        "python -m promptlint.cli --file demo/example_good_prompt.txt",
        "TEST 4: Analyzing a well-written prompt (minimal issues expected)"
    )

    # Test 5: JSON output
    run_command(
        "python -m promptlint.cli --file demo/example_good_prompt.txt --format json",
        "TEST 5: JSON output for CI/CD integration"
    )

    print("\n" + "=" * 80)
    print("  Demo Complete!")
    print("=" * 80)
    print("\nKey Takeaways:")
    print("  [+] 15+ comprehensive quality checks")
    print("  [+] Security, clarity, specificity, verbosity, and completeness")
    print("  [+] 5 auto-fix capabilities (30-50% token reduction)")
    print("  [+] Line-by-line feedback with precise context")
    print("  [+] JSON output for automation")
    print("  [+] Configurable rules per team/project")
    print("\nNext Steps:")
    print("  * Check out FEATURES.md for full documentation")
    print("  * View .promptlintrc for configuration options")
    print("  * Read README.md for CI/CD integration")
    print()

if __name__ == "__main__":
    main()
