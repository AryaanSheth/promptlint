# Rules Overview

PromptLint ships **20 rules** covering security, cost, structure, and quality. Every rule can be individually enabled, disabled, or have its severity overridden.

## All Rules

| Rule | Severity | Auto-Fix | Category |
|------|:--------:|:--------:|----------|
| [`cost`](/rules/cost) | INFO | — | 💰 Cost |
| [`cost-limit`](/rules/cost-limit) | CRITICAL | — | 💰 Cost |
| [`prompt-injection`](/rules/prompt-injection) | CRITICAL | ✅ | 🔒 Security |
| [`jailbreak-pattern`](/rules/jailbreak-pattern) | CRITICAL | — | 🔒 Security |
| [`secret-in-prompt`](/rules/secret-in-prompt) | CRITICAL | — | 🔒 Security |
| [`pii-in-prompt`](/rules/pii-in-prompt) | CRITICAL | — | 🔒 Security |
| [`context-injection-boundary`](/rules/context-injection-boundary) | CRITICAL | — | 🔒 Security |
| [`structure-sections`](/rules/structure-sections) | WARN | ✅ | 🏗️ Structure |
| [`role-clarity`](/rules/role-clarity) | WARN | — | 🏗️ Structure |
| [`output-format-missing`](/rules/output-format-missing) | WARN | — | 🏗️ Structure |
| [`hallucination-risk`](/rules/hallucination-risk) | WARN | — | 🏗️ Structure |
| [`clarity-vague-terms`](/rules/clarity-vague-terms) | WARN | — | ✨ Quality |
| [`specificity-examples`](/rules/specificity-examples) | INFO | — | 🎯 Specificity |
| [`specificity-constraints`](/rules/specificity-constraints) | INFO | — | 🎯 Specificity |
| [`politeness-bloat`](/rules/politeness-bloat) | WARN | ✅ | 📝 Verbosity |
| [`verbosity-redundancy`](/rules/verbosity-redundancy) | INFO | ✅ | 📝 Verbosity |
| [`verbosity-sentence-length`](/rules/verbosity-sentence-length) | INFO | — | 📝 Verbosity |
| [`actionability-weak-verbs`](/rules/actionability-weak-verbs) | INFO | — | 💪 Actionability |
| [`consistency-terminology`](/rules/consistency-terminology) | INFO | — | 🔄 Consistency |
| [`completeness-edge-cases`](/rules/completeness-edge-cases) | INFO | — | ✅ Completeness |

## By Category {#by-category}

### 🔒 Security {#security}

The five security rules fire at **CRITICAL** severity by default. They should never be disabled in production pipelines.

| Rule | What it catches |
|------|----------------|
| [`prompt-injection`](/rules/prompt-injection) | Classic injection phrases like "ignore previous instructions" |
| [`jailbreak-pattern`](/rules/jailbreak-pattern) | Jailbreak attempts like "DAN mode", roleplay overrides, persona hijacking |
| [`secret-in-prompt`](/rules/secret-in-prompt) | API keys, passwords, connection strings, tokens |
| [`pii-in-prompt`](/rules/pii-in-prompt) | Email addresses, phone numbers, SSNs, credit card numbers |
| [`context-injection-boundary`](/rules/context-injection-boundary) | User-injected content without a trust boundary marker |

### 💰 Cost & Tokens

| Rule | What it catches |
|------|----------------|
| [`cost`](/rules/cost) | Token count and projected cost (INFO, always informational) |
| [`cost-limit`](/rules/cost-limit) | Prompt exceeds configured `token_limit` |

### 🏗️ Structure {#structure}

| Rule | What it catches |
|------|----------------|
| [`structure-sections`](/rules/structure-sections) | No task / context / output sections detected |
| [`role-clarity`](/rules/role-clarity) | No role or persona defined for the model |
| [`output-format-missing`](/rules/output-format-missing) | No output format specification |
| [`hallucination-risk`](/rules/hallucination-risk) | Patterns that increase hallucination likelihood |

### ✨ Quality {#quality}

| Rule | What it catches |
|------|----------------|
| [`clarity-vague-terms`](/rules/clarity-vague-terms) | Vague words: "good", "efficient", "things", "various", "proper" |
| [`specificity-examples`](/rules/specificity-examples) | No examples / few-shot demonstrations provided |
| [`specificity-constraints`](/rules/specificity-constraints) | No constraints on what the model should NOT do |
| [`politeness-bloat`](/rules/politeness-bloat) | Unnecessary politeness tokens ("please", "kindly", "thank you") |
| [`verbosity-redundancy`](/rules/verbosity-redundancy) | Redundant phrases ("in order to", "as well as") |
| [`verbosity-sentence-length`](/rules/verbosity-sentence-length) | Sentences over 40 words |
| [`actionability-weak-verbs`](/rules/actionability-weak-verbs) | Passive voice and weak verbs ("be done", "be written") |
| [`consistency-terminology`](/rules/consistency-terminology) | Same concept referred to by multiple names |
| [`completeness-edge-cases`](/rules/completeness-edge-cases) | No edge case handling defined |

## Severity Levels

| Severity | Default exit code | Meaning |
|----------|:-----------------:|---------|
| `CRITICAL` | `2` | Security or hard constraint violation — must fix |
| `WARN` | `1` | Structural or quality issue — should fix |
| `INFO` | `0` | Optimization suggestion — consider fixing |

Override exit code threshold with `--fail-level`:

```bash
promptlint --file prompt.txt --fail-level warn  # exit 1 on any WARN or above
promptlint --file prompt.txt --fail-level info  # exit 1 on any finding
```

## Disabling Rules

```yaml
# .promptlintrc
rules:
  completeness_edge_cases: false
  actionability_weak_verbs: false
```
