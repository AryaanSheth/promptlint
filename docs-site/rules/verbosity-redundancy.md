# `verbosity-redundancy` — Redundant Phrase Removal

**Severity:** INFO · **Auto-fix:** Yes · **Category:** 📝 Verbosity

## What It Does

Detects multi-word phrases that can be replaced with a shorter equivalent without changing meaning. These accumulate across prompts and waste tokens.

## Detected Phrases (40+)

All matches are case-insensitive:

### Prepositions & Connectives
| Verbose | Concise | Tokens saved |
|---------|---------|:---:|
| `in order to` | `to` | 2 |
| `due to the fact that` | `because` | 4 |
| `for the purpose of` | `for` | 3 |
| `in the event that` | `if` | 3 |
| `with regard to` | `about` / `for` | 2 |
| `in relation to` | `about` | 2 |
| `for the reason that` | `because` | 3 |
| `with the exception of` | `except` | 3 |
| `in spite of the fact that` | `although` | 5 |
| `in close proximity to` | `near` | 3 |
| `prior to` | `before` | 1 |
| `subsequent to` | `after` | 1 |
| `until such time as` | `until` | 3 |

### Time Expressions
| Verbose | Concise |
|---------|---------|
| `at this point in time` | `now` |
| `in the near future` | `soon` |
| `at the present time` | `now` |
| `on a daily basis` | `daily` |
| `on a weekly basis` | `weekly` |
| `on a monthly basis` | `monthly` |

### Redundant Pairs (things that say the same thing twice)
| Redundant phrase | Why |
|-----------------|-----|
| `past history` | History is always past |
| `future plans` | Plans are always future |
| `end result` | Results are ends |
| `basic fundamentals` | Fundamentals are basic |
| `close proximity` | Proximity implies closeness |
| `new innovation` | Innovations are new |
| `personal opinion` | Opinions are personal |
| `true fact` | Facts are true |
| `repeat again` | Repeat = do again |
| `still remains` | Remains = still is |
| `advance planning` | Planning is in advance |
| `past experience` | Experience is from the past |
| `unexpected surprise` | Surprises are unexpected |
| `completely eliminate` | Eliminate = completely remove |
| `completely finished` | Finished = completely done |

### Wordy Verb Phrases
| Verbose | Concise |
|---------|---------|
| `has the ability to` | `can` |
| `is able to` | `can` |
| `gather together` | `gather` |
| `join together` | `join` |
| `refer back` | `refer` |
| `return back` | `return` |
| `a total of` | *(just the number)* |
| `each and every` | `every` |
| `first and foremost` | `first` |

## Example

**Input:**
```
In order to gather together the results, the function has the ability to
process each and every record. Due to the fact that this runs on a daily basis,
we need to completely eliminate past history from the cache prior to running.
```

**Findings:**
```
[ INFO ] verbosity-redundancy (line 1)  'in order to' → 'to'
[ INFO ] verbosity-redundancy (line 1)  'gather together' → 'gather'
[ INFO ] verbosity-redundancy (line 1)  'has the ability to' → 'can'
[ INFO ] verbosity-redundancy (line 2)  'each and every' → 'every'
[ INFO ] verbosity-redundancy (line 2)  'due to the fact that' → 'because'
[ INFO ] verbosity-redundancy (line 2)  'on a daily basis' → 'daily'
[ INFO ] verbosity-redundancy (line 3)  'completely eliminate' (redundant intensifier)
[ INFO ] verbosity-redundancy (line 3)  'past history' (tautology)
[ INFO ] verbosity-redundancy (line 3)  'prior to' → 'before'
```

**After `--fix`:**
```
To gather the results, the function can process every record. Because this
runs daily, we need to eliminate history from the cache before running.
```

## False Positives

**`prior to` in formal/legal prompts** — some regulated industries use `prior to` as a required legal term. Disable verbosity-redundancy or use `prior to` as a recognized domain term.

**`personal opinion` in survey prompts** — "What is your personal opinion?" is a legitimate phrasing in survey design where `personal` distinguishes it from professional recommendation. The rule will still flag it.

**`is able to` in accessibility contexts** — "The screen reader is able to interpret this" is technically correct but uses a pattern the rule flags. Rephrase to "The screen reader can interpret this."

## Configuration

```yaml
rules:
  verbosity_redundancy: true

fix:
  verbosity_redundancy: true   # auto-replace on --fix
```

Disable:
```yaml
rules:
  verbosity_redundancy: false
```

::: tip Only one occurrence per pattern is reported per run
If `prior to` appears 5 times in a prompt, only the first occurrence is flagged. `--fix` replaces all occurrences.
:::
