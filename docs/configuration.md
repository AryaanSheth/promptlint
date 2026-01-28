# Configuration Reference

Complete guide to configuring PromptLint via `.promptlintrc`.

## File Format

PromptLint uses YAML for configuration. Create a `.promptlintrc` file in your project root.

```yaml
# .promptlintrc
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

rules:
  # Your rule configuration here
```

## Global Settings

### `model`

**Type:** `string`  
**Default:** `gpt-4o`  
**Description:** Model name for token counting (used by tiktoken).

**Supported models:**
- `gpt-4o` (recommended)
- `gpt-4`
- `gpt-3.5-turbo`
- `text-davinci-003`
- Any OpenAI model supported by tiktoken

**Example:**
```yaml
model: gpt-4o
```

---

### `token_limit`

**Type:** `integer`  
**Default:** `800`  
**Description:** Maximum allowed tokens per prompt. Triggers CRITICAL alert if exceeded.

**Example:**
```yaml
token_limit: 800  # Alert if prompt > 800 tokens
```

---

### `cost_per_1k_tokens`

**Type:** `float`  
**Default:** `0.005`  
**Description:** Cost per 1,000 input tokens (in USD). Used for cost projections.

**Example:**
```yaml
cost_per_1k_tokens: 0.005  # $0.005 per 1K tokens (GPT-4o input pricing)
```

**Pricing reference (as of 2024):**
- GPT-4o: `0.005` (input), `0.015` (output)
- GPT-4: `0.03` (input), `0.06` (output)
- GPT-3.5-turbo: `0.0015` (input), `0.002` (output)

---

### `calls_per_day`

**Type:** `integer`  
**Default:** `1000000`  
**Description:** Expected API calls per day. Used for cost projections in dashboard.

**Important:** If set to 100,000 or higher, daily cost projections are hidden (considered unrealistic for most use cases).

**Example:**
```yaml
calls_per_day: 10000  # 10k calls/day = ~300k/month
```

---

### `structure_style`

**Type:** `string`  
**Default:** `auto`  
**Options:** `auto`, `xml`, `headings`, `markdown`, `none`  
**Description:** Preferred structure format for auto-fix scaffolding.

**Example:**
```yaml
structure_style: xml  # Auto-fix wraps prompts in <task> tags
```

**Options explained:**
- `auto`: Intelligently chooses based on existing prompt format
- `xml`: Use XML tags (`<task>`, `<context>`, `<output_format>`)
- `headings`: Use colons (`Task:`, `Context:`, `Output:`)
- `markdown`: Use Markdown headers (`## Task`, `## Context`)
- `none`: Don't add structure scaffolding

---

## Display Settings

Control output formatting.

```yaml
display:
  preview_length: 60
  context_width: 80
```

### `display.preview_length`

**Type:** `integer`  
**Default:** `60`  
**Description:** Maximum characters shown in finding context previews.

---

### `display.context_width`

**Type:** `integer`  
**Default:** `80`  
**Description:** Width of context lines in terminal output.

---

## Rules Configuration

All rules follow this structure:

```yaml
rules:
  rule_name:
    enabled: true
    # rule-specific options
```

### Enabling/Disabling Rules

**Enable a rule:**
```yaml
rules:
  politeness_bloat:
    enabled: true
```

**Disable a rule:**
```yaml
rules:
  politeness_bloat:
    enabled: false
```

**Disable all rules except specific ones:**
```yaml
rules:
  # Only run cost and security checks
  cost: true
  prompt_injection: true
  
  # Disable quality checks
  politeness_bloat: false
  clarity_vague_terms: false
  # ... etc
```

---

## Cost & Token Rules

### `cost`

Displays token count and cost per call.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  cost:
    enabled: true
```

**Output example:**
```
[ INFO ] cost (line -) Prompt is ~97 tokens (~$0.0005 input per call on gpt-4o).
At 10,000 calls/day -> ~$4.85/day input.
```

---

### `cost_limit`

Alerts if prompt exceeds `token_limit`.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  cost_limit:
    enabled: true
```

**Output example:**
```
[ CRITICAL ] cost-limit (line -) Prompt exceeds token limit: 850/800 tokens.
```

---

## Security Rules

### `prompt_injection`

Detects injection attack patterns.

**Options:**
- `enabled` (boolean): Enable/disable the rule
- `patterns` (list): Regex patterns to detect

```yaml
rules:
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - you are now a [a-zA-Z ]+
      - disregard all prior
      - forget everything
```

**Auto-fix:** When `--fix` is used, entire lines containing injection patterns are removed.

**Output example:**
```
[ CRITICAL ] prompt-injection (line 3) Injection pattern detected: 'ignore previous instructions'.
```

---

## Structure Rules

### `structure_sections`

Checks for organized prompt structure (replaces old `structure_tags` and `structure_delimiters`).

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  structure_sections:
    enabled: true
```

**What it detects:**
- ✅ XML tags (`<task>`, `<context>`)
- ✅ Headings (`Task:`, `Context:`, `Output:`)
- ✅ Markdown headers (`## Task`, `## Context`)
- ✅ JSON structure
- ✅ Code block delimiters (` ``` `)
- ✅ Numbered lists (`1. Task`, `2. Context`)

**Output if no structure found:**
```
[ WARN ] structure-sections (line -) No explicit sections detected (Task/Context/Output).
[ INFO ] structure-recommendations (line -) Recommended templates: headings (Task:, Context:, Output:) / XML tags (<task>) / Markdown (## sections).
```

**Backward compatibility:** Old config using `structure_tags` or `structure_delimiters` automatically maps to `structure_sections`.

---

## Quality Rules: Clarity

### `clarity_vague_terms`

Detects ambiguous, uncertain, subjective, or undefined terms.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  clarity_vague_terms:
    enabled: true
```

**Categories detected:**

| Category | Examples | Why It's Bad |
|----------|----------|--------------|
| **Vague quantifiers** | some, various, several, many, few, things, stuff | No clear quantity |
| **Uncertain language** | maybe, perhaps, possibly, might, could | AI doesn't know how to handle uncertainty |
| **Subjective terms** | good, nice, bad, better, simple, complex | No objective criteria |
| **Undefined standards** | appropriate, suitable, proper, relevant, adequate | What's "appropriate"? |

**Output examples:**
```
[ WARN ] clarity-vague-terms (line 1) Vague term 'some' detected (vague quantifier). Be more specific.
[ WARN ] clarity-vague-terms (line 1) Vague term 'maybe' detected (uncertain language). Be more specific.
[ WARN ] clarity-vague-terms (line 2) Vague term 'good' detected (subjective term). Be more specific.
```

---

## Quality Rules: Specificity

### `specificity_examples`

Suggests adding examples for clarity.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  specificity_examples:
    enabled: true
```

**Output example:**
```
[ INFO ] specificity-examples (line -) Consider adding examples to clarify expected output format.
```

---

### `specificity_constraints`

Suggests adding explicit constraints (length, format, scope).

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  specificity_constraints:
    enabled: true
```

**Output example:**
```
[ INFO ] specificity-constraints (line -) Consider adding constraints (length, format, scope) for clearer results.
```

---

## Quality Rules: Verbosity & Efficiency

### `politeness_bloat`

Detects unnecessary politeness words that add tokens without value.

**Options:**
- `enabled` (boolean): Enable/disable the rule
- `allow_politeness` (boolean): If `true`, makes this INFO-level instead of WARN
- `words` (list): Words to detect
- `savings_per_hit` (float): Estimated tokens saved per removal

```yaml
rules:
  politeness_bloat:
    enabled: true
    allow_politeness: false  # false = WARN (optimization focus), true = INFO (polite tone OK)
    words:
      - please
      - kindly
      - i would appreciate
      - thank you
      - be so kind as to
      - if possible
    savings_per_hit: 1.5
```

**Auto-fix:** Removes politeness words and common phrase fragments.

**Output examples:**

*With `allow_politeness: false` (default, token optimization focus):*
```
[ WARN ] politeness-bloat (line 1) Consider removing 'Please' (adds 1.5 tokens without semantic value).
```

*With `allow_politeness: true` (team prefers polite tone):*
```
[ INFO ] politeness-bloat (line 1) Optional: Remove 'Please' to save ~1.5 tokens.
```

---

### `verbosity_redundancy`

Detects redundant phrases that can be simplified.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  verbosity_redundancy:
    enabled: true
```

**Auto-fix replacements:**

| Redundant Phrase | Replacement | Tokens Saved |
|------------------|-------------|--------------|
| in order to | to | ~2 |
| due to the fact that | because | ~3 |
| at this point in time | now | ~3 |
| in the event that | if | ~2 |
| for the purpose of | for | ~2 |

**Output example:**
```
[ INFO ] verbosity-redundancy (line 1) Redundant phrase 'in order to' detected. Use simpler alternative.
```

---

### `verbosity_sentence_length`

Flags overly long sentences (40+ words).

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  verbosity_sentence_length:
    enabled: true
```

**Output example:**
```
[ INFO ] verbosity-sentence-length (line -) Long sentence detected (87 words). Consider breaking it up.
```

---

## Quality Rules: Actionability

### `actionability_weak_verbs`

Detects passive voice and weak language.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  actionability_weak_verbs:
    enabled: true
```

**Note:** Detection only, no auto-fix (requires full sentence parsing for grammatical correctness).

**Output example:**
```
[ INFO ] actionability-weak-verbs (line 2) Passive voice detected: 'is provided'. Consider active voice: 'provide'.
```

---

## Quality Rules: Consistency

### `consistency_terminology`

Detects mixed terminology (e.g., "user" vs "customer").

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  consistency_terminology:
    enabled: true
```

**Common inconsistencies detected:**
- user / customer / client
- function / method
- error / exception
- start / begin / initialize

**Output example:**
```
[ INFO ] consistency-terminology (line -) Mixed terminology: 'user' and 'customer'. Use one term consistently.
```

---

## Quality Rules: Completeness

### `completeness_edge_cases`

Reminds to specify error handling and edge cases.

**Type:** Boolean  
**Default:** `true`  

```yaml
rules:
  completeness_edge_cases:
    enabled: true
```

**Output example:**
```
[ INFO ] completeness-edge-cases (line -) Consider specifying how to handle edge cases and errors.
```

---

## Auto-Fix Configuration

Control which auto-fixes are applied with `--fix`.

```yaml
fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
```

### `fix.enabled`

**Type:** Boolean  
**Default:** `true`  
**Description:** Master switch for all auto-fixes.

---

### `fix.prompt_injection`

**Type:** Boolean  
**Default:** `true`  
**Description:** Remove entire lines containing injection patterns.

---

### `fix.politeness_bloat`

**Type:** Boolean  
**Default:** `true`  
**Description:** Remove politeness words and phrase fragments.

---

### `fix.verbosity_redundancy`

**Type:** Boolean  
**Default:** `true`  
**Description:** Replace redundant phrases with simpler alternatives.

---

### `fix.structure_scaffold`

**Type:** Boolean  
**Default:** `true`  
**Description:** Add missing structure tags based on `structure_style`.

---

## Complete Example Configuration

```yaml
# .promptlintrc - Production-ready configuration

# Model & Cost Settings
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

# Structure style for auto-fix
structure_style: xml

# Display Settings
display:
  preview_length: 60
  context_width: 80

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
      - disregard all prior
      - forget everything above

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
    allow_politeness: false  # Token optimization focus
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
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
```

## Team Presets

### Security-First Team

Focus on security, minimal quality checking.

```yaml
model: gpt-4o
token_limit: 1000

rules:
  cost: true
  cost_limit: true
  prompt_injection: true
  structure_sections: true
  
  # Disable quality checks
  clarity_vague_terms: false
  politeness_bloat: false
  verbosity_redundancy: false
```

### Cost-Optimization Team

Aggressive token reduction.

```yaml
model: gpt-4o
token_limit: 500  # Strict limit
calls_per_day: 50000  # High volume
cost_per_1k_tokens: 0.005

rules:
  cost: true
  cost_limit: true
  politeness_bloat:
    enabled: true
    allow_politeness: false  # Strict optimization
  verbosity_redundancy: true
  verbosity_sentence_length: true
  
  # Less focus on other checks
  clarity_vague_terms: false
  consistency_terminology: false
```

### Quality-First Team

Maximum prompt quality, less strict on tokens.

```yaml
model: gpt-4o
token_limit: 2000  # Generous limit

rules:
  # All quality checks enabled
  cost: true
  clarity_vague_terms: true
  specificity_examples: true
  specificity_constraints: true
  politeness_bloat:
    enabled: true
    allow_politeness: true  # Polite tone is OK
  consistency_terminology: true
  completeness_edge_cases: true
  actionability_weak_verbs: true
  structure_sections: true
```

---

## Configuration Testing

Test your config without running the full lint:

```bash
# Verify config loads
python -m promptlint.cli --config .promptlintrc --text "test" --format json

# Test with different config
python -m promptlint.cli --config configs/production.promptlintrc --file prompt.txt
```

## Troubleshooting

### Config not loading

**Problem:** PromptLint ignores your `.promptlintrc`

**Solution:** 
- Ensure file is in project root
- Check YAML syntax (use a YAML validator)
- Use `--config` flag explicitly: `python -m promptlint.cli --config .promptlintrc`

### Rules not working

**Problem:** Rules don't trigger expected warnings

**Solution:**
- Check rule is `enabled: true`
- Verify rule name matches exactly (use underscores, not hyphens)
- Old configs: `structure_tags` → use `structure_sections` instead

### Auto-fix too aggressive

**Problem:** `--fix` removes too much content

**Solution:**
```yaml
fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: false  # Disable this fix
  verbosity_redundancy: true
  structure_scaffold: false  # Disable this fix
```

---

## Next Steps

- **[Rules Reference](rules-reference.md)** - Detailed examples for each rule
- **[CLI Reference](cli-reference.md)** - Command-line options
- **[Best Practices](best-practices.md)** - How to write great prompts
