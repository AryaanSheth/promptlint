# `politeness-bloat` — Politeness Token Removal

**Severity:** WARN · **Auto-fix:** Yes · **Category:** 📝 Verbosity

## What It Does

Detects unnecessary politeness words that consume tokens without improving output. Models respond identically to "Write a function" and "Please kindly write a function" — but the latter costs more.

## Example

**Input:**
```
Please kindly help me write a Python function to calculate fibonacci numbers.
Could you also add error handling? Thank you so much in advance.
```

**Findings:**
```
[ WARN ] politeness-bloat (line 1)
  Unnecessary politeness: 'Please kindly' (saves ~3 tokens)

[ WARN ] politeness-bloat (line 2)
  Unnecessary politeness: 'Could you also' → rephrase as direct instruction

[ WARN ] politeness-bloat (line 2)
  Unnecessary politeness: 'Thank you so much in advance' (saves ~6 tokens)
```

**After `--fix`:**
```
Write a Python function to calculate fibonacci numbers.
Add error handling.
```

## Detected Phrases

| Phrase | Action |
|--------|--------|
| `please` | Removed |
| `kindly` | Removed |
| `could you` | Rewritten to imperative |
| `would you` | Rewritten to imperative |
| `if you don't mind` | Removed |
| `thank you` | Removed |
| `thanks in advance` | Removed |
| `I would appreciate` | Removed |
| `feel free to` | Removed |

## Configuration

```yaml
rules:
  politeness_bloat:
    enabled: true
    allow_politeness: false  # set to true to demote to INFO

fix:
  politeness_bloat: true
```

### Demote to INFO

If you want to keep the check but not fail at WARN level:

```yaml
rules:
  politeness_bloat:
    enabled: true
    allow_politeness: true  # demotes to INFO severity
```

## Cost Impact

At 10,000 calls/day and $0.005/1k tokens, removing 5 politeness tokens per prompt saves:

```
5 tokens × 10,000 calls × $0.005/1000 = $0.25/day = $91.25/year
```

Small per-prompt, significant at scale.
