# `hallucination-risk` — Hallucination Risk Detection

**Severity:** WARN · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Detects prompts that ask for factual or current information without providing grounding context. Open-ended factual questions are the primary trigger for model hallucination — the model generates plausible-sounding but invented answers.

## Trigger Conditions

The rule fires when:
1. The prompt contains a **factual question pattern** (any of the below), AND
2. The prompt does NOT contain a **grounding indicator** (any of the below)

## Factual Question Patterns (trigger the check)

| Pattern group | Examples |
|--------------|---------|
| Factual wh-questions | `what is`, `what are`, `who is`, `who are`, `when did`, `when was`, `where is`, `how many`, `how much` |
| Currency/recency signals | `currently`, `latest`, `recently`, `today`, `now`, `as of`, `up to date` |
| Summary requests | `tell me about`, `give me a list of`, `give me a summary of`, `give me an overview of` |

## Grounding Indicators (suppress the check)

| Indicator | Example |
|-----------|---------|
| Template variable | `{context}`, `{{DOCUMENT}}` |
| `<context>` tag | `<context>The following is the report...</context>` |
| `Context:` label | `Context: Here is the data...` |
| Code fence | ` ```json ` |
| "Given the following" | `Given the following document...` |
| "Based on the following/above/provided" | `Based on the provided text...` |
| "Using the data/information/context below/above" | `Using the context below...` |

## Examples

::: danger Triggers the rule
```
What are the latest developments in quantum computing?
Who is the current CEO of OpenAI?
How many parameters does GPT-4 have?
```

Finding:
```
[ WARN ] hallucination-risk (line -)
  Prompt requests factual/current information without grounding context.
  Consider adding a {context} variable or <context> section with source data.
```
:::

::: tip Grounded — passes
```
Based on the provided research brief, what are the latest developments
in quantum computing mentioned?

<context>
{{RESEARCH_BRIEF}}
</context>
```
Has `Based on the provided` + `<context>` → no finding.
:::

## False Positives

**Factual questions with known-static answers** — "What is 2+2?" or "What is the capital of France?" will trigger the rule because they contain `what is`. These are legitimate zero-shot questions where the model's training data is reliable. The rule errs on the side of caution — you can disable it for prompts you're confident are low-hallucination-risk.

**Prompts that ground via the system prompt** — if your grounding context is in a separate system prompt and your user-turn prompt just asks "What are the latest developments?", the rule will fire on the user-turn text alone. You can disable the rule if you handle grounding at the orchestration layer.

**"Currently" in instructions** — "Currently, the user is on step 3" doesn't ask for factual recall, but `currently` will still trigger the check. Use `At this point` instead.

## Configuration

```yaml
rules:
  hallucination_risk: true   # or false to disable
```

Demote to INFO:
```yaml
rules:
  hallucination_risk:
    enabled: true
    level: info
```

## Mitigations

The rule flags — it doesn't fix. Standard mitigations:

1. **RAG (Retrieval-Augmented Generation)** — retrieve relevant chunks, inject as context
2. **Explicit grounding** — "Based only on the document below, answer..." 
3. **Uncertainty instruction** — "If you don't know, say 'I don't know' rather than guessing"
4. **Source citation requirement** — "Cite the specific sentence from the context that supports your answer"

::: tip Example: grounding pattern
```
<role>You are a research analyst.</role>
<task>Answer the question based strictly on the provided research brief.</task>
<constraints>
- Do not use knowledge from outside the provided context
- If the answer is not in the context, say "Not mentioned in the provided brief"
- Quote the relevant sentence when possible
</constraints>
<context>
{{RESEARCH_BRIEF}}
</context>
<question>{{USER_QUESTION}}</question>
```
:::
