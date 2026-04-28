# `completeness-edge-cases` — Edge Case Coverage

**Severity:** INFO · **Auto-fix:** No · **Category:** ✅ Completeness

## What It Does

Fires when the prompt defines a task but provides no guidance on edge cases or failure modes. Prompts that only describe the happy path produce brittle behavior on boundary inputs.

## Example

::: danger No edge cases
```
<task>Parse the user's date of birth from the input string.</task>
<output_format>Return as ISO 8601 string (YYYY-MM-DD).</output_format>
```

Finding:
```
[ INFO ] completeness-edge-cases (line -)
  No edge cases defined. Consider specifying behavior for:
  invalid input, empty input, ambiguous values, boundary conditions.
```
:::

::: tip With edge cases
```
<task>Parse the user's date of birth from the input string.</task>
<edge_cases>
- If the input is empty or null, return null
- If the date is ambiguous (e.g., "01/02/03"), prefer DD/MM/YY format
- If the year is two digits (e.g., "85"), assume 1900s if > 25, else 2000s
- If parsing fails entirely, return {"error": "unparseable_date", "input": <original>}
</edge_cases>
<output_format>Return ISO 8601 string (YYYY-MM-DD) or null or error object.</output_format>
```
:::

## What Counts as Edge Case Coverage

The rule looks for:
- `<edge_cases>` or `<error_handling>` XML tag
- `Edge cases:`, `Error handling:`, `Failure modes:` headings
- Lines containing `if ... empty`, `if ... null`, `if ... invalid`, `if ... fails`
- `otherwise`, `fallback`, `on error`

## Configuration

```yaml
rules:
  completeness_edge_cases: true

# Promote to WARN for stricter enforcement:
rules:
  completeness_edge_cases:
    enabled: true
    level: warn
```

## Why It Matters

The happy path is easy. Production prompts handle:
- Empty or null input
- Malformed data
- Ambiguous values
- Rate limits or timeouts (if the prompt controls retry logic)
- Missing fields

Define these explicitly and your model's behavior becomes predictable.
