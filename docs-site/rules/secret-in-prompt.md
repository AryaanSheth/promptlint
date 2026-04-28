# `secret-in-prompt` — Hardcoded Secret Detection

**Severity:** CRITICAL · **Auto-fix:** No · **Category:** 🔒 Security

## What It Does

Detects API keys, passwords, connection strings, tokens, and other credentials hardcoded in the prompt text. Even prompts that are never logged can leak secrets through model outputs, context windows, or accidental exposure.

## Example

**Prompt:**
```
Connect to the database at postgres://admin:hunter2@db.prod.example.com/users
and retrieve all records where status = 'active'.
```

**Finding:**
```
[ CRITICAL ] secret-in-prompt (line 1)
  Potential secret detected: database connection string with embedded credentials
```

## Detected Patterns

| Category | Examples |
|----------|---------|
| API keys | `sk-...`, `Bearer eyJ...`, `AIza...`, `AKIA...` (AWS) |
| Connection strings | `postgres://user:pass@host`, `mongodb+srv://...`, `redis://:pass@...` |
| Passwords in URLs | `https://user:password@...` |
| Common key patterns | `api_key=...`, `password=...`, `secret=...`, `token=...` |
| Private keys | PEM-encoded blocks (`-----BEGIN PRIVATE KEY-----`) |

## How to Fix

Replace secrets with template placeholders:

::: danger Bad
```
Use API key sk-abc123xyz to call the OpenAI API.
Database: postgres://admin:s3cr3t@db.prod.example.com/users
```
:::

::: tip Good
```
Use the API key from {{OPENAI_API_KEY}} to call the OpenAI API.
Database: {{DATABASE_URL}}
```
:::

In code, inject at runtime:

```python
import os

prompt = template.replace("{{OPENAI_API_KEY}}", os.environ["OPENAI_API_KEY"])
prompt = prompt.replace("{{DATABASE_URL}}", os.environ["DATABASE_URL"])
```

## Configuration

```yaml
rules:
  secret_in_prompt: true  # or false to disable
```

## Why It Matters

Secrets in prompts can be leaked:
- In model completions if the model echoes the prompt
- In logs when prompt text is logged for debugging
- In error messages
- Through context window dumps via injection attacks

Never put secrets in prompts. Use environment variables and inject them at runtime.
