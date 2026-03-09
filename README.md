## PromptLint

Static analysis for LLM prompts. Think ESLint, but for the text you send to GPT-4 / Claude / Gemini.

It catches token waste, vague language, prompt injection, missing structure, and a bunch of other things that make prompts worse in production. Runs locally, no API calls, results in milliseconds.

```
$ promptlint --file system_prompt.txt

PromptLint Findings
[ INFO     ] cost (line -) Prompt is ~38 tokens (~$0.0002 input per call on gpt-4o).
[ WARN     ] structure-sections (line -) No explicit sections detected (Task/Context/Output).
[ WARN     ] clarity-vague-terms (line 1) Vague term 'some' detected (vague quantifier). Be more specific.
[ INFO     ] verbosity-redundancy (line 3) Redundant phrase 'In order to' detected. Use simpler alternative.
[ WARN     ] politeness-bloat (line 1) Consider removing 'Please' (adds 1.5 tokens without semantic value).
[ CRITICAL ] prompt-injection (line 5) Injection pattern detected: 'ignore previous instructions'.

1 file(s) scanned, 8 finding(s) in 0.41s
```

### Install

```bash
pip install -e ./cli
```

Or from inside `cli/`:

```bash
pip install -e .
```

Requires Python 3.9+.

### Usage

```bash
# lint a file
promptlint --file prompt.txt

# lint inline text
promptlint -t "Please write some code for me"

# multiple files with globs
promptlint prompts/**/*.txt --exclude prompts/drafts/*

# pipe from stdin
cat prompt.txt | promptlint --format json

# auto-fix what it can
promptlint --file prompt.txt --fix

# CI mode: exit 1 on warnings, only print the summary
promptlint prompts/ --fail-level warn --quiet
```

Exit codes: `0` = clean, `1` = warnings found (with `--fail-level warn`), `2` = critical issues.

### What it checks

| Rule | What it does | Fixable |
|------|-------------|---------|
| `cost` | Token count and per-call cost estimate | - |
| `cost-limit` | Warns when prompt exceeds your token budget | - |
| `prompt-injection` | Catches "ignore previous instructions" and similar | yes |
| `structure-sections` | Flags prompts with no clear sections | yes |
| `clarity-vague-terms` | Finds "some", "stuff", "maybe", "good", etc. | - |
| `specificity-examples` | Suggests adding examples for complex instructions | - |
| `specificity-constraints` | Suggests adding length/format/scope constraints | - |
| `politeness-bloat` | Flags "please", "kindly", "thank you" (burns tokens) | yes |
| `verbosity-sentence-length` | Flags sentences over 40 words | - |
| `verbosity-redundancy` | "in order to" -> "to", "due to the fact that" -> "because" | yes |
| `actionability-weak-verbs` | Flags excessive passive voice | - |
| `consistency-terminology` | Catches mixed terms (user/customer, function/method) | - |
| `completeness-edge-cases` | Reminds you to specify error handling | - |

Run `promptlint --list-rules` to see them all, or `promptlint --explain cost` for details on any rule.

### Auto-fix

Pass `--fix` and PromptLint will remove politeness filler, simplify redundant phrases, strip injection lines, and scaffold missing `<task>`/`<context>` tags:

```
$ promptlint -t "Please kindly write code in order to sort the array, thank you" --fix

Optimized Prompt
<task>Write code to sort the array.</task>
```

### Configuration

Drop a `.promptlintrc` in your repo root (or run `promptlint --init` to generate one):

```yaml
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

rules:
  cost:
    enabled: true
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - "you are now a [a-zA-Z ]+"
  politeness_bloat:
    enabled: true
    words: [please, kindly, thank you, i would appreciate]
    savings_per_hit: 1.5
  structure_sections:
    enabled: true

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
```

Every rule can be toggled individually. See `docs/` for the full config reference.

### CLI reference

```
promptlint [FILES...] [OPTIONS]

  -V, --version            Show version
  -f, --file PATH          Single prompt file
  -t, --text TEXT          Inline prompt text
  -c, --config PATH        Config file (default: .promptlintrc)
  --format {text,json}     Output format
  --fix                    Auto-fix and print optimized prompt
  --fail-level LEVEL       none / warn / critical (default: critical)
  --show-dashboard         Token savings breakdown
  -q, --quiet              Summary line only (for CI)
  --exclude PATTERN        Exclude globs (repeatable)
  --list-rules             Show all rules
  --explain RULE_ID        Explain a specific rule
  --init                   Generate starter .promptlintrc
```

### Repo layout

```
cli/        Python CLI (this is the main thing)
landing/    Marketing site (Express + Supabase)
docs/       Config and rule documentation
vscode/     VS Code extension (planned)
```

### Inline ignores

Suppress a rule on a specific line:

```
Please write code  # promptlint-disable politeness-bloat
```

Or suppress everything on that line:

```
Please write code  # promptlint-disable
```

### Roadmap

- VS Code extension with inline linting
- Team presets (security-first, cost-first)
- Custom rule framework
- LLM framework integrations (LangChain, etc.)

### Security

- No API keys in the repo. Supabase/Resend credentials are loaded from `.env` files that are gitignored.
- All analysis is local. Nothing leaves your machine.
- The landing server only serves static files from `public/` and never exposes secrets to the browser.

### License

[Apache 2.0](LICENSE)
