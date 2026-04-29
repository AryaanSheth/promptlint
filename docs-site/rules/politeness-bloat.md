# `politeness-bloat` — Politeness Token Removal

**Severity:** WARN (default) · **Auto-fix:** Yes · **Category:** 📝 Verbosity

## What It Does

Detects unnecessary politeness words that consume tokens without affecting model output quality. LLMs respond identically to "Write a function" and "Please kindly write a function" — the polite version just costs more.

## Default Detected Words

The following words/phrases are flagged by default:

| Word / phrase | Tokens wasted |
|--------------|:-------------:|
| `please` | ~1 |
| `kindly` | ~1 |
| `i would appreciate` | ~3 |
| `thank you` | ~2 |
| `be so kind as to` | ~5 |
| `if possible` | ~2 |

You can customize the list — see [Configuration](#configuration).

## Severity: `allow_politeness`

::: warning The `allow_politeness` flag is not intuitive
- `allow_politeness: false` (default) → findings fire at **WARN** level
- `allow_politeness: true` → findings fire at **INFO** level (demoted)

Setting `allow_politeness: true` does **not** disable the rule — it just reduces severity so it won't fail a `--fail-level warn` pipeline. To disable entirely, set the rule to `false`.
:::

## Example

**Input:**
```
Please kindly help me write a Python function.
I would appreciate it if you could add error handling.
Thank you.
```

**With `allow_politeness: false` (default):**
```
[ WARN ] politeness-bloat (line 1)
  'please' adds ~1.5 tokens without semantic value. Remove it.

[ WARN ] politeness-bloat (line 1)
  'kindly' adds ~1.5 tokens without semantic value. Remove it.

[ WARN ] politeness-bloat (line 2)
  'i would appreciate' adds ~1.5 tokens without semantic value. Remove it.

[ WARN ] politeness-bloat (line 3)
  'thank you' adds ~1.5 tokens without semantic value. Remove it.
```

**With `allow_politeness: true`:**
```
[ INFO ] politeness-bloat (line 1)
  'please' adds ~1.5 tokens. Consider removing (~1.5 tokens).
  [This is allowed per configuration — removing improves token efficiency.]
```

**After `--fix`:**
```
Write a Python function.
Add error handling.
```

## Cost Impact

At 10,000 calls/day and $0.005/1k tokens, removing 3 politeness tokens per prompt saves:

```
3 tokens × $0.005/1000 × 10,000 calls/day × 30 days = $4.50/month
```

Small per-prompt, and it compounds across all your prompts.

## False Positives

**"Please" in quoted strings or examples** — the rule matches case-insensitively as a whole word, so `please` inside a quoted string like `"Please enter your name:"` will still trigger. If your prompt is *about* a UI element that uses "please", disable the rule or adjust your prompt to use a placeholder.

**"If possible" as a genuine constraint** — if you mean "do X if it's feasible given the constraints", consider replacing with a clearer conditional rather than suppressing the rule.

## Configuration

```yaml
rules:
  politeness_bloat:
    enabled: true
    allow_politeness: false    # false = WARN (default), true = INFO
    words:                     # override the full list
      - please
      - kindly
      - i would appreciate
      - thank you
      - be so kind as to
      - if possible
      - could you please
      - would you mind
    savings_per_hit: 1.5       # tokens saved per occurrence (used in output messages)

fix:
  politeness_bloat: true       # auto-remove on --fix
```

### Add custom words

To add words to the default list, you must specify the full list:

```yaml
rules:
  politeness_bloat:
    words:
      - please
      - kindly
      - i would appreciate
      - thank you
      - be so kind as to
      - if possible
      - with your assistance    # custom addition
      - at your earliest convenience  # custom addition
```

### Disable

```yaml
rules:
  politeness_bloat: false
```
