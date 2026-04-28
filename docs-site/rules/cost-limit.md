# `cost-limit` — Token Budget Enforcement

**Severity:** CRITICAL · **Auto-fix:** No · **Category:** 💰 Cost

## What It Does

Fires at CRITICAL level when the prompt exceeds the configured `token_limit`. Use this to catch accidentally bloated prompts before they hit API rate limits or blow your context window.

## Example

**Prompt:** 850 tokens, `token_limit: 800`

```
[ CRITICAL ] cost-limit (line -)
  Prompt exceeds token limit: 850/800 tokens.
  Consider removing redundant content or splitting into smaller prompts.
```

## Configuration

```yaml
token_limit: 800  # Default

rules:
  cost_limit: true
```

### Choosing a Limit

Set `token_limit` to 60–70% of your model's context window to leave room for the completion:

| Model | Context window | Recommended `token_limit` |
|-------|:-------------:|:-------------------------:|
| GPT-4o | 128k | 500–2000 (system prompt budget) |
| GPT-4 | 8k | 500–1000 |
| GPT-3.5 Turbo | 16k | 500–1500 |
| Claude 3.5 Sonnet | 200k | 500–5000 |
| Gemini 1.5 Pro | 1M | 500–10000 |

## Disabling

```yaml
rules:
  cost_limit: false
```

Or raise the limit:

```yaml
token_limit: 2000
```
