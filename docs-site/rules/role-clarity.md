# `role-clarity` — Role Definition Check

**Severity:** WARN · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Checks that the prompt defines a role or persona for the model. Prompts without a role rely on the model's default behavior, which is inconsistent across model versions.

## Example

::: danger Missing role
```
Write a technical blog post about Kubernetes networking.
Return it in Markdown format with code examples.
```

Finding:
```
[ WARN ] role-clarity (line -)
  No role defined. Add a persona (e.g., "You are a senior DevOps engineer")
  to improve consistency and output quality.
```
:::

::: tip With role
```
You are a senior DevOps engineer with 10 years of Kubernetes experience.
Write a technical blog post about Kubernetes networking.
Return it in Markdown format with code examples.
```
:::

## What Counts as a Role

The rule considers these as valid role definitions:
- `You are a [role]`
- `Act as a [role]`
- `<role>...</role>` XML tag
- `Role:` or `Persona:` heading
- `As a [role],`

## Configuration

```yaml
rules:
  role_clarity: true  # or false to disable
```

## Why It Matters

A role definition:
- Sets the model's expertise level and tone
- Reduces hallucination by anchoring the model's "perspective"
- Improves consistency across model versions
- Lets you tune formality and technical depth

Without a role, the same prompt can produce dramatically different output between GPT-3.5 and GPT-4o, or between Claude versions.
