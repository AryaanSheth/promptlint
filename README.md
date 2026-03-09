## PromptLint

PromptLint is a prompt quality analyzer for teams shipping AI features. It detects
cost waste, quality issues, structural problems, and security risks before prompts reach production.
With **15+ intelligent checks** and **auto-fix capabilities**, PromptLint helps keep prompts
clear, efficient, and production‑ready.

### Repository structure

| Directory | Purpose |
|-----------|---------|
| **`cli/`** | Command-line tool (Python). Lint prompts from the terminal or CI. |
| **`vscode/`** | *(Planned)* VS Code extension for editor integration. |
| **`landing/`** | Static landing / marketing site served from a backend with environment-based config. |
| **`docs/`** | Project documentation (configuration, rules, integrations). |

### One‑line value prop
**Comprehensive prompt analysis with 15+ quality checks, auto-fix, and measurable cost savings.**

### Who it is for
- **Teams shipping AI features:** measurable savings and risk reduction with detailed analytics
- **Tech leads & platform owners:** comprehensive policy enforcement and fast CI integration
- **Developers & prompt engineers:** instant feedback with line‑level context and auto-fix suggestions

### What it does

#### 📊 Cost & Token Analysis
- **Token counting**: accurate token estimation for any model
- **Cost projection**: daily, monthly, and annual cost estimates
- **Limit enforcement**: catch prompts exceeding token budgets

#### 🔒 Security Checks
- **Injection detection**: catch "ignore previous instructions" and similar patterns
- **Pattern matching**: configurable security patterns for your threat model
- **Auto-removal**: optional automatic removal of injection attempts

#### 🏗️ Structure & Organization
- **XML tag validation**: enforce required tags like `<task>`, `<context>`, `<output_format>`
- **Delimiter checking**: ensure code blocks and sections are properly delimited
- **Auto-scaffolding**: automatically add missing structure tags

#### ✨ Quality: Clarity
- **Vague term detection**: flag ambiguous words like "some", "various", "things", "stuff"
- **Uncertain language**: catch hedging words like "maybe", "perhaps", "possibly"
- **Subjective terms**: identify undefined criteria like "good", "nice", "better"
- **Undefined standards**: flag terms like "appropriate", "suitable", "relevant"

#### 🎯 Quality: Specificity
- **Example suggestions**: prompt for examples when giving complex instructions
- **Constraint checking**: encourage explicit limits, formats, and scopes
- **Edge case prompts**: remind about error handling and boundary conditions

#### 📝 Quality: Verbosity & Efficiency
- **Politeness bloat**: remove unnecessary filler words ("please", "kindly", "thank you")
- **Redundancy detection**: catch phrases like "in order to" → "to", "due to the fact that" → "because"
- **Sentence length**: flag overly complex sentences (40+ words)
- **Auto-optimization**: automatically fix verbose patterns

#### 💪 Quality: Actionability
- **Passive voice detection**: encourage active voice for clearer instructions
- **Weak verb identification**: flag unclear or indirect language
- **Auto-strengthening**: convert passive constructions to active voice

#### 🔄 Quality: Consistency
- **Terminology checking**: detect mixed terms (user/customer, function/method, error/exception)
- **Format consistency**: ensure uniform styling throughout prompts

#### ✅ Quality: Completeness
- **Edge case reminders**: prompt for error handling specifications
- **Requirement coverage**: ensure all aspects of the task are addressed

### Quick start

Install the CLI first: `pip install -e ./cli` (from repo root) or `pip install -e .` from `cli/`. Then:

#### Basic analysis
```bash
promptlint --file my_prompt.txt
```

#### With cost dashboard
```bash
promptlint --file my_prompt.txt --show-dashboard
```

#### With auto-fix
```bash
promptlint --file my_prompt.txt --fix
```

#### Multi-file with globs
```bash
promptlint prompts/**/*.txt --exclude prompts/drafts/*
```

### Example output

Input prompt:
```
Please kindly write some code that does various things with maybe several functions.
The user should be provided with appropriate output that is nice and good.
In order to accomplish this task, it might be better if the error handling is done properly.
```

Output (abbreviated):
```
PromptLint Findings
[ INFO     ] cost (line -) Prompt is ~38 tokens (~$0.0002 input per call on gpt-4o).
[ WARN     ] structure-sections (line -) No explicit sections detected (Task/Context/Output).
[ WARN     ] clarity-vague-terms (line 1) Vague term 'some' detected (vague quantifier). Be more specific.
[ WARN     ] clarity-vague-terms (line 1) Vague term 'various' detected (vague quantifier). Be more specific.
[ WARN     ] clarity-vague-terms (line 2) Vague term 'maybe' detected (uncertain language). Be more specific.
[ INFO     ] verbosity-redundancy (line 3) Redundant phrase 'In order to' detected. Use simpler alternative.
[ WARN     ] politeness-bloat (line 1) Consider removing 'Please' (adds 1.5 tokens without semantic value).
[ INFO     ] specificity-examples (line -) Consider adding examples to clarify expected output format.

1 file(s) scanned, 12 finding(s) in 0.42s
```

With `--fix --show-dashboard`:
```
Savings Dashboard
Current Tokens: 38
Optimized Tokens: 22 (42.1% reduction)
Savings per Call: ~$0.0001

Optimized Prompt
<task>Write code that does various things with maybe several functions.
The user should be provided with appropriate output that is nice and good.
To accomplish this task, it might be better if the error handling is done properly.</task>
```

### Output modes
- **Text output** (default): fast, readable, terminal‑safe
- **JSON output**: `--format json` for CI or analytics dashboards
- **Fix mode**: `--fix` removes bloat, fixes redundancy, and adds structure

### CI / pre‑commit ready
```bash
promptlint prompts/system.txt --fail-level warn --quiet
```

Exit codes:
- `none` → always 0
- `warn` → exit 1 on WARN or CRITICAL
- `critical` → exit 2 on CRITICAL

### Configuration (`.promptlintrc`)

PromptLint is fully configurable per team or repo. All 15+ rules can be enabled or disabled individually.

```yaml
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

# Structure style for auto-fix: auto, xml, headings, markdown, none
structure_style: auto

# Rules Configuration
rules:
  # Cost & Token Analysis
  cost:
    enabled: true
  cost_limit:
    enabled: true

  # Security Checks
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - you are now a [a-zA-Z ]+

  # Structure & Organization
  structure_sections:
    enabled: true

  # Quality: Clarity
  clarity_vague_terms:
    enabled: true

  # Quality: Specificity
  specificity_examples:
    enabled: true
  specificity_constraints:
    enabled: true

  # Quality: Verbosity & Efficiency
  politeness_bloat:
    enabled: true
    words:
      - please
      - kindly
      - i would appreciate
      - thank you
      - be so kind as to
      - if possible
    savings_per_hit: 1.5
  verbosity_sentence_length:
    enabled: true
  verbosity_redundancy:
    enabled: true

  # Quality: Actionability
  actionability_weak_verbs:
    enabled: true

  # Quality: Consistency
  consistency_terminology:
    enabled: true

  # Quality: Completeness
  completeness_edge_cases:
    enabled: true

# Auto-fix Configuration
fix:
  enabled: true
  # Security fixes
  prompt_injection: true
  # Quality fixes
  politeness_bloat: true
  verbosity_redundancy: true
  # actionability_weak_verbs: true  # Detection only, no auto-fix
  # Structure fixes
  structure_scaffold: true
```

### Why it matters
- **Clear ROI:** measurable token savings and cost projections (up to 50% reduction)
- **Risk reduction:** 15+ quality checks and injection detection before release
- **Developer experience:** line‑level feedback with caret context and auto-fix mode
- **Operational fit:** runs locally or in CI with no dependency on external services

### Installation

Install the CLI from the `cli/` package:

```bash
pip install -e ./cli
```

From inside `cli/` you can also run:

```bash
pip install -r requirements.txt
pip install -e .
```

See `cli/README.md` for run and config details.

### CLI options

```bash
promptlint [FILES...] [OPTIONS]

Options:
  -V, --version            Show version and exit
  --file, -f PATH          Single prompt file path
  --text, -t TEXT          Inline prompt text
  --config, -c PATH        Config file path (default: .promptlintrc)
  --format {text,json}     Output format (default: text)
  --fix                    Apply auto-fixes and print optimized prompt
  --fail-level LEVEL       Exit on level: none, warn, critical (default: critical)
  --show-dashboard         Include savings dashboard in output
  --quiet, -q              Suppress findings; print summary line only (CI mode)
  --exclude PATTERN        Glob pattern(s) to exclude (repeatable)
  --list-rules             List all available rules and exit
  --explain RULE_ID        Show detailed explanation of a rule and exit
  --init                   Generate a starter .promptlintrc
```

You can also pipe input: `echo "my prompt" | promptlint --format json`

## Features at a glance

| Category | Feature | Detection | Auto-fix |
|----------|---------|-----------|----------|
| 💰 Cost | Token counting | ✅ | - |
| 💰 Cost | Cost projection | ✅ | - |
| 💰 Cost | Token limits | ✅ | - |
| 🔒 Security | Injection patterns | ✅ | ✅ |
| 🏗️ Structure | XML tags | ✅ | ✅ |
| 🏗️ Structure | Delimiters | ✅ | - |
| ✨ Clarity | Vague terms | ✅ | - |
| ✨ Clarity | Uncertain language | ✅ | - |
| 🎯 Specificity | Missing examples | ✅ | - |
| 🎯 Specificity | Missing constraints | ✅ | - |
| 📝 Efficiency | Politeness bloat | ✅ | ✅ |
| 📝 Efficiency | Redundant phrases | ✅ | ✅ |
| 📝 Efficiency | Long sentences | ✅ | - |
| 💪 Actionability | Passive voice | ✅ | - |
| 🔄 Consistency | Mixed terminology | ✅ | - |
| ✅ Completeness | Edge cases | ✅ | - |

**Total: 15+ checks, 5 auto-fixable**

## Roadmap ideas
- Team presets (security‑first, cost‑first, quality‑first)
- Batch processing for multiple prompt files
- VSCode extension with real-time linting
- Advanced NLP-based quality scoring
- Custom rule creation framework
- Prompt library with best practices
- Integration with popular LLM frameworks

## Security & privacy
- **No API keys in the repo:** all provider keys (for example, Supabase or Resend) are supplied via environment variables or local config files that are gitignored.
- **Local‑only analysis:** prompt text is analyzed locally by the CLI; you control when and where prompts are stored.
- **Landing app safety:** the `landing/` backend reads Supabase and email credentials from `.env`/`.config` files only and never exposes them to the browser.

## License

Licensed under the [Apache License, Version 2.0](LICENSE).
