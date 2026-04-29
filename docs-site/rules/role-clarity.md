# `role-clarity` — Role Definition Check

**Severity:** WARN · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Checks that the prompt defines a role or persona for the model. Prompts without a role rely on the model's default behavior, which varies between model versions and can produce inconsistent tone, expertise level, and format.

## Trigger Conditions

::: warning Three conditions must all be true for this rule to fire
1. The prompt is **at least 30 words long** — short prompts aren't expected to have a role definition
2. The prompt contains **instructional language** (words like `you`, `respond`, `answer`, `help`, `assist`, `always`, `never`, `must`, `should`)
3. The prompt **does not contain** a recognized role definition phrase
:::

This means the rule won't fire on a simple 5-word translation request, only on prompts that are clearly giving behavioral instructions to the model.

## Recognized Role Phrases

The rule considers any of these as a valid role definition:

| Phrase | Example |
|--------|---------|
| `you are` / `you're` | `You are a helpful assistant.` |
| `act as` | `Act as a senior Python engineer.` |
| `your role is` | `Your role is to review code.` |
| `you will serve as` | `You will serve as a technical reviewer.` |
| `you work as` | `You work as a customer support agent.` |
| `your job is` | `Your job is to extract key information.` |
| `your task is` | `Your task is to summarize the document.` |
| `you are responsible for` | `You are responsible for validating inputs.` |
| `you specialize in` | `You specialize in financial analysis.` |

## Example

::: danger No role — fires
```
Always respond in formal English. You must answer questions about our product
only. Never discuss competitor products. Keep responses under 3 sentences.
```

Finding:
```
[ WARN ] role-clarity (line -)
  No role or persona defined. Add 'You are a [role]...' to improve
  output consistency.
```
This has 30+ words and clear instructions (`always`, `must`, `never`) — but no role.
:::

::: tip With role — passes
```
You are a formal customer support specialist for Acme Corp.
Always respond in formal English. You must answer questions about our product
only. Never discuss competitor products. Keep responses under 3 sentences.
```
:::

## False Positives

**Data extraction prompts** — a prompt like `Extract all dates from the following text and return JSON` is 14 words with no instructional keywords (`you`, `respond`, `must`). It won't trigger despite having no role.

**Prompts with implicit role via structure** — if you use `<role>Senior Python Engineer</role>` in XML, this is NOT currently recognized (the rule only checks for the phrases above). Add `You are a senior Python engineer.` to be safe.

## Configuration

```yaml
rules:
  role_clarity: true   # or false to disable
```

Demote to INFO if role-less prompts are acceptable in your use case:
```yaml
rules:
  role_clarity:
    enabled: true
    level: info
```

## Why Roles Matter

A role definition:
- Sets the model's implicit expertise level and calibrates its vocabulary
- Reduces hallucination by anchoring the model's "perspective"
- Improves consistency when the same prompt runs across different model versions
- Lets you control formality and domain specificity without spelling it out in every sentence

Without a role, the same prompt can produce dramatically different output between GPT-4o and GPT-3.5, or between Claude 3 Haiku and Claude 3.5 Sonnet.
