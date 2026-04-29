# How It Works

PromptLint performs static analysis on prompt text — no model calls, no internet access, no latency.

## Analysis Pipeline

```
Input (file / stdin / --text)
        │
        ▼
   ┌─────────────┐
   │   io.py     │  Read file, resolve globs, read stdin
   └──────┬──────┘
          │
          ▼
   ┌─────────────────┐
   │  config.py      │  Load .promptlintrc, apply defaults
   └──────┬──────────┘
          │
          ▼
   ┌─────────────────────────────────────────┐
   │              engine.py                  │
   │  ┌───────────┐  ┌──────────┐  ┌──────┐ │
   │  │ security  │  │ quality  │  │ cost │ │
   │  │  rules    │  │  rules   │  │ rule │ │
   │  └───────────┘  └──────────┘  └──────┘ │
   └──────┬──────────────────────────────────┘
          │  List[Finding]
          ▼
   ┌──────────────────┐
   │  autofix.py      │  (if --fix flag set)
   └──────┬───────────┘
          │  optimized prompt text
          ▼
   ┌──────────────────┐
   │  output.py       │  Text / JSON / SARIF renderer
   └──────────────────┘
```

## Rule Execution

Rules are organized into three modules:

| Module | Rules |
|--------|-------|
| `rules/security.py` | `prompt-injection`, `jailbreak-pattern`, `secret-in-prompt`, `pii-in-prompt`, `context-injection-boundary` |
| `rules/quality.py` | `structure-sections`, `role-clarity`, `output-format-missing`, `hallucination-risk`, `clarity-vague-terms`, `specificity-*`, `politeness-bloat`, `verbosity-*`, `actionability-*`, `consistency-*`, `completeness-*` |
| `rules/cost.py` | `cost`, `cost-limit` |

Each rule receives the full prompt text and configuration, then returns a (possibly empty) list of `Finding` objects.

## Finding Object

```python
@dataclass
class Finding:
    rule_id: str       # e.g. "prompt-injection"
    level: str         # "CRITICAL" | "WARN" | "INFO"
    line: int          # 1-based; -1 for file-level findings
    message: str       # Human-readable description
    fix: str | None    # Suggested fix text (if auto-fixable)
```

## Token Counting

The Python CLI uses `tiktoken` when installed for exact counts:

```python
import tiktoken
enc = tiktoken.encoding_for_model("gpt-4o")
token_count = len(enc.encode(prompt_text))
```

Without `tiktoken`, or in the Node.js CLI:

```
token_count ≈ len(prompt_text) / 4
```

This heuristic has ±15% error on typical English prompts.

## Auto-Fix

When `--fix` is passed, `autofix.py` applies transformations in order:

1. Remove injection lines (`prompt-injection` fix)
2. Strip politeness words (`politeness-bloat` fix)
3. Replace redundant phrases (`verbosity-redundancy` fix)
4. Scaffold missing structure (`structure-sections` fix)
5. Normalize whitespace

The original file is **never modified**. The optimized text is written to stdout.

## Python / TypeScript Parity

Both the Python CLI and TypeScript CLI implement identical rule logic. Parity is enforced in CI:

```bash
# Runs in CI to verify both engines return identical findings
python -m pytest cli/tests/test_parity.py
```

Any new rule must be added to:
1. `cli/promptlint/rules/` (Python)
2. `npm/src/rules/` (TypeScript)
3. `rules-manifest.json` (source of truth)

## Exit Codes

| Code | Meaning |
|------|---------|
| `0` | No findings at or above `--fail-level` |
| `1` | Findings at WARN level |
| `2` | Findings at CRITICAL level |
