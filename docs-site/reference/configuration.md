# Configuration Reference

Complete reference for `.promptlintrc` — PromptLint's YAML configuration file.

## File Discovery

PromptLint searches for `.promptlintrc` starting in the current directory, walking up to the filesystem root. You can override this with `--config`:

```bash
promptlint --file prompt.txt --config /path/to/.promptlintrc
```

## Schema

```yaml
# .promptlintrc

model: string             # default: "gpt-4o"
token_limit: integer      # default: 800
cost_per_1k_tokens: float # default: 0.005
calls_per_day: integer    # default: 1000000

structure_style: string   # default: "auto"

display:
  preview_length: integer # default: 60
  context_width: integer  # default: 80

rules:
  <rule_id>: boolean | RuleConfig

fix:
  enabled: boolean           # default: true
  prompt_injection: boolean  # default: true
  politeness_bloat: boolean  # default: true
  verbosity_redundancy: boolean  # default: true
  structure_scaffold: boolean    # default: true
  normalize_spacing: boolean     # default: true
```

## `model`

**Type:** string · **Default:** `"gpt-4o"`

Passed to `tiktoken.encoding_for_model()`. Any OpenAI model name works. For non-OpenAI models, tiktoken falls back to `cl100k_base` encoding.

```yaml
model: gpt-4o
```

## `token_limit`

**Type:** integer · **Default:** `800`

Triggers `cost-limit` CRITICAL when exceeded.

```yaml
token_limit: 500
```

## `cost_per_1k_tokens`

**Type:** float · **Default:** `0.005`

Input token cost in USD per 1,000 tokens.

```yaml
cost_per_1k_tokens: 0.005  # GPT-4o input
```

## `calls_per_day`

**Type:** integer · **Default:** `1000000`

Used for cost projection. If ≥ 100,000, daily projections are hidden.

```yaml
calls_per_day: 10000
```

## `structure_style`

**Type:** `"auto"` | `"xml"` | `"headings"` | `"markdown"` | `"none"` · **Default:** `"auto"`

Controls auto-fix scaffold format for `structure-sections`.

```yaml
structure_style: xml
```

## `display`

```yaml
display:
  preview_length: 60  # chars shown in finding context preview
  context_width: 80   # terminal wrap width
```

## `rules`

Each rule ID (using underscores) can be set to:
- `true` — enabled with default settings
- `false` — disabled
- An object with `enabled` and optional overrides

```yaml
rules:
  # Simple toggle
  cost: true
  actionability_weak_verbs: false

  # Severity override
  specificity_examples:
    enabled: true
    level: warn          # "critical" | "warn" | "info"

  # Custom patterns
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - admin override:

  # PII sub-checks
  pii_in_prompt:
    enabled: true
    check_email: true
    check_phone: true
    check_ssn: true
    check_credit_card: true

  # Politeness mode
  politeness_bloat:
    enabled: true
    allow_politeness: false  # true = demote to INFO
```

### Rule ID Mapping

Config uses underscores; rule IDs in findings use hyphens:

| Config key | Rule ID |
|-----------|---------|
| `cost` | `cost` |
| `cost_limit` | `cost-limit` |
| `prompt_injection` | `prompt-injection` |
| `jailbreak_pattern` | `jailbreak-pattern` |
| `secret_in_prompt` | `secret-in-prompt` |
| `pii_in_prompt` | `pii-in-prompt` |
| `context_injection_boundary` | `context-injection-boundary` |
| `structure_sections` | `structure-sections` |
| `role_clarity` | `role-clarity` |
| `output_format_missing` | `output-format-missing` |
| `hallucination_risk` | `hallucination-risk` |
| `clarity_vague_terms` | `clarity-vague-terms` |
| `specificity_examples` | `specificity-examples` |
| `specificity_constraints` | `specificity-constraints` |
| `politeness_bloat` | `politeness-bloat` |
| `verbosity_redundancy` | `verbosity-redundancy` |
| `verbosity_sentence_length` | `verbosity-sentence-length` |
| `actionability_weak_verbs` | `actionability-weak-verbs` |
| `consistency_terminology` | `consistency-terminology` |
| `completeness_edge_cases` | `completeness-edge-cases` |

## `fix`

Controls which auto-fixes are applied when `--fix` is passed.

```yaml
fix:
  enabled: true                # master switch
  prompt_injection: true       # remove injection lines
  politeness_bloat: true       # remove politeness words
  verbosity_redundancy: true   # collapse redundant phrases
  structure_scaffold: true     # add structure tags
  normalize_spacing: true      # clean blank lines
```
