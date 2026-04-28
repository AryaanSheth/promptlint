# `actionability-weak-verbs` — Weak Verb Detection

**Severity:** INFO · **Auto-fix:** No · **Category:** 💪 Actionability

## What It Does

Detects passive voice and weak verb constructions that reduce the clarity of instructions. Active, imperative verbs produce more consistent model behavior than passive constructions.

## Example

::: danger Passive / weak
```
A function should be written that can be used to parse JSON.
The result needs to be returned as a dictionary.
Error handling should be included.
```

Findings:
```
[ INFO ] actionability-weak-verbs (line 1)
  Weak construction: 'should be written' — use imperative: "Write a function..."

[ INFO ] actionability-weak-verbs (line 2)
  Weak construction: 'needs to be returned' — use imperative: "Return..."

[ INFO ] actionability-weak-verbs (line 3)
  Weak construction: 'should be included' — use imperative: "Include..."
```
:::

::: tip Active / imperative
```
Write a function to parse JSON.
Return the result as a dictionary.
Include error handling.
```
:::

## Detected Patterns

| Weak | Strong |
|------|--------|
| `should be written` | `write` |
| `needs to be done` | `do` |
| `can be used to` | `use to` / verb directly |
| `is required to` | `must` |
| `it would be good to` | [just say it] |
| `feel free to` | [just say it or remove] |

## Configuration

```yaml
rules:
  actionability_weak_verbs: true
```

## Why It Matters

Passive constructions are ambiguous about agency. "A function should be written" — by whom? The model tends to produce more consistent output when instructions are direct imperatives: "Write a function."
