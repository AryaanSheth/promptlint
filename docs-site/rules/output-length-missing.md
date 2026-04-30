# `output-length-missing` — Output Length Constraint

**Severity:** INFO · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Detects prompts that contain a task verb (write, generate, list, etc.) but don't specify how long the output should be. Without a length constraint, response length varies unpredictably between model versions, calls, and providers — a consistent response length requires an explicit constraint.

## Trigger Conditions

::: warning Three conditions must all be true
1. The prompt is **at least 80 characters long**
2. The prompt contains a **task verb** from the list below
3. The prompt does **not** contain any **length constraint** from the list below
:::

## Task Verbs (trigger the check)

`write`, `create`, `implement`, `build`, `generate`, `list`, `extract`, `return`, `output`, `summarize`, `describe`, `explain`, `produce`, `draft`, `compose`

## Length Constraint Keywords (suppress the check)

| Pattern | Examples |
|---------|---------|
| Explicit counts | `200 words`, `3 sentences`, `5 bullet points`, `50 tokens` |
| Maximum/limit | `max 100 words`, `maximum length`, `word limit`, `token limit` |
| Brevity directives | `be brief`, `be concise`, `keep it short`, `succinct`, `terse` |
| Relative bounds | `no more than 300 words`, `at most 3 paragraphs`, `up to 5 items` |
| Other | `truncate`, `limited to 200`, `in 3 points` |

## Examples

::: danger Triggers the rule
```
Write a detailed explanation of how transformers work in neural networks.
Include the attention mechanism, positional encoding, and layer normalization.
```
Has `write` — no length constraint. Output could be 100 or 2,000 words.

```
[ INFO ] output-length-missing (line -)
  No output length constraint specified. Add a word/token/sentence limit
  for consistent response lengths.
```
:::

::: tip Passes the rule
```
Write a detailed explanation of how transformers work in neural networks
in no more than 300 words. Cover the attention mechanism, positional
encoding, and layer normalization.
```
Has `no more than 300 words` → no finding.

```
Create a 5-bullet summary of the document below.
```
Has `5-bullet` → no finding.

```
Generate a concise overview of the project status.
```
Has `concise` → no finding.
:::

## False Positives

**Short prompts** — prompts under 80 characters don't fire this rule. `Write a haiku about rain` (24 chars) won't trigger.

**Prompts with implicit constraints** — "Write a tweet announcing the launch" implicitly requires brevity (Twitter's 280-char limit), but promptlint doesn't understand domain conventions. Add "in 240 characters or fewer" to be explicit.

**Template variables** — if your length constraint is injected via a variable (`{length_limit}`), promptlint won't see it. Use `# promptlint-disable output-length-missing` to suppress.

## Configuration

```yaml
rules:
  output_length_missing: true   # or false to disable
```

Promote to WARN:
```yaml
rules:
  output_length_missing:
    enabled: true
    severity: warn
```

Disable for a single prompt:
```
Write an essay about climate change.
# promptlint-disable output-length-missing
```

## Recommended Fix

Add an explicit length boundary in one of these forms:

```
# Word count
Write a 200-word summary of the following document.

# Sentence count
Explain the concept in 3 sentences.

# Bullet points
List the key advantages in 5 bullet points.

# Token budget (for API cost control)
Summarize the article in at most 100 tokens.

# Brevity directive
Describe the architecture. Be concise.
```

For production prompts, word counts or token limits are preferable over brevity directives — they're more precise and work consistently across model versions.

## Why Length Constraints Matter

Without a length constraint:
- A model update can silently change average response length by 30–50%
- Responses in production vary from a single sentence to multiple paragraphs for the same prompt
- Long responses increase latency and token cost unexpectedly
- Short responses may miss required content
- Downstream parsing that expects a fixed structure becomes brittle

Adding a length constraint doesn't prevent good answers — it creates a contract between your prompt and the model, making outputs auditable and reproducible.
