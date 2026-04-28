# `specificity-examples` — Missing Examples

**Severity:** INFO · **Auto-fix:** No · **Category:** 🎯 Specificity

## What It Does

Fires when the prompt has no examples (few-shot demonstrations). Adding even one or two examples is the highest-ROI prompt improvement for output consistency.

## Example

**Prompt without examples:**
```
<task>Extract the sentiment and key topic from the review.</task>
<output_format>JSON with "sentiment" and "topic" keys.</output_format>
```

**Finding:**
```
[ INFO ] specificity-examples (line -)
  No examples provided. Adding 1-2 input/output pairs significantly
  improves output consistency and format adherence.
```

## How to Add Examples

```
<task>Extract the sentiment and key topic from the review.</task>

<examples>
Input: "The product arrived quickly but the packaging was damaged."
Output: {"sentiment": "mixed", "topic": "shipping and packaging"}

Input: "Absolutely love this! Works perfectly and great value."
Output: {"sentiment": "positive", "topic": "product quality and value"}
</examples>

<input>{{REVIEW_TEXT}}</input>
<output_format>JSON with "sentiment" and "topic" keys.</output_format>
```

## What Counts as Examples

The rule looks for:
- `<examples>` or `<example>` XML tags
- `Example:` or `Examples:` headings
- `Input:` / `Output:` pairs
- `Q:` / `A:` pairs
- Numbered examples (`1.`, `2.`)

## Configuration

```yaml
rules:
  specificity_examples: true

# Promote to WARN level:
rules:
  specificity_examples:
    enabled: true
    level: warn
```

## Why It Matters

Zero-shot vs. few-shot can be a 20–40% quality difference on classification and extraction tasks. The cost is a few extra tokens per call — almost always worth it.
