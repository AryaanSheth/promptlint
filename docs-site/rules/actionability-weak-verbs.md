# `actionability-weak-verbs` — Weak Directive Detection

**Severity:** INFO · **Auto-fix:** No · **Category:** 💪 Actionability

## What It Does

Detects two categories of weak language in instructions:
1. **Hedged directive phrases** — words that soften a command when a direct imperative is clearer
2. **Excessive passive voice** — fires when 6+ passive constructions appear in the same prompt

## Detected Weak Directive Phrases

| Pattern | Issue | Better alternative |
|---------|-------|--------------------|
| `consider`, `try to`, `attempt to`, `endeavor to` | Weak directive — sounds optional | Use the imperative form directly |
| `you might want to` | Hedged instruction | State the requirement directly |
| `feel free to` | Unnecessary hedge | Remove it entirely |
| `it would be good/nice/helpful/great if/to` | Indirect instruction | State what you want |
| `if possible` | Conditional hedge | Commit to the instruction |
| `whenever possible`, `whenever you can` | Weak conditional | Use `always` or state the actual condition |

## Passive Voice Detection

Passive voice is flagged only when **more than 5 passive constructions** appear in a single prompt. A single "is returned" or "was processed" won't trigger a finding — the rule targets prompts that are *predominantly* passive.

::: tip Why the 5+ threshold?
A few passive constructions are fine and sometimes clearer ("The result is returned as JSON"). The rule catches prompts that have systematically avoided active voice throughout, not individual instances.
:::

## Examples

::: danger Weak directives
```
Consider adding error handling if possible.
You might want to include examples when you can.
Feel free to add comments to explain the code.
It would be nice if you could return JSON.
Try to keep the function under 30 lines.
```

Findings:
```
[ INFO ] actionability-weak-verbs (line 1)  'consider' — weak directive, use imperative
[ INFO ] actionability-weak-verbs (line 1)  'if possible' — commit to the instruction
[ INFO ] actionability-weak-verbs (line 2)  'you might want to' — state directly
[ INFO ] actionability-weak-verbs (line 2)  'whenever you can' — use 'always' or state the condition
[ INFO ] actionability-weak-verbs (line 3)  'feel free to' — unnecessary hedge, remove
[ INFO ] actionability-weak-verbs (line 4)  'it would be nice if' — indirect instruction
[ INFO ] actionability-weak-verbs (line 5)  'try to' — weak directive, use imperative
```
:::

::: tip Direct imperatives
```
Add error handling.
Include 2 input/output examples.
Add inline comments explaining non-obvious logic.
Return a JSON object.
Keep the function under 30 lines.
```
:::

::: danger Excessive passive voice (6+ constructions)
```
Data is read from the file. Errors are caught by the handler. Results are stored
in the cache. Each record is processed by the validator. The output is returned
to the caller. Performance is measured by the benchmark suite.
```

Finding (single finding for the whole prompt):
```
[ INFO ] actionability-weak-verbs (line -)
  Multiple passive voice constructions (6) detected. Use active voice for clarity.
```
:::

::: tip Active voice
```
Read data from the file. Catch errors in the handler. Store results in the cache.
Validate each record. Return the output to the caller. Benchmark performance.
```
:::

## False Positives

**"Consider" for genuine options** — "Consider one of these three approaches: A, B, or C" is a legitimate use of `consider` (presenting options, not a weak command). The rule doesn't distinguish intent.

**`if possible` as a real conditional** — "Cache the result if possible (only if disk space > 100MB)" is a real conditional, not a hedge. Rephrase to make the condition explicit: "Cache the result when disk space exceeds 100MB."

**Technical passive voice** — "The value is clamped to [0, 1]" is standard technical writing that's clearer than the active form. A few of these won't trigger the rule (threshold is 6+).

## Configuration

```yaml
rules:
  actionability_weak_verbs: true   # or false to disable
```

Disable (useful for creative writing or soft-instruction prompts):
```yaml
rules:
  actionability_weak_verbs: false
```
