# `specificity-examples` — Missing Examples

**Severity:** INFO · **Auto-fix:** No · **Category:** 🎯 Specificity

## What It Does

Detects prompts that contain a creative/generative instruction but provide no examples of the expected output. Few-shot examples are the highest-ROI prompt improvement for output consistency on generation tasks.

## Trigger Conditions

::: warning Three conditions must all be true
1. The prompt is **longer than 100 characters**
2. The prompt contains at least one **generative instruction verb**: `write`, `create`, `generate`, `build`, `implement`, `design`
3. The prompt does **not** contain an **example indicator**: `example`, `e.g.`, `such as`, `like`, `for instance`
:::

This is a heuristic, not structural detection. The rule doesn't parse for `<examples>` sections — it looks for the keyword `example` (or synonyms) anywhere in the prompt text.

## Examples

::: danger Triggers the rule
```
Write a Python function that validates email addresses and returns a
tuple of (is_valid: bool, error_message: str).
```
Contains `write` (generative verb), no `example` keyword, > 100 chars.

```
[ INFO ] specificity-examples (line -)
  Consider adding examples to clarify expected output format.
```
:::

::: tip Passes the rule
```
Write a Python function that validates email addresses.

Examples:
  validate("user@example.com")  → (True, "")
  validate("not-an-email")      → (False, "missing @ symbol")
  validate("")                  → (False, "empty input")
```
Contains `examples` → no finding.
:::

## False Positives

**Prompts about writing style** — "Write a formal email" is short and won't fire (< 100 chars usually). "Write a comprehensive formal business email for a client who has missed two invoice payments" is > 100 chars, has `write`, and will fire. Whether you need examples here is debatable.

**`like` as a non-example word** — "Generate output like JSON but simpler" contains `like`, so it suppresses the rule even though no actual examples are given. This is intentional — the word `like` signals an informal comparison that serves a similar purpose.

**`design` in non-generative context** — "What are the design principles of REST APIs?" contains `design` but it's a question, not a generation task. The rule will still fire because it looks for the keyword, not the grammatical role. The false-positive rate for this verb is higher than for `write` or `generate`.

## Configuration

```yaml
rules:
  specificity_examples: true

# Promote to WARN for stricter enforcement:
rules:
  specificity_examples:
    enabled: true
    level: warn
```

Disable:
```yaml
rules:
  specificity_examples: false
```

## When to Add Examples

Examples have the biggest impact when:
- The output **format** needs to be precise (JSON schema, specific string pattern)
- The output **style** needs to be consistent (tone, vocabulary, length)
- The task involves **classification or extraction** where label choices matter

Diminishing returns when:
- The task is a one-off generation (brainstorming, creative writing)
- The model's default behavior for that task already matches your needs
- Adding examples would consume too many tokens relative to the benefit

## How to Add Effective Examples

```
<task>Extract action items and owners from meeting notes.</task>

<examples>
Input: "Sarah will follow up with the vendor by EOW"
Output: {"action": "follow up with vendor", "owner": "Sarah", "due": "end of week"}

Input: "John to schedule quarterly review next month"
Output: {"action": "schedule quarterly review", "owner": "John", "due": "next month"}

Input: "No action items"
Output: []
</examples>

<input>{{MEETING_NOTES}}</input>
<output_format>JSON array. Return [] if no action items found.</output_format>
```
