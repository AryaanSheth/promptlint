# `consistency-terminology` — Terminology Consistency

**Severity:** INFO · **Auto-fix:** No · **Category:** 🔄 Consistency

## What It Does

Detects when the same concept is referred to by multiple different names within the same prompt. Inconsistent terminology confuses the model about whether these refer to the same thing or different things.

## Example

::: danger Inconsistent
```
Extract user records from the database.
Each customer should have a name and email.
Return the person's data as JSON.
Users must have a valid account to appear in results.
```

Finding:
```
[ INFO ] consistency-terminology (line -)
  Inconsistent terminology: 'user', 'customer', 'person' may refer to the same entity.
  Pick one term and use it consistently.
```
:::

::: tip Consistent
```
Extract user records from the database.
Each user should have a name and email.
Return the user's data as JSON.
Users must have a valid account to appear in results.
```
:::

## Common Inconsistency Patterns

| Concept | Inconsistent variants |
|---------|----------------------|
| End user | "user", "customer", "client", "person", "member" |
| API call | "request", "call", "invocation", "query" |
| Response | "response", "result", "output", "return value" |
| Error | "error", "exception", "failure", "issue", "problem" |
| Config | "config", "configuration", "settings", "options", "params" |

## Configuration

```yaml
rules:
  consistency_terminology: true
```

## No Auto-Fix

Merging terminology requires knowing which term is canonical — PromptLint reports the ambiguity but you choose the term.
