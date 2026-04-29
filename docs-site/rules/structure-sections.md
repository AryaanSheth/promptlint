# `structure-sections` — Prompt Organization

**Severity:** WARN · **Auto-fix:** Yes · **Category:** 🏗️ Structure

## What It Does

Checks that the prompt has some form of explicit structure. Structureless prompts — a wall of text with no sections — produce inconsistent output and are harder to maintain and iterate on.

## What Counts as "Structured"

The rule considers a prompt structured if it contains **any** of these:

| Signal | Example |
|--------|---------|
| XML tags | `<task>`, `<context>`, `<output_format>`, `<role>` |
| Labeled headings | `Task:`, `Context:`, `Output:`, `Goal:`, `Requirements:`, `Instructions:` |
| Markdown headers | `## Task`, `# Instructions`, `### Output Format` |
| JSON structure | `{"key": "value"}` or `["item"]` with quotes |
| Code fences or `---` | ` ```python ` or `---` horizontal rules |
| Numbered sections | `1. `, `2. `, `3. ` at the start of lines |

::: tip The bar is intentionally low
If your prompt has *any* structure at all — even just `1. Do X\n2. Do Y` — this rule won't fire. It's looking for completely unstructured walls of text, not enforcing a specific structure format.
:::

## When the Rule Fires

**Fires:**
```
Write a function that parses JSON data and returns a dictionary handling
errors gracefully and logging exceptions and returning None on failure.
```
No tags, headings, numbering, or delimiters → WARN.

**Does NOT fire:**
```
1. Parse JSON data from the input string.
2. Return a dictionary on success.
3. Return None and log the exception on failure.
```
Numbered list = structured → no finding.

## Example Output

```
[ WARN ] structure-sections (line -)
  No explicit sections detected (Task/Context/Output).

[ INFO ] structure-recommendations (line -)
  Recommended templates: headings (Task:, Context:, Output:) /
  XML tags (<task>) / Markdown (## sections)
```

Two findings are emitted: the WARN for the missing structure, plus an INFO recommendation suggesting format options.

## Auto-Fix

When `--fix` is passed, PromptLint wraps the prompt in a `<task>` tag (or uses the configured `structure_style`):

**Before:**
```
Write a function to parse JSON.
```

**After (`structure_style: xml`):**
```xml
<task>
Write a function to parse JSON.
</task>
```

::: warning Auto-fix only adds a task wrapper
The scaffold only wraps the existing content in a `<task>` tag. It does **not** infer and add `<context>` or `<output_format>` sections — those require understanding your intent. Use the scaffold as a starting point and add the other sections manually.
:::

## Configuration

```yaml
structure_style: xml   # "xml" | "headings" | "markdown" | "auto" | "none"

rules:
  structure_sections: true

fix:
  structure_scaffold: true
```

| `structure_style` | Auto-fix output |
|-------------------|----------------|
| `xml` (default) | `<task>...</task>` |
| `headings` | `Task:\n...` |
| `markdown` | `## Task\n...` |
| `auto` | Detects existing style and matches it |
| `none` | Auto-fix disabled for this rule |

## False Positives

**Short prompts** — a 10-word prompt like "Translate this to French" is fine unstructured. The rule fires regardless of prompt length. If you have intentionally terse prompts (translation, simple Q&A), disable the rule or use a short labeled heading.

**Prompts that are themselves JSON/code** — if your prompt *is* a JSON object or a code snippet, the rule won't fire (those count as structured). But if you're asking about code and the prompt contains a code fence, it also won't fire.

## Why Structure Matters

Structured prompts:
- Give the model explicit signal about what's task vs. context vs. format
- Are easier to maintain as your requirements evolve
- Enable reliable few-shot patterns when the structure is consistent
- Make it obvious when sections are missing (e.g., `<output_format>` not present)
