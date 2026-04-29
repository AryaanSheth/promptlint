# Configuration

PromptLint is configured via a `.promptlintrc` YAML file in your project root. All settings are optional — sensible defaults are applied automatically.

## Minimal Config

```yaml
# .promptlintrc
model: gpt-4o
token_limit: 800
```

## Full Reference

```yaml
# .promptlintrc

# ── Global ──────────────────────────────────────────────────────
model: gpt-4o           # tiktoken model for exact token counts
token_limit: 800        # CRITICAL if prompt exceeds this
cost_per_1k_tokens: 0.005  # USD per 1k input tokens
calls_per_day: 10000    # for cost projection

structure_style: auto   # "xml" | "headings" | "markdown" | "auto" | "none"

display:
  preview_length: 60    # chars to show in finding preview
  context_width: 80     # terminal width for wrapping

# ── Rules ────────────────────────────────────────────────────────
rules:
  # Cost
  cost: true
  cost_limit: true

  # Security
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - you are now a [a-zA-Z ]+
      - disregard all prior
      - forget everything
      - new instructions:
  jailbreak_pattern: true
  secret_in_prompt: true
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: true
    check_ssn: true
    check_credit_card: true
  context_injection_boundary: true

  # Structure
  structure_sections: true
  role_clarity: true
  output_format_missing: true
  hallucination_risk: true

  # Quality
  clarity_vague_terms: true
  specificity_examples: true
  specificity_constraints: true
  politeness_bloat:
    enabled: true
    allow_politeness: false
  verbosity_redundancy: true
  verbosity_sentence_length: true
  actionability_weak_verbs: true
  consistency_terminology: true
  completeness_edge_cases: true

# ── Auto-fix ────────────────────────────────────────────────────
fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
  normalize_spacing: true
```

## Global Settings

### `model`

**Type:** `string` · **Default:** `gpt-4o`

The tiktoken model used for exact token counting. Any model supported by tiktoken works.

```yaml
model: gpt-4o
# model: gpt-4
# model: gpt-3.5-turbo
# model: claude-3-5-sonnet-20241022  # falls back to cl100k_base
```

### `token_limit`

**Type:** `integer` · **Default:** `800`

Triggers `cost-limit` (CRITICAL) when the prompt exceeds this count. Set to 60–70% of your model's context window to leave room for completions.

```yaml
token_limit: 800   # GPT-4o has 128k context; 800 keeps system prompts lean
```

### `cost_per_1k_tokens`

**Type:** `float` · **Default:** `0.005`

Input token price in USD per 1,000 tokens. Used by the `cost` rule to project spend.

| Model | Input price |
|-------|------------|
| GPT-4o | `0.005` |
| GPT-4o mini | `0.00015` |
| GPT-4 | `0.03` |
| GPT-3.5 Turbo | `0.0015` |
| Claude 3.5 Sonnet | `0.003` |
| Claude 3 Haiku | `0.00025` |

### `calls_per_day`

**Type:** `integer` · **Default:** `1000000`

Used to project daily and monthly cost savings. If ≥ 100,000, cost projections are suppressed (considered a load test scenario).

### `structure_style`

**Type:** `string` · **Default:** `auto`

Controls what format the `structure-sections` auto-fix scaffolds:

| Value | Effect |
|-------|--------|
| `xml` | Wraps in `<task>`, `<context>`, `<output_format>` tags |
| `headings` | Adds `Task:`, `Context:`, `Output Format:` headings |
| `markdown` | Adds `## Task`, `## Context`, `## Output Format` sections |
| `auto` | Detects existing style and matches it |
| `none` | Disables auto-fix scaffolding |

## Rule Configuration

Each rule can be enabled/disabled and have its severity overridden:

```yaml
rules:
  # Simple toggle
  completeness_edge_cases: false

  # Override severity
  specificity_examples:
    enabled: true
    level: warn   # promote from INFO → WARN

  # Custom patterns (prompt-injection)
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - admin override:
      - bypass safety
```

### Disable a Rule

```yaml
rules:
  actionability_weak_verbs: false
  verbosity_sentence_length: false
```

### Severity Override

```yaml
rules:
  specificity_examples:
    enabled: true
    level: warn    # or "critical", "info"
```

## Team Presets

### Security-First

```yaml
model: gpt-4o
token_limit: 1000

rules:
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - you are now a [a-zA-Z ]+
      - admin mode
      - bypass restrictions
  jailbreak_pattern: true
  secret_in_prompt: true
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: true
    check_ssn: true
    check_credit_card: true
  context_injection_boundary: true
  cost: false
  specificity_examples: false
  specificity_constraints: false
  completeness_edge_cases: false
```

### Cost-First

```yaml
model: gpt-4o
token_limit: 400
cost_per_1k_tokens: 0.005
calls_per_day: 50000

rules:
  cost: true
  cost_limit: true
  politeness_bloat: true
  verbosity_redundancy: true
  verbosity_sentence_length: true
  prompt_injection: true
  structure_sections: false
  specificity_examples: false
  completeness_edge_cases: false

fix:
  enabled: true
  politeness_bloat: true
  verbosity_redundancy: true
```

### Quality-First

```yaml
model: gpt-4o

rules:
  structure_sections: true
  role_clarity: true
  output_format_missing: true
  hallucination_risk: true
  clarity_vague_terms: true
  specificity_examples:
    enabled: true
    level: warn
  specificity_constraints:
    enabled: true
    level: warn
  completeness_edge_cases:
    enabled: true
    level: warn
  actionability_weak_verbs:
    enabled: true
    level: warn
  cost: false
  cost_limit: false
```

## Config File Location

PromptLint searches for `.promptlintrc` starting from the current directory, walking up to the filesystem root (similar to ESLint). You can also pass a config explicitly:

```bash
promptlint --file prompt.txt --config /path/to/custom.yaml
```
