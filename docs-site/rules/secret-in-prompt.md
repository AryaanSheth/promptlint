# `secret-in-prompt` — Hardcoded Secret Detection

**Severity:** CRITICAL · **Auto-fix:** No · **Category:** 🔒 Security

## What It Does

Detects credentials, tokens, and keys hardcoded directly in the prompt text. Secrets in prompts are a critical vulnerability: they appear in model completions if the model echoes the prompt, in logs, in error messages, and can be exfiltrated by injection attacks.

## Detected Secret Patterns

| Pattern | Label | Example |
|---------|-------|---------|
| `sk-[A-Za-z0-9]{20,}` | OpenAI API key | `sk-abcdef1234567890abcdef` |
| `sk-proj-[A-Za-z0-9]{20,}` | OpenAI project key | `sk-proj-abcdef1234...` |
| `sk-ant-[A-Za-z0-9]{20,}` | Anthropic API key | `sk-ant-api03-...` |
| `AIza[0-9A-Za-z_-]{35}` | Google API key | `AIzaSyBxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `ghp_[A-Za-z0-9]{36}` | GitHub PAT | `ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `gho_[A-Za-z0-9]{36}` | GitHub OAuth token | `gho_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx` |
| `Bearer <token>` | Bearer auth token | `Bearer eyJhbGciOiJSUzI1NiJ9...` |
| `api_key = "..."` | Generic API key assignment | `api_key="c1234567890abcdef"` |
| `password = "..."` | Hardcoded password | `password="hunter2"` |
| `[A-Fa-f0-9]{32}` | MD5 hash / potential token | `5d41402abc4b2a76b9719d911017c592` |
| `[A-Fa-f0-9]{40}` | SHA1 / potential token | `aaf4c61ddcc5e8a2dabede0f3b482cd9aea9434d` |
| `[A-Fa-f0-9]{64}` | SHA256 / potential token | `2c624232cdd221771294dfbb310acbc...` |

::: warning Hash pattern false positives
The 32/40/64-character hex patterns catch MD5, SHA1, and SHA256 hashes which are used extensively in legitimate technical contexts — git commit SHAs, file checksums, content hashes. These *also* match common token formats, so PromptLint errs on the side of flagging them.

If your prompts contain legitimate checksums or commit SHAs, you can disable the rule for those cases or add an inline ignore comment. This is a known trade-off: the false-positive rate is higher than for the named-key patterns, but the security risk of missing a real token is severe.
:::

::: warning What's NOT detected
- Database connection strings (no DSN pattern yet) — use [`pii-in-prompt`](/rules/pii-in-prompt) for IP addresses
- Private key file contents (`-----BEGIN PRIVATE KEY-----`) — coming in a future release
- `.env` file contents pasted verbatim — partially covered by the `password=` and `api_key=` patterns
:::

## Example

**Prompt:**
```
Connect to OpenAI using key sk-abc123xyz456def789ghi012jkl345mno678pqr.
Use GitHub token ghp_abcdefghijklmnopqrstuvwxyz012345678901 for repo access.
The admin password is: password="sup3r_s3cret!"
```

**Findings:**
```
[ CRITICAL ] secret-in-prompt (line 1)
  OpenAI API key detected

[ CRITICAL ] secret-in-prompt (line 2)
  GitHub personal access token detected

[ CRITICAL ] secret-in-prompt (line 3)
  Hardcoded password detected
```

Note: matched values are **not shown in output** to prevent double-logging secrets.

## How to Fix

Replace every secret with an environment variable reference or template placeholder:

::: danger Never do this
```
Use API key sk-abc123xyz to call OpenAI.
Database password: hunter2
GitHub token: ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```
:::

::: tip Do this instead
```
Use the API key from the OPENAI_API_KEY environment variable.
Database password: {{DB_PASSWORD}}
GitHub token: {{GITHUB_TOKEN}}
```
:::

**Python — inject at runtime:**
```python
import os

prompt = template.replace("{{DB_PASSWORD}}", os.environ["DB_PASSWORD"])
```

**Never store secrets in:**
- Prompt files committed to version control
- Hard-coded strings in application code
- `.env` files that end up in the prompt text

Use a secrets manager (AWS Secrets Manager, HashiCorp Vault, 1Password Secrets Automation) and inject at runtime.

## Configuration

```yaml
rules:
  secret_in_prompt: true  # or false to disable
```

No sub-options — either enabled or disabled.

## Why It Matters

Even if your prompt is never deliberately logged:
1. **Model completions** — if the model echoes the prompt back (e.g., "Sure! You asked me to connect using sk-..."), the secret is in the completion
2. **Injection attacks** — `prompt-injection` attacks can instruct the model to repeat the system prompt, including embedded secrets
3. **API response logging** — many teams log completions for debugging; the secret ends up in the log
4. **Context window dumps** — some orchestration frameworks log the full context on error
