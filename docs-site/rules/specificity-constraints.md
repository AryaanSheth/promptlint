# `specificity-constraints` — Missing Constraints

**Severity:** INFO · **Auto-fix:** No · **Category:** 🎯 Specificity

## What It Does

Fires when the prompt has no negative constraints — no "do not", "avoid", "must not", or `<constraints>` section. Models need to know what **not** to do as much as what to do.

## Example

**Prompt without constraints:**
```
<task>Write a Python function to parse JSON from a string.</task>
<output_format>Python code.</output_format>
```

**Finding:**
```
[ INFO ] specificity-constraints (line -)
  No constraints defined. Consider adding a <constraints> section
  specifying what the model should NOT do (e.g., "Do not use third-party libraries").
```

**With constraints:**
```
<task>Write a Python function to parse JSON from a string.</task>
<constraints>
- Use only the standard library (no third-party packages)
- Do not add docstrings or comments
- Do not print anything to stdout
- Return None on parse failure (do not raise exceptions)
</constraints>
<output_format>Python code only. No explanation.</output_format>
```

## What Counts as Constraints

- `<constraints>` or `<restrictions>` XML tag
- `Constraints:`, `Restrictions:`, `Do not:` headings
- Lines containing `do not`, `don't`, `must not`, `avoid`, `never`

## Configuration

```yaml
rules:
  specificity_constraints: true

# Promote to WARN:
rules:
  specificity_constraints:
    enabled: true
    level: warn
```

## Why It Matters

Without constraints, models make reasonable-sounding but wrong choices:
- Add explanatory prose when you wanted code only
- Use a library you don't have installed
- Return null instead of an empty list
- Print debug output to stdout

Constraints are the cheapest way to prevent the most common failure modes.
