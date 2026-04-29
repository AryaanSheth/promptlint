# FAQ

## Does PromptLint send my prompts anywhere?

**No.** All analysis is local. PromptLint never makes network requests during linting. Your prompt text stays on your machine.

The one exception: if you use the tiktoken-based token counter (`pip install "promptlint-cli[tiktoken]"`), tiktoken downloads its vocabulary files on first use — but that's a one-time download of model vocabulary data, not your prompt text.

---

## Python vs. Node.js — which should I use?

| Feature | Python CLI | Node.js CLI |
|---------|:----------:|:-----------:|
| Token counting | Exact (tiktoken) | Heuristic (chars ÷ 4, ±15%) |
| Auto-fix | ✅ | ✅ |
| SARIF output | ✅ | ✅ |
| Rule coverage | 20 rules | 20 rules |
| Speed | ~100ms startup | ~80ms startup |

Use Python if you care about exact token counts and cost projections. Use Node.js if you're in a JavaScript/TypeScript environment. For CI/CD, both work equally well — use the GitHub Action which wraps the Node.js CLI.

---

## Are patterns matched as regex or plain substrings?

**Regex.** All patterns — injection patterns, jailbreak patterns, and custom patterns you add in `.promptlintrc` — are compiled as case-insensitive regular expressions.

Simple phrases like `ignore previous instructions` work as substring regex (no anchors = match anywhere in the string). You can use full regex syntax:

```yaml
rules:
  prompt_injection:
    patterns:
      - "ignore previous instructions"           # substring match
      - "admin (override|bypass):"               # alternation
      - "(?:you are|act as) (?:an? )?[A-Z]\\w+" # group + character class
```

::: warning Invalid patterns are skipped, not errors
If a pattern fails to compile, PromptLint logs a warning and continues — it does not crash. Test custom patterns with `promptlint --explain prompt-injection` or by linting a test file.
:::

---

## Which models does PromptLint support?

PromptLint is **model-agnostic** — it analyzes the prompt text regardless of which model you use. The `model` config setting only affects token counting (via tiktoken) and cost projection.

Supported by tiktoken (for exact counts): `gpt-4o`, `gpt-4`, `gpt-3.5-turbo`, and other OpenAI models. For non-OpenAI models (Claude, Gemini, Llama), tiktoken falls back to `cl100k_base` encoding which is close but not exact for those tokenizers.

---

## How do I suppress a false positive?

**Option 1** — Disable the rule entirely:
```yaml
rules:
  actionability_weak_verbs: false
```

**Option 2** — Demote to a level below your `--fail-level`:
```yaml
rules:
  specificity_examples:
    enabled: true
    level: info   # won't fail a --fail-level warn pipeline
```

**Option 3** — Narrow the rule scope. For example, reduce injection patterns to only the most critical ones:
```yaml
rules:
  prompt_injection:
    patterns:
      - ignore previous instructions
      - admin override:
      # (omitting broader patterns that cause false positives)
```

---

## Does PromptLint handle template variables like `{{VAR}}`?

Yes — template variables are preserved in all fixes and most rules. The [`context-injection-boundary`](/rules/context-injection-boundary) rule specifically looks for template variables and fires when it finds one without a trust boundary marker nearby.

Other rules treat `{{VAR}}` as a literal string. For example, `pii-in-prompt` won't flag `{{USER_EMAIL}}` — only actual email addresses like `user@example.com`.

---

## Can I run PromptLint on multiple files at once?

Yes. Three approaches:

```bash
# Glob pattern (quotes required on most shells)
promptlint --file "prompts/**/*.txt"

# Shell loop (more control per file)
for f in prompts/*.txt; do
  promptlint --file "$f" --format json
done | jq -s '.'  # merge JSON results

# GitHub Actions (scans a directory)
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
```

When using a glob, the exit code reflects the worst finding across all files.

---

## What does the score mean?

The score (0–100) is computed across four weighted categories:

| Category | Weight | Penalty per CRITICAL | per WARN | per INFO |
|----------|:------:|:-------------------:|:--------:|:--------:|
| Security | 40% | −30 | −10 | −3 |
| Cost | 20% | −30 | −10 | −3 |
| Quality | 25% | −30 | −8 | −3 |
| Completeness | 15% | −30 | −10 | −3 |

Each category is scored 0–100, then combined by weight. Scores are clamped to 0.

Grades: **A** (90+), **B** (75+), **C** (60+), **D** (45+), **F** (below 45)

---

## Why does the `specificity-examples` rule fire on my prompt even though I have examples?

The rule checks for the **word** `example` (or `e.g.`, `such as`, `like`, `for instance`) anywhere in the prompt. If your examples don't use any of those keywords, the rule still fires.

Fix: add a label before your examples:
```
Examples:
  Input: ...
  Output: ...
```

Or add the `<examples>` tag. The word "example" anywhere in the text suppresses the rule.

---

## Can I use PromptLint with non-English prompts?

Partially. Security rules (injection detection, PII, secrets) work on any language because they use regex patterns, not NLP. Quality rules (vague terms, politeness, redundancy) are English-optimized and will have high false-positive rates on other languages — disable those rules for non-English prompts.

---

## Can I use PromptLint in Docker?

Yes. See the [Docker integration guide](/integrations/docker) for a minimal Dockerfile and docker-compose setup.

---

## Where do I report bugs or request features?

[Open an issue on GitHub](https://github.com/AryaanSheth/promptlint/issues). Include the prompt text (sanitized if needed), your `.promptlintrc`, the PromptLint version (`promptlint --version`), and the unexpected output.
