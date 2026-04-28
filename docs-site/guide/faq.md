# FAQ

## Does PromptLint send my prompts anywhere?

**No.** All analysis is local. PromptLint never makes network requests during linting. Your prompt text stays on your machine.

## Which models does PromptLint support?

PromptLint is model-agnostic — it analyzes prompt text regardless of which model you use. The `model` config setting only affects token counting (via tiktoken) and cost projection. You can use GPT-4o, Claude, Gemini, Llama, or any other model.

## Python vs Node.js — which should I use?

| Feature | Python CLI | Node.js CLI |
|---------|-----------|-------------|
| Token counting | Exact (tiktoken) | Heuristic (±15%) |
| Auto-fix | ✅ | ✅ |
| SARIF output | ✅ | ✅ |
| Rule coverage | 20 rules | 20 rules |

Use Python if you care about exact token counts and cost projections. Use Node.js if you're in a JavaScript/TypeScript environment and don't need exact counts.

## How do I suppress a false positive?

There are two ways:

1. **Disable the rule entirely** in `.promptlintrc`:
   ```yaml
   rules:
     actionability_weak_verbs: false
   ```

2. **Adjust the severity** to a level below your `--fail-level`:
   ```yaml
   rules:
     specificity_examples:
       enabled: true
       level: info  # won't fail a warn-level check
   ```

## Can I use PromptLint with non-English prompts?

PromptLint's security rules (injection detection, PII, secrets) work on any language. Quality rules (vague terms, politeness bloat, redundancy) are English-optimized and may produce false positives on other languages. You can disable specific rules for non-English projects.

## Does PromptLint work with prompt templates (with `{{variables}}`)?

Yes. PromptLint lints the template text, not the rendered output. It correctly ignores `{{variable}}` placeholders in most rules. The `pii-in-prompt` rule won't fire on `{{USER_EMAIL}}` — only on literal email addresses.

## How do I run PromptLint on multiple files?

::: code-group

```bash [Glob pattern]
promptlint --file "prompts/**/*.txt"
```

```bash [Shell loop]
for f in prompts/*.txt; do
  promptlint --file "$f" --format json
done
```

```bash [GitHub Actions]
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
```

:::

## What does the score mean?

The score (0–100) is a weighted sum:

- Start at 100
- Subtract 30 for each CRITICAL finding
- Subtract 10 for each WARN finding
- Subtract 5 for each INFO finding
- Clamped to 0

Grades: A (90+), B (80+), C (70+), D (60+), F (< 60)

## How do I add a custom injection pattern?

```yaml
# .promptlintrc
rules:
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions   # built-in
      - admin override:                 # custom
      - execute as root:                # custom
```

Patterns are matched case-insensitively as substrings (not full regex by default).

## Can I use PromptLint in Docker?

Yes. See the [Docker integration guide](/integrations/docker).

## Where do I report bugs or request features?

[Open an issue on GitHub](https://github.com/AryaanSheth/promptlint/issues).
