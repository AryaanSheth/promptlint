# `hallucination-risk` — Hallucination Risk Detection

**Severity:** WARN · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Detects prompt patterns that statistically increase the likelihood of hallucinated output — fabricated facts, invented citations, or made-up statistics.

## High-Risk Patterns

| Pattern | Why it's risky |
|---------|----------------|
| `list all`, `name all`, `enumerate every` | Model invents items to complete the list |
| `when was`, `who invented`, `what year` | Factual recall questions the model may confabulate |
| `cite sources`, `provide references` | Model fabricates plausible-sounding citations |
| `give statistics`, `provide data` | Model invents numbers |
| Open-ended creative + factual mix | Model can't distinguish invention from recall |

## Example

**Prompt:**
```
List all the papers published on transformer architectures in 2023
and cite the authors for each.
```

**Finding:**
```
[ WARN ] hallucination-risk (line 1)
  High hallucination risk: 'list all' + citation request.
  Models frequently fabricate papers and authors.
  Consider: grounding with a document, RAG, or restricting to known data.
```

## Mitigations

The rule doesn't block — it warns. Common mitigations:

1. **Ground with a document** — Provide the source material and ask the model to extract from it
2. **RAG** — Retrieve relevant chunks before prompting
3. **Restrict scope** — "Based only on the context below, list..." instead of open-ended recall
4. **Add uncertainty instruction** — "If you don't know, say 'I don't know' rather than guessing"

## Configuration

```yaml
rules:
  hallucination_risk: true  # or false to disable
```

## Example: Safer Prompting

::: danger High hallucination risk
```
List all the major breakthroughs in quantum computing in the last 5 years
with citations.
```
:::

::: tip Grounded alternative
```
Based only on the provided research summary below, list the quantum computing
breakthroughs mentioned. If a breakthrough isn't mentioned in the text, do not
include it.

<context>
{{RESEARCH_SUMMARY}}
</context>
```
:::
