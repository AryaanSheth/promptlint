# Contributing to PromptLint

## Architecture

PromptLint ships as four separate packages from one monorepo. Every rule must be implemented in **both** the Python and TypeScript engines — they are independent codebases that must stay in sync:

```
promptlint/
├── cli/                    Python CLI  →  PyPI: promptlint-cli
│   └── promptlint/
│       ├── engine.py       orchestrates all rule checks
│       ├── autofix.py      auto-fix transformations
│       ├── io.py           file/stdin reading
│       ├── output.py       terminal + SARIF rendering
│       ├── constants.py    non-configurable magic numbers
│       ├── rules/
│       │   ├── cost.py     token counting (uses tiktoken)
│       │   ├── security.py injection, PII, secrets, boundaries
│       │   ├── quality.py  structure, clarity, verbosity, politeness
│       │   └── registry.py rule catalogue (--list-rules, --explain)
│       └── utils/
│           └── config.py   PromptlintConfig dataclass + YAML loading
│
├── npm/                    Node.js CLI  →  npm: promptlint-cli
│   └── src/
│       ├── engine.ts       mirrors engine.py
│       ├── cli.ts          mirrors cli.py
│       ├── config.ts       mirrors utils/config.py
│       └── rules/
│           ├── cost.ts     token counting (heuristic, ±15%)
│           ├── security.ts mirrors security.py
│           └── quality.ts  mirrors quality.py
│
├── action/                 GitHub Action wrapper (uses npm engine)
├── vscode/                 VS Code extension (uses npm engine)
└── action.yml              GitHub Action definition (repo root)
```

### Python ↔ TypeScript parity (critical constraint)

Every rule change in `cli/promptlint/rules/` **must** have a matching change in `npm/src/rules/`. CI will catch build failures but not logic drift — reviewers should verify both sides on every PR that touches rule logic.

The two engines share:
- Rule IDs and severity levels (defined in `registry.py` for Python; mirrored manually in TypeScript)
- Configuration schema (`.promptlintrc` YAML, loaded by both)
- Output format (findings structure, SARIF schema)

They differ in:
- Token counting: Python uses `tiktoken` (exact); npm uses `chars/4` heuristic (±15%)
- Terminal rendering: Python uses `rich`; npm uses raw ANSI codes

---

## Development setup

```bash
# Python CLI
cd cli
pip install -e ".[dev]"   # installs pytest, pytest-cov, hypothesis
pytest tests/             # run the test suite
pytest tests/ --cov=promptlint --cov-report=term-missing   # with coverage

# Node.js engine
cd npm
npm install
npm run build             # compile TypeScript
npm run lint              # eslint
```

---

## Adding a new rule

Rules are the core unit of extension. Every rule is a pure function:
`check_<name>(text: str, config: PromptlintConfig) -> List[Dict]`

Follow these steps for **both** the Python and TypeScript engines.

### Step 1 — Pick a category

| Category file | When to add here |
|---|---|
| `rules/security.py` | Injection, data leakage, trust boundaries |
| `rules/quality.py` | Clarity, structure, verbosity, actionability |
| `rules/cost.py` | Token usage, budget limits |

### Step 2 — Add the Python rule

Open the appropriate `rules/*.py` file and add a function following this pattern:

```python
def check_my_rule(text: str, config: PromptlintConfig) -> List[Dict[str, object]]:
    results: List[Dict[str, object]] = []

    if not config.enabled_rules.get("my-rule", True):
        return results

    # ... detection logic ...

    results.append({
        "level": "WARN",          # INFO | WARN | CRITICAL
        "rule": "my-rule",        # kebab-case, matches registry ID
        "message": "Human-readable description of the finding.",
        "line": _line_number(text, match.start()),   # or "-" for whole-prompt findings
        "context": _line_context(text, match.start(), config.context_width),
        "savings": 2.0,           # optional: estimated token savings
    })

    return results
```

Then register it in `engine.py`:

```python
from .rules.quality import check_my_rule   # add to imports

# inside LintEngine.analyze():
results.extend(check_my_rule(text, self.config))
```

### Step 3 — Add to the rule registry

Open `rules/registry.py` and add a `RuleMeta` entry to the `_RULES` list:

```python
RuleMeta(
    id="my-rule",
    category="Quality",
    default_severity="WARN",
    fixable=False,
    short="One-sentence summary shown in --list-rules.",
    long=(
        "Multi-line explanation shown by --explain my-rule.\n\n"
        "Example output:\n"
        "  [ WARN ] my-rule (line 3) ..."
    ),
),
```

### Step 4 — Add to the default config

In `utils/config.py`, add the rule ID to `enabled_rules` in `PromptlintConfig`:

```python
enabled_rules: Dict[str, bool] = field(
    default_factory=lambda: {
        ...
        "my-rule": True,   # ← add here
    }
)
```

### Step 5 — Mirror in TypeScript

Open `npm/src/rules/<category>.ts` and add the equivalent function:

```typescript
export function checkMyRule(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["my-rule"] ?? true)) return [];

  const results: Finding[] = [];

  // ... same detection logic ...

  results.push({
    level: "WARN",
    rule: "my-rule",
    message: "Human-readable description of the finding.",
    line: lineNumber(text, match.index),
    context: lineContext(text, match.index, config.contextWidth),
  });

  return results;
}
```

Then call it from `npm/src/engine.ts`:

```typescript
import { checkMyRule } from "./rules/quality";

// inside analyze():
results.push(...checkMyRule(text, config));
```

### Step 6 — Write tests

Add tests in `cli/tests/test_rules.py`:

```python
class TestMyRule:
    def test_detects_problem(self, default_config):
        results = check_my_rule("text that triggers the rule", default_config)
        assert len(results) == 1
        assert results[0]["level"] == "WARN"
        assert results[0]["rule"] == "my-rule"

    def test_clean_text_no_findings(self, default_config):
        results = check_my_rule("clean prompt without the issue", default_config)
        assert len(results) == 0

    def test_disabled_rule(self, disabled_config):
        results = check_my_rule("text that triggers the rule", disabled_config)
        assert len(results) == 0
```

### Step 7 — Update the starter config

Add the rule to `_STARTER_CONFIG` in `cli/promptlint/cli.py` so `promptlint --init` includes it.

---

## CI checklist

Every PR must pass:

| Check | Command |
|---|---|
| Python tests + coverage ≥ 70% | `pytest tests/ --cov=promptlint --cov-fail-under=70` |
| Python type checking | `mypy promptlint/ --ignore-missing-imports` |
| Python security scan | `bandit -r promptlint/ -ll` |
| TypeScript build | `npm run build` (in `npm/`) |
| TypeScript lint | `npm run lint` (in `npm/`) |
| Action dist up-to-date | checked automatically by CI |

---

## Rule severity guidelines

| Severity | When to use |
|---|---|
| `CRITICAL` | Active security risk (injection, secrets, PII). Blocks CI by default. |
| `WARN` | Structural problem that reliably degrades output quality. |
| `INFO` | Style guidance, cost hints, optional improvements. |
