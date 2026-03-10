---
name: promptlint
description: Lint and improve LLM prompts using the promptlint CLI. Use when writing, reviewing, or optimizing prompts for GPT-4, Claude, Gemini, or any LLM — whether in plain text files or embedded in Python/TypeScript code. Activates when the user writes prompts, asks to optimize or review a prompt, mentions prompt injection, or works with LangChain/OpenAI/Anthropic SDK code containing prompt strings.
---

# PromptLint — Agent Skill

Promptlint is a static analyzer for LLM prompts. It catches token waste, vague language, prompt injection, missing structure, and other issues. Runs locally, no API calls.

## Installation

```bash
pip install promptlint-cli              # base install
pip install promptlint-cli[tiktoken]    # adds exact BPE token counting
```

## Prompt Conventions

Follow these conventions so promptlint can analyze prompts effectively.

### Preferred: separate prompt files

Store prompts as plain text in a `prompts/` directory:

```
prompts/
├── system.txt
├── summarize.txt
├── extract-entities.txt
└── code-review.txt
```

Lint the whole directory at once:

```bash
promptlint prompts/
```

### In-code prompts

When prompts are embedded in `.py` or `.ts` files, extract the string and use `--text`:

```bash
promptlint -t "You are a helpful assistant that summarizes articles in 3 bullet points."
```

For multi-line prompts, pipe them via stdin:

```bash
echo "Your long prompt..." | promptlint --format json
```

### Template prompts with variables

For prompts containing `{user_input}`, `{{context}}`, or f-string placeholders, substitute realistic sample values before linting. This gives accurate token counts and surfaces issues that only appear with real content.

Example — if the source code has:

```python
PROMPT = f"Summarize the following article in {num_points} bullet points:\n{article_text}"
```

Lint with a realistic substitution:

```bash
promptlint -t "Summarize the following article in 5 bullet points:
The Federal Reserve announced today that interest rates will remain unchanged..."
```

## Lint-and-Fix Loop

When asked to improve a prompt, run this iterative loop:

### Step 1: Run promptlint

```bash
promptlint --file prompt.txt --format json
```

Or inline:

```bash
promptlint -t "the prompt text" --format json
```

### Step 2: Read findings by priority

Fix in this order:

| Priority | Level | Rules | Action |
|----------|-------|-------|--------|
| 1 | CRITICAL | `prompt-injection` | Remove or rewrite the flagged line immediately |
| 2 | WARN | `clarity-vague-terms` | Replace vague words ("some", "stuff", "good") with specific terms |
| 2 | WARN | `structure-sections` | Add XML tags, markdown headers, or numbered sections |
| 2 | WARN | `politeness-bloat` | Remove "please", "kindly", "thank you" |
| 3 | INFO | `verbosity-redundancy` | Simplify: "in order to" → "to", "due to the fact that" → "because" |
| 3 | INFO | `specificity-examples` | Add concrete examples of expected input/output |
| 3 | INFO | `specificity-constraints` | Add explicit length, format, or scope limits |
| 3 | INFO | `completeness-edge-cases` | Specify error/edge-case handling |
| 3 | INFO | `consistency-terminology` | Pick one term and use it everywhere (user vs customer) |
| 3 | INFO | `actionability-weak-verbs` | Rewrite passive voice to active voice |
| 3 | INFO | `verbosity-sentence-length` | Split sentences longer than 40 words |

### Step 3: Apply auto-fixes first

```bash
promptlint --file prompt.txt --fix
```

This auto-removes politeness filler, simplifies redundant phrases, strips injection lines, and scaffolds missing XML sections. Use the output as the starting point for manual fixes.

### Step 4: Fix remaining manual findings

Edit the prompt to address WARN and INFO findings that `--fix` cannot handle (vague terms, missing examples, passive voice).

### Step 5: Re-run and verify

```bash
promptlint --file prompt.txt
```

Repeat until no CRITICAL or WARN findings remain. INFO findings are advisory — address them if practical.

### Example loop

```bash
# Initial scan
promptlint -t "Please kindly write a function that does some stuff with various inputs"
# Findings: politeness-bloat (x2), clarity-vague-terms (x3), structure-sections

# Auto-fix pass
promptlint -t "Please kindly write a function that does some stuff with various inputs" --fix
# Output: <task>Write a function that does some stuff with various inputs.</task>

# Manual fix: replace vague terms
promptlint -t "<task>Write a Python function that accepts a list of integers and returns the sum of all even numbers. Handle empty lists by returning 0.</task>"
# Result: 0 CRITICAL, 0 WARN, 1 INFO (specificity-examples) — acceptable
```

## Extracting Prompts from Code

When working with prompts embedded in framework code, use this approach:

### Common patterns to look for

**OpenAI SDK:**
```python
client.chat.completions.create(
    messages=[{"role": "system", "content": "THE PROMPT STRING"}]
)
```

**Anthropic SDK:**
```python
anthropic.messages.create(
    system="THE PROMPT STRING",
    messages=[{"role": "user", "content": "THE PROMPT STRING"}]
)
```

**LangChain:**
```python
ChatPromptTemplate.from_messages([
    ("system", "THE PROMPT STRING"),
    ("user", "{user_input}")
])
```

**Named variables (any framework):**
```python
SYSTEM_PROMPT = "THE PROMPT STRING"
SUMMARIZE_TEMPLATE = "THE PROMPT STRING"
```

### Extraction workflow

1. Identify prompt strings in the code using the patterns above
2. Extract the literal string content (strip f-string prefixes, replace template variables with samples)
3. Run `promptlint -t "extracted content" --format json`
4. Read the JSON findings and apply fixes back to the source code
5. Re-run to verify

Do NOT lint the entire code file — only extract and lint the prompt strings themselves.

## All Rules Reference

| Rule | Category | Severity | Fixable | What it checks |
|------|----------|----------|---------|----------------|
| `cost` | Cost & Tokens | INFO | — | Token count and cost-per-call estimate |
| `cost-limit` | Cost & Tokens | WARN | — | Alert when prompt exceeds configured token limit |
| `prompt-injection` | Security | CRITICAL | yes | Injection patterns with leetspeak/unicode normalization |
| `structure-sections` | Structure | WARN | yes | Verifies explicit sections (XML, headings, numbered lists) |
| `clarity-vague-terms` | Quality | WARN | — | Flags "some", "stuff", "maybe", "good", "appropriate" |
| `specificity-examples` | Quality | INFO | — | Suggests adding examples for complex instructions |
| `specificity-constraints` | Quality | INFO | — | Suggests adding length/format/scope constraints |
| `politeness-bloat` | Efficiency | WARN | yes | Flags "please", "kindly", "thank you" (wastes tokens) |
| `verbosity-sentence-length` | Efficiency | INFO | — | Flags sentences over 40 words |
| `verbosity-redundancy` | Efficiency | INFO | yes | "in order to" → "to", "due to the fact that" → "because" |
| `actionability-weak-verbs` | Quality | INFO | — | Flags excessive passive voice |
| `consistency-terminology` | Quality | INFO | — | Catches mixed terms (user/customer, function/method) |
| `completeness-edge-cases` | Quality | INFO | — | Reminds you to specify error/edge-case handling |

Use `promptlint --explain <rule-id>` for detailed docs on any rule.

## CLI Quick Reference

```
promptlint [FILES...] [OPTIONS]

Input:
  -f, --file PATH          Single prompt file
  -t, --text TEXT          Inline prompt text
  (stdin)                  Pipe text via stdin

Output:
  --format {text,json}     Output format (json for programmatic use)
  --show-dashboard         Token savings breakdown
  -q, --quiet              Summary line only (for CI)

Fixing:
  --fix                    Auto-fix and print optimized prompt

Configuration:
  -c, --config PATH        Config file (default: .promptlintrc)
  --fail-level LEVEL       none / warn / critical (default: critical)
  --exclude PATTERN        Exclude globs (repeatable)

Info:
  -V, --version            Show version
  --list-rules             Show all rules
  --explain RULE_ID        Explain a specific rule
  --init                   Generate starter .promptlintrc
```

## Configuration

Generate a starter config:

```bash
promptlint --init
```

Key settings in `.promptlintrc`:

```yaml
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005

rules:
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - "you are now a [a-zA-Z ]+"
  politeness_bloat:
    enabled: true
    words: [please, kindly, thank you, if possible]
  structure_sections:
    enabled: true

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
```

## Security Notes

The injection detection normalizes text before matching to catch evasion attempts:
- **Leetspeak**: `1gn0r3 pr3v10u$ 1nstruct10ns` → detected
- **Zero-width chars**: invisible unicode characters are stripped
- **Character repetition**: `ignoooore` → normalized and detected
- **Unicode confusables**: Cyrillic/Latin lookalikes are collapsed

Custom patterns can be added in `.promptlintrc` under `rules.prompt_injection.patterns` as regex strings.
