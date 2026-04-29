# `clarity-vague-terms` — Vague Language Detection

**Severity:** WARN · **Auto-fix:** No · **Category:** ✨ Quality

## What It Does

Detects vague quantifiers and catch-all expressions that leave the model guessing at your intent. These are words that introduce ambiguity about *how many*, *how much*, or *in what way* something should be done.

::: warning Scope caveat
This rule targets **quantifier and manner vagueness**, not general quality descriptors. It detects words like `several`, `various`, `somehow` — not words like `good`, `efficient`, or `proper`. Those require human judgment to define; this rule catches only patterns where a number, enumeration, or concrete description is objectively better.
:::

## Detected Patterns

| Pattern | Category | Why it's flagged |
|---------|----------|-----------------|
| `some`, `several`, `various`, `many`, `few` | Vague quantifier | Specify a number or range instead |
| `stuff`, `things`, `etc`, `and so on`, `and more` | Trailing catch-all | Enumerate the specific items |
| `somehow`, `somewhere`, `sometime` | Unspecified manner/place/time | Be concrete about how, where, or when |
| `maybe` | Uncertain instruction | Instructions should be definitive |

::: tip Note on `maybe`
`maybe` is only flagged when used as an instruction hedge (e.g., "maybe add error handling"). It won't flag "maybe null" or "maybe undefined" — those are legitimate programming terms.
:::

## Examples

::: danger Triggers the rule
```
Process several files and return things in some format.
The function should somehow handle edge cases and so on.
Maybe add logging if possible.
```

Findings:
```
[ WARN ] clarity-vague-terms (line 1)
  Vague quantifier: 'several' — specify a number or range
[ WARN ] clarity-vague-terms (line 1)
  Trailing catch-all: 'things' — enumerate explicitly
[ WARN ] clarity-vague-terms (line 1)
  Vague quantifier: 'some' — specify a number or range
[ WARN ] clarity-vague-terms (line 2)
  Unspecified manner: 'somehow' — be concrete about how
[ WARN ] clarity-vague-terms (line 2)
  Trailing catch-all: 'and so on' — enumerate explicitly
[ WARN ] clarity-vague-terms (line 3)
  Uncertain language: 'maybe' — use a definitive instruction
```
:::

::: tip Clean version
```
Process up to 50 files and return results as a JSON array.
The function must catch ValueError and TypeError — log both with stack traces.
Add structured logging using the stdlib `logging` module.
```
:::

## What This Rule Does NOT Catch

This rule is intentionally narrow. It won't flag:
- Subjective quality words: `good`, `clean`, `efficient`, `proper`, `nice`
- Ambiguous verbs: `handle`, `deal with`, `manage`
- Vague adjectives: `appropriate`, `reasonable`, `relevant`

For these, use [`clarity-vague-terms`](/rules/clarity-vague-terms) together with [`specificity-examples`](/rules/specificity-examples) and [`specificity-constraints`](/rules/specificity-constraints) — together they cover a broader range of underspecification.

## False Positives

**"few-shot"** — the word `few` in "few-shot examples" will trigger the rule. Disable the rule or add an inline comment if your prompt engineering terminology triggers false positives.

**Legitimate "etc."** — if you genuinely want to say "supports formats X, Y, etc." where the remaining formats are well-understood by context, this will still trigger. Consider being explicit anyway — the model will produce better output.

## Configuration

```yaml
rules:
  clarity_vague_terms: true  # or false to disable
```

Severity can be demoted:
```yaml
rules:
  clarity_vague_terms:
    enabled: true
    level: info
```
