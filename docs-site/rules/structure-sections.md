# `structure-sections` — Prompt Organization

**Severity:** WARN · **Auto-fix:** Yes · **Category:** 🏗️ Structure

## What It Does

Checks that the prompt has explicit organizational sections for task, context, and output format. Unstructured prompts produce inconsistent model output and are harder to maintain.

## Example

**Unstructured prompt:**
```
Write a function that calculates fibonacci numbers and handles errors properly
and returns JSON format and should be efficient.
```

**Findings:**
```
[ WARN ] structure-sections (line -)
  No explicit sections detected (Task / Context / Output).

[ INFO ] structure-sections (line -)
  Recommended: XML tags (<task>, <context>, <output_format>),
  headings (Task:, Context:, Output:), or Markdown (## sections)
```

**After `--fix`:**
```xml
<task>
Write a function that calculates fibonacci numbers and handles errors properly
and returns JSON format and should be efficient.
</task>
```

## Recognized Structure Formats

The rule considers a prompt "structured" if it contains any of:

| Format | Example |
|--------|---------|
| XML tags | `<task>`, `<context>`, `<output_format>`, `<instructions>` |
| Markdown headings | `## Task`, `## Context`, `## Output` |
| Labeled sections | `Task:`, `Context:`, `Output Format:` |
| Role prefix | `You are ...` (counts as role section) |

## Auto-Fix Behavior

The auto-fix behavior depends on `structure_style` in `.promptlintrc`:

| `structure_style` | Output |
|-------------------|--------|
| `xml` (default) | Wraps content in `<task>...</task>` |
| `headings` | Adds `Task:` heading prefix |
| `markdown` | Adds `## Task` heading |
| `auto` | Detects existing style and matches |
| `none` | Auto-fix disabled for this rule |

## Configuration

```yaml
structure_style: xml  # or "headings", "markdown", "auto", "none"

rules:
  structure_sections: true

fix:
  structure_scaffold: true
```

## Why It Matters

Structured prompts:
- Produce more consistent output
- Are easier to read and maintain
- Help the model understand what's instruction vs. data
- Enable better few-shot learning when examples are clearly separated
