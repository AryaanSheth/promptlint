# `completeness-edge-cases` — Edge Case Coverage

**Severity:** INFO · **Auto-fix:** No · **Category:** ✅ Completeness

## What It Does

Fires when a prompt contains a task verb but provides no guidance on error or edge-case handling. Prompts that only describe the happy path produce brittle behavior on unexpected inputs.

## Trigger Conditions

All three must be true:

1. **Task verb present** — the prompt contains `write`, `create`, `implement`, `build`, or `generate`
2. **No edge-case keywords** — none of: `edge case`, `error`, `exception`, `invalid`, `empty`, `null`, `missing`
3. **Prompt is more than 100 characters**

One finding is emitted for the whole prompt (line `-`).

::: tip Keyword-based detection
The rule matches any occurrence of the keyword anywhere in the prompt text. "Return null on empty input" contains `null` and `empty`, so it suppresses the finding. You don't need a dedicated `<edge_cases>` section — as long as one of the suppression keywords appears, the rule is satisfied.
:::

## Examples

::: danger No edge-case coverage
```
Write a function that parses a date string and returns an ISO 8601 date.
The input will be in MM/DD/YYYY format. Return the formatted date.
```

Finding:
```
[ INFO ] completeness-edge-cases (line -)
  Consider specifying how to handle edge cases and errors.
```
:::

::: tip With edge-case coverage — inline keyword suppresses the rule
```
Write a function that parses a date string and returns an ISO 8601 date.
The input will be in MM/DD/YYYY format.
Return null if the input is empty or invalid.
Raise a ValueError if the format cannot be parsed.
```
*(Contains `null`, `empty`, `invalid`, `error` → rule does not fire)*
:::

::: tip With explicit edge-case section
```
Write a function that parses a date string and returns an ISO 8601 date.
The input will be in MM/DD/YYYY format.

Edge cases:
- Empty string → return None
- Invalid format → raise ValueError with the original input
- Two-digit year → treat as 2000s if ≤ 25, else 1900s
- Null input → raise TypeError
```
*(Contains `edge case`, `empty`, `invalid`, `null` → rule does not fire)*
:::

## Common Edge Cases to Address

For **parsing tasks:**
- Empty or null input
- Malformed or unexpected format
- Boundary values (min/max length, date ranges, number limits)
- Encoding issues (non-ASCII, BOM characters)

For **transformation tasks:**
- Input with missing required fields
- Input with extra/unknown fields
- Type mismatches

For **generation tasks:**
- What to do when there is not enough context
- Fallback format if the preferred format cannot be produced
- Maximum output length behavior

For **retrieval/lookup tasks:**
- Not found — return null, empty list, or raise an error?
- Multiple matches — return all, return first, or raise?
- Partial match — return closest or nothing?

## False Positives

**Short prompts** — the 100-character threshold prevents the rule from firing on terse one-liners like "Write a haiku about autumn." which genuinely don't need edge-case guidance.

**Creative/open-ended prompts** — "Create a story about a detective" doesn't benefit from null/empty handling. Disable the rule for creative writing prompts:

```yaml
rules:
  completeness_edge_cases: false
```

**The keyword appears in a different context** — "Generate an error message for the user" contains `error`, which suppresses the rule even though no edge cases are defined. This is a known limitation of keyword-based detection.

## Configuration

```yaml
rules:
  completeness_edge_cases: true   # default: true
```

Disable:
```yaml
rules:
  completeness_edge_cases: false
```

The severity is fixed at INFO and cannot be promoted via config — use `--fail-level info` to make it block CI.
