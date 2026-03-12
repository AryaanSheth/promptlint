#!/usr/bin/env python3
"""
PromptLint Demo Pipeline — Fake chatbot UI that shows lint findings and autofix.
"""

import json
import subprocess
import sys
from pathlib import Path

from typing import Optional

from flask import Flask, jsonify, request, send_from_directory

REPO_ROOT = Path(__file__).resolve().parent.parent
DEMO_DIR = Path(__file__).resolve().parent
CLI_PATH = REPO_ROOT / "cli"

app = Flask(__name__)

# Config path for promptlint (use repo root .promptlintrc if exists)
CONFIG_PATH = REPO_ROOT / ".promptlintrc"


def _run_promptlint(prompt_text: str, fix: bool = False) -> dict:
    """Run promptlint on text, return parsed JSON output."""
    if not prompt_text or not prompt_text.strip():
        return {"error": "Prompt text is required"}

    args = [
        sys.executable,
        "-m",
        "promptlint.cli",
        "-t",
        prompt_text,
        "--format",
        "json",
    ]
    if CONFIG_PATH.exists():
        args.extend(["-c", str(CONFIG_PATH)])
    if fix:
        args.append("--fix")

    try:
        result = subprocess.run(
            args,
            cwd=str(CLI_PATH),
            capture_output=True,
            text=True,
            timeout=30,
        )
        stdout = result.stdout.strip()
        stderr = result.stderr.strip()

        if result.returncode != 0 and result.returncode != 1 and result.returncode != 2:
            return {"error": stderr or f"promptlint exited with code {result.returncode}"}

        if not stdout:
            return {"error": "No output from promptlint", "stderr": stderr}

        data = json.loads(stdout)
        return data
    except subprocess.TimeoutExpired:
        return {"error": "promptlint timed out"}
    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse promptlint output: {e}", "raw": stdout[:500]}
    except Exception as e:
        return {"error": str(e)}


def _mock_llm_response(optimized_prompt: str) -> str:
    """Generate a realistic fake LLM response based on the optimized prompt."""
    if not optimized_prompt or len(optimized_prompt.strip()) < 5:
        return "I'm not sure what you're asking. Could you please rephrase your question?"
    lower = optimized_prompt.lower()
    if "ignore" in lower or "instruction" in lower or "system prompt" in lower:
        return "I can't assist with that request."
    if "sum" in lower and ("function" in lower or "code" in lower):
        return """Sure, here's a Python function that sums a list of numbers:

```python
def sum_list(numbers):
    return sum(numbers)
```

For edge cases like empty lists, this returns 0. Want me to add validation or handle floats?"""
    if "sort" in lower and ("function" in lower or "code" in lower):
        return """Here's the updated function that sorts the list:

```python
def function(lst):
    return sorted(lst)
```

Using `lst` instead of `list` avoids shadowing the built-in. `sorted()` returns a new list and handles edge cases (empty, single-element)."""
    if "function" in lower or "code" in lower or "write" in lower:
        return """Here's a starting point for that:

```python
def process(inputs):
    # Process inputs and return result
    result = []
    for item in inputs:
        # Add your logic here
        result.append(item)
    return result
```

Let me know if you'd like me to refine this or add error handling."""
    if "summar" in lower or "summary" in lower:
        return """Here's a summary in 3 points:

1. **Main idea** — The core argument or conclusion of the content.
2. **Supporting points** — Key evidence, examples, or reasoning.
3. **Takeaway** — Practical implication or next step.

If you have specific text to summarize, paste it and I'll do a real pass."""
    if "extract" in lower or "entity" in lower:
        return """I can help extract entities. Here's the structure I'd use:

| Entity | Type | Value |
|--------|------|-------|
| ...    | PERSON / ORG / DATE | ... |

Share the text and I'll extract the actual entities."""
    return "I'd be happy to help with that. Could you give me a bit more detail about what you're looking for?"


def _build_fix_log(findings: list, optimized_prompt: Optional[str]) -> list:
    """Build a human-readable log of what was fixed."""
    log = []
    fixable_rules = {"politeness-bloat", "verbosity-redundancy", "prompt-injection", "structure-sections"}

    by_rule = {}
    for f in findings:
        rule = f.get("rule", "")
        if rule in fixable_rules:
            by_rule[rule] = by_rule.get(rule, 0) + 1

    if not by_rule and not optimized_prompt:
        return ["No auto-fixable issues found."]

    log.append("→ Applying auto-fixes...")
    if "prompt-injection" in by_rule:
        log.append(f"  ✂ Removed {by_rule['prompt-injection']} injection pattern(s)")
    if "politeness-bloat" in by_rule:
        log.append(f"  ✂ Stripped {by_rule['politeness-bloat']} politeness filler(s)")
    if "verbosity-redundancy" in by_rule:
        log.append(f"  ✂ Simplified {by_rule['verbosity-redundancy']} redundant phrase(s)")
    if "structure-sections" in by_rule:
        log.append("  ✂ Scaffolded missing <task>/<context> structure")

    if optimized_prompt:
        log.append("→ Optimized prompt ready")
    return log


@app.route("/")
def index():
    return send_from_directory(DEMO_DIR / "static", "index.html")


@app.route("/api/chat", methods=["POST"])
def api_chat():
    """Single endpoint: analyze + fix, return chat-friendly response."""
    data = request.get_json() or {}
    prompt = data.get("prompt", "")
    if not prompt or not prompt.strip():
        return jsonify({"error": "Message is required"})
    result = _run_promptlint(prompt, fix=True)
    if "error" in result:
        return jsonify(result)
    result["fix_log"] = _build_fix_log(
        result.get("findings", []),
        result.get("optimized_prompt"),
    )
    opt = (result.get("optimized_prompt") or "").strip() or prompt
    result["mock_response"] = _mock_llm_response(opt)
    result["original"] = prompt
    return jsonify(result)


if __name__ == "__main__":
    app.run(debug=True, port=5051)
