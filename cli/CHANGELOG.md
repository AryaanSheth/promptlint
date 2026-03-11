# Changelog

All notable changes to PromptLint are documented here.  
This project follows [Semantic Versioning](https://semver.org/).

## 1.1.1 — 2026-03-11

### Fixed (VS Code Extension)
- **`Fix All Files` was identical to `Fix File`** — `promptlint.fixAll` now iterates all open documents that match the configured languages and applies auto-fixes to each, instead of acting only on the active editor.
- **`showStatusBar: false` had no effect** — the status bar is no longer created when the setting is disabled.
- **Missing `activationEvents`** — added `onLanguage` entries for `python`, `javascript`, `typescript`, `json`, and `yaml` so the extension activates automatically on those file types (they were already in the default `languages` list but the extension wouldn't activate until a command was triggered).
- **Command title typo** — "Fix All File" renamed to "Fix All Files".

### Added (VS Code Extension)
- `license`, `repository`, `keywords`, and `icon` fields added to the extension manifest, satisfying VS Code Marketplace publishing requirements.
- `.vscodeignore` now excludes `test-fixtures/` and `package-lock.json` to keep the packaged `.vsix` lean.

---

## 1.1.0 — 2026-03-10

### Added
- **VS Code extension** (`vscode/`) — real-time diagnostics, quick fixes, token/cost status bar, and command palette integration powered by the promptlint CLI.
  - **Diagnostics on save** — findings appear as squiggly underlines with severity-mapped colors (Error/Warning/Info).
  - **Lint on type** — optional debounced linting as you type (off by default).
  - **Quick fixes** — lightbulb menu offers one-click fixes for fixable rules and inline `# promptlint-disable` comments.
  - **Magic comment markers** — `# promptlint-start` / `# promptlint-end` (or `//`) delimit prompt regions inside `.py`, `.ts`, `.js` files; only those regions are linted.
  - **Code wrapper stripping** — variable assignments and string delimiters (`"""`, `` ` ``, etc.) inside marker regions are automatically stripped before linting/fixing so the CLI only sees prompt text.
  - **Indentation-preserving fix** — "Fix File" applies CLI auto-fixes while keeping original indentation and code structure intact.
  - **Status bar** — live token count and cost-per-call indicator; click to open the dashboard.
  - **Commands** — Lint File, Fix File, Fix All, Show Dashboard, Explain Rule, Initialize Config.
  - **Settings** — `promptlint.pythonPath`, `lintOnSave`, `lintOnType`, `lintOnTypeDelay`, `languages`, `configPath`, `failLevel`, `showStatusBar`.
  - **Auto-detection** — prompts the user to install `promptlint-cli` if the CLI is not found.

---

## 1.0.2 — 2026-03-10

### Security
- **Injection evasion normalization.** The `prompt-injection` rule now normalizes text before matching to catch obfuscated attacks:
  - **Leetspeak decoding** — `0→o`, `1→i`, `3→e`, `4→a`, `5→s`, `7→t`, `8→b`, `@→a`, `$→s`, `!→i`, `(→c`, `|→l`, `+→t`.
  - **Zero-width character stripping** — removes `U+200B`, `U+200C`, `U+200D`, `U+2060`, `U+FEFF`, soft hyphens, and other invisible chars.
  - **Unicode NFKD normalization** — collapses fullwidth and confusable characters to their ASCII equivalents.
  - **Character repetition collapse** — `ignoooore` → `ignore` (3+ consecutive identical chars reduced to 1).
- Obfuscated matches display a distinct message: *"Obfuscated injection pattern detected: '...' (after normalizing leetspeak/unicode)."*

### Added
- **Cursor skill** (`.cursor/skills/promptlint/SKILL.md`) — teaches Cursor agents prompt conventions, the lint-and-fix loop, prompt extraction from code, and the full CLI/rules reference.
- **Claude Code skill** (`.claude/skills/promptlint/SKILL.md`) — equivalent skill for Claude Code with the same comprehensive coverage.
- **28 new tests** for injection normalization — unit tests for `_normalize_for_matching` and integration tests for `check_injection` covering leetspeak, zero-width chars, soft hyphens, character repetition, fullwidth unicode, mixed evasion, custom patterns, and false-positive checks. Test suite now at 145 tests.

### Changed
- Stale planning files (`FEATURES.md`, `featurex.md`, `.github_issue_body.md`) moved to `docs/internal/`.

---

## 1.0.1 — 2026-03-10

### Changed
- **`tiktoken` is now an optional dependency.** The base install (`pip install promptlint-cli`) no longer requires a Rust compiler or native extensions. Install with `pip install promptlint-cli[tiktoken]` for exact BPE token counts.
- When `tiktoken` is not installed, the `cost` and `cost-limit` rules use a fast character-based estimate (~4 chars per token) instead. All other rules are unaffected.

---

## 1.0.0 — 2026-03-09

First public release.

### Added
- **`--version` / `-V`** flag.
- **`--list-rules`** — tabular overview of every built-in rule with ID, category, severity, and fix support.
- **`--explain RULE_ID`** — detailed description and examples for any rule.
- **`--init`** — generate a starter `.promptlintrc` in the current directory.
- **`--quiet` / `-q`** — suppress findings output; print only the summary line (ideal for CI).
- **Positional file/glob arguments** — `promptlint prompts/**/*.txt` with optional `--exclude` patterns.
- **Inline ignore comments** — add `# promptlint-disable rule-id` (or `# promptlint-disable` to suppress all) on any line.
- **Summary line** — every run ends with "N file(s) scanned, X finding(s) in Ys".
- **`python -m promptlint`** support via `__main__.py`.

### Security
- **Injection pattern validation** — invalid regex patterns in config are rejected at load time with a clear warning.
- **Graceful regex errors at runtime** — bad patterns in `check_injection` and auto-fix won't crash; they're skipped with a stderr warning.
- **Bounded stdin/file input** — inputs exceeding 10 MB are rejected to prevent memory exhaustion.
- **Numeric config bounds** — `token_limit`, `cost_per_1k_tokens`, and `calls_per_day` are clamped to sane ranges.
- **Quadratic regex fix** — replaced `[\s\S]*` JSON-detection regex in `quality.py` with an O(n) character check.
- **Landing CSP** — `helmet` now enforces a `Content-Security-Policy` header instead of disabling it.
- **Landing error leak** — Supabase error messages are no longer sent to the client.
- **Landing rate limit** — `/api/signup-count` now has a 60-req/min rate limiter.

### Changed
- Version bumped from 0.1.0 to 1.0.0.
- **Migrated from `setup.py` to `pyproject.toml`** with compatible-release (`~=`) dependency pins.
- Removed unused `typer` dependency; CLI remains pure `argparse`.
- **Comprehensive test suite** — 77 pytest tests covering config, rules, engine, CLI flags, auto-fix, and edge cases.

### Rules (unchanged from 0.1.0)
- `cost` — token count and cost estimate
- `cost-limit` — token budget enforcement
- `prompt-injection` — injection pattern detection (auto-fixable)
- `structure-sections` — section structure verification (auto-fixable)
- `clarity-vague-terms` — vague language detection
- `specificity-examples` — missing example suggestion
- `specificity-constraints` — missing constraint suggestion
- `politeness-bloat` — politeness word detection (auto-fixable)
- `verbosity-sentence-length` — long sentence detection
- `verbosity-redundancy` — redundant phrase detection (auto-fixable)
- `actionability-weak-verbs` — passive voice detection
- `consistency-terminology` — mixed term detection
- `completeness-edge-cases` — edge case reminder
