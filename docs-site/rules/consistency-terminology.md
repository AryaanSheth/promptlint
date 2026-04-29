# `consistency-terminology` — Terminology Consistency

**Severity:** INFO · **Auto-fix:** No · **Category:** 🔄 Consistency

## What It Does

Detects when the same concept is referred to by two different names within the same prompt. When both terms from a known synonym pair appear together, the model may treat them as distinct entities — causing duplicated logic or ignored instructions.

One finding is emitted per conflicting pair found.

## Built-in Term Pairs

The rule checks 12 built-in synonym pairs. A finding fires when **both** terms from a pair appear anywhere in the prompt:

| Term A | Term B |
|--------|--------|
| `user` | `customer` |
| `function` | `method` |
| `error` | `exception` |
| `AI` | `model` |
| `LLM` | `model` |
| `query` | `request` |
| `response` | `reply` |
| `output` | `result` |
| `prompt` | `message` |
| `system prompt` | `instruction` |
| `task` | `goal` |
| `agent` | `assistant` |

::: warning Pair-based, not cluster-based
The rule only compares terms within the same predefined pair. It will not flag "user" vs "client" or "person" vs "customer" — those aren't built-in pairs. Use `custom_term_pairs` to add your own.
:::

## Examples

::: danger Mixed terminology
```
Extract all user records from the database.
Each customer entry must include a name, email, and account status.
Return the user list as JSON.
```

Findings:
```
[ INFO ] consistency-terminology (line -)
  Mixed terminology: 'user' and 'customer'. Use one term consistently.
```
:::

::: tip Consistent terminology
```
Extract all user records from the database.
Each user entry must include a name, email, and account status.
Return the user list as JSON.
```
:::

::: danger Multiple conflicting pairs
```
Call the LLM to generate a response.
The model will return a reply in under 200 tokens.
```

Findings:
```
[ INFO ] consistency-terminology (line -)
  Mixed terminology: 'LLM' and 'model'. Use one term consistently.
[ INFO ] consistency-terminology (line -)
  Mixed terminology: 'response' and 'reply'. Use one term consistently.
```
:::

## Custom Term Groups

Add project-specific synonym groups in `.promptlintrc`. Each group is a list of terms that should not be mixed — every pair within the group is checked:

```yaml
rules:
  consistency_terminology:
    enabled: true
    custom_term_pairs:
      - ["config", "configuration", "settings"]    # flags config+settings, config+configuration, etc.
      - ["endpoint", "route", "path"]
      - ["payload", "body", "data"]
```

## False Positives

**Intentional distinction** — "An AI model differs from a traditional rule-based model in…" uses both `AI` and `model` but refers to different things. The rule can't distinguish intent. Disable it or use `custom_term_pairs` with terms that are genuinely equivalent in your domain.

**Technical writing conventions** — API documentation often uses `request` and `query` with distinct meanings (HTTP request vs. database query). In that context, the pair `query`/`request` may flag legitimately different concepts.

## Configuration

Enable/disable:
```yaml
rules:
  consistency_terminology: true   # default: true
```

Disable:
```yaml
rules:
  consistency_terminology: false
```

## No Auto-Fix

Resolving a terminology conflict requires knowing which term is canonical — PromptLint reports the ambiguity but leaves the choice to you.
