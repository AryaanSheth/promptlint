# `verbosity-redundancy` — Redundant Phrase Removal

**Severity:** INFO · **Auto-fix:** Yes · **Category:** 📝 Verbosity

## What It Does

Detects and removes multi-word phrases that can be replaced with shorter equivalents without changing meaning.

## Example

**Input:**
```
Write a function in order to parse JSON data and also return the result
as well as handle errors due to the fact that the input may be invalid.
```

**Findings:**
```
[ INFO ] verbosity-redundancy (line 1)
  Redundant phrase: 'in order to' → 'to' (saves 2 tokens)

[ INFO ] verbosity-redundancy (line 1)
  Redundant phrase: 'and also' → 'and' (saves 1 token)

[ INFO ] verbosity-redundancy (line 2)
  Redundant phrase: 'as well as' → 'and' (saves 2 tokens)

[ INFO ] verbosity-redundancy (line 2)
  Redundant phrase: 'due to the fact that' → 'because' (saves 4 tokens)
```

**After `--fix`:**
```
Write a function to parse JSON data and return the result
and handle errors because the input may be invalid.
```

## Phrase Map

| Verbose | Concise | Tokens saved |
|---------|---------|:------------:|
| `in order to` | `to` | 2 |
| `as well as` | `and` | 2 |
| `and also` | `and` | 1 |
| `due to the fact that` | `because` | 4 |
| `at this point in time` | `now` | 4 |
| `in the event that` | `if` | 3 |
| `for the purpose of` | `for` | 3 |
| `with regard to` | `about` | 2 |
| `in spite of the fact that` | `although` | 5 |
| `on a daily basis` | `daily` | 2 |

## Configuration

```yaml
rules:
  verbosity_redundancy: true

fix:
  verbosity_redundancy: true
```
