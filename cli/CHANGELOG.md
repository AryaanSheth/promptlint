# Changelog

All notable changes to PromptLint are documented here.  
This project follows [Semantic Versioning](https://semver.org/).

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
