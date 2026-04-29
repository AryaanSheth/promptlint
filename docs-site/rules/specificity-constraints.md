# `specificity-constraints` — Missing Constraints

**Severity:** INFO · **Auto-fix:** No · **Category:** 🎯 Specificity

## What It Does

Detects prompts that contain a task instruction but no constraint keywords. Without constraints — "do not", "must", "limit", "exactly" — the model makes its own choices about scope, format, and edge case handling.

## Trigger Conditions

::: warning Three conditions must all be true
1. The prompt is **longer than 80 characters**
2. The prompt contains a **task verb**: `write`, `create`, `generate`, `list`, `explain`
3. The prompt does **not** contain a **constraint keyword**: `must`, `should`, `limit`, `maximum`, `minimum`, `between`, `exactly`, `only`
:::

This is keyword-based heuristic detection. The rule doesn't understand whether your constraints are semantically sufficient — it just checks if constraint vocabulary is present.

## Examples

::: danger Triggers the rule
```
Write a Python function that parses configuration files and returns
a dictionary of the settings with their values.
```
Has `write` (task verb), > 80 chars, no constraint keywords.

```
[ INFO ] specificity-constraints (line -)
  Consider adding constraints (length, format, scope) for clearer results.
```
:::

::: tip Passes the rule
```
Write a Python function that parses configuration files and returns
a dictionary of the settings.
Constraints:
- Must use only the standard library (no third-party packages)
- Should handle missing files gracefully (return empty dict, not raise)
- Maximum 30 lines of code
- Only support INI and JSON formats
```
Has `must`, `should`, `maximum`, `only` → no finding.
:::

## False Positives

**Prompts with implicit constraints via examples** — "Write a function. Example: `validate("a@b.c") → True`" has implicit format constraints from the example, but the rule still fires because no constraint keyword is present. This is intentional — explicit constraints are clearer.

**`should` in non-constraint context** — "Write a greeting that should feel warm" contains `should`, so the rule is suppressed even though there aren't meaningful constraints. The heuristic isn't semantically aware.

**Short prompts** — "Write a haiku about autumn" is < 80 chars and won't fire even though it has no constraints. The rule targets longer, more complex prompts where unconstrained generation is riskier.

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

Disable:
```yaml
rules:
  specificity_constraints: false
```

## What Makes a Good Constraint

Effective constraints are **negative and boundary-defining**, not just positive instructions:

| Type | Example |
|------|---------|
| Scope limit | "Only extract from the provided text — do not use outside knowledge" |
| Format boundary | "Return JSON only — no prose before or after" |
| Length constraint | "Maximum 3 bullet points" |
| Library constraint | "Use only the standard library" |
| Error behavior | "Return null on failure — do not raise exceptions" |
| Exclusion | "Do not include PII in the output" |

A useful mental model: **what would you be annoyed to see the model do?** Each of those is a constraint.

```
<constraints>
- Do not add docstrings or inline comments
- Do not use f-strings — use .format() for compatibility
- Do not print to stdout
- Return None (not False, not "") when the input is empty
- Maximum 25 lines
</constraints>
```
