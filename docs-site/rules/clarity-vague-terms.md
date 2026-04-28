# `clarity-vague-terms` — Vague Language Detection

**Severity:** WARN · **Auto-fix:** No · **Category:** ✨ Quality

## What It Does

Detects vague, ambiguous terms that reduce output quality. Words like "good", "efficient", "things", "various", and "proper" force the model to guess your intent.

## Example

::: danger Vague
```
Write a good function that efficiently handles various edge cases properly.
```

Findings:
```
[ WARN ] clarity-vague-terms (line 1)
  Vague term: 'good' — specify what "good" means (e.g., "readable", "tested", "O(n log n)")

[ WARN ] clarity-vague-terms (line 1)
  Vague term: 'efficiently' — specify performance requirements

[ WARN ] clarity-vague-terms (line 1)
  Vague term: 'various' — enumerate the specific cases

[ WARN ] clarity-vague-terms (line 1)
  Vague term: 'properly' — define what proper handling looks like
```
:::

::: tip Specific
```
Write a function that:
- Is O(n log n) time complexity
- Handles empty input, None, and lists > 10,000 elements
- Returns an empty list (not None) on empty input
- Raises ValueError (not crashes) on invalid types
```
:::

## Detected Vague Terms

| Term | Better alternatives |
|------|-------------------|
| `good` | "readable", "tested", "O(n)", "under 30 lines" |
| `efficient` | "O(n log n)", "< 100ms", "memory-efficient" |
| `things` | Name the actual things |
| `various` | "the following: A, B, C" |
| `proper` | Define what proper means |
| `appropriate` | Be specific |
| `nice` | Define the quality |
| `handle` | "return X", "raise Y", "log Z" |
| `deal with` | Specify the handling |
| `etc.` | Enumerate completely |

## Configuration

```yaml
rules:
  clarity_vague_terms: true  # or false to disable
```

## No Auto-Fix

Replacing vague terms requires understanding your intent — PromptLint reports them but you fix them. Use the findings as a review checklist.
