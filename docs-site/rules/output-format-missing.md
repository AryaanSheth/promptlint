# `output-format-missing` — Output Format Specification

**Severity:** WARN · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Detects prompts that contain an output instruction verb but don't specify the output format. When you tell the model to "extract", "list", or "return" something but don't say *how*, the format varies between models, versions, and even individual runs.

## Trigger Conditions

::: warning Two conditions must both be true
1. The prompt is **at least 60 characters long**
2. The prompt contains an **output instruction verb** (below) AND does **not** contain a format keyword (below)
:::

## Output Instruction Verbs (trigger the check)

`list`, `extract`, `find`, `return`, `give me`, `provide`, `output`, `generate`, `create`, `show`, `summarize`, `identify`, `enumerate`

## Format Keywords (suppress the check)

`JSON`, `XML`, `CSV`, `Markdown`, `bullet`, `numbered`, `table`, `plain text`, `HTML`, `YAML`, `format:`, `return as`, `output as`, `structured as`, `schema`

## Examples

::: danger Triggers the rule
```
Extract all company names and dates from the document.
Provide a summary of the key findings.
```
Has `extract`, `provide`, `summary` — no format keyword.

```
[ WARN ] output-format-missing (line -)
  Output instruction detected but no format specified (JSON, markdown,
  bullet list, etc.). Unspecified format produces inconsistent results.
```
:::

::: tip Passes the rule
```
Extract all company names and dates from the document.
Return a JSON array of objects with {"company": string, "date": "YYYY-MM-DD"}.
Provide a markdown bullet list summary of the key findings.
```
Has `JSON` and `markdown` → no finding.
:::

## False Positives

**Creative prompts** — "Write a poem about autumn" has the verb `write` (which isn't in the trigger list), so it won't fire. But "Generate a poem about autumn" will fire because `generate` is a trigger verb and there's no format keyword. Add "in free verse format" or "as a haiku" to suppress.

**Short prompts** — prompts under 60 characters don't trigger this rule. `List the planets` (18 chars) won't fire.

**The word "table" in non-format context** — "Extract data from the accounting table" contains `table` as a non-format word, which would suppress the finding even though no output format is specified. Be explicit: "Return a markdown table" vs. "from the database table".

## Configuration

```yaml
rules:
  output_format_missing: true   # or false to disable
```

Demote to INFO:
```yaml
rules:
  output_format_missing:
    enabled: true
    level: info
```

## Recommended Fix

Add an explicit `<output_format>` section specifying the exact schema:

```
<task>Extract all company names and dates from the document.</task>

<output_format>
Return a JSON array only — no prose before or after.
Schema:
[
  {
    "company": "string",
    "date": "YYYY-MM-DD",
    "confidence": "high|medium|low"
  }
]
If no entities are found, return an empty array [].
</output_format>
```

## Why Format Specification Matters

Without a format spec:
- GPT-4o and Claude may format the same data differently
- JSON responses may or may not be wrapped in markdown code fences
- Lists may be bulleted, numbered, or inline depending on the model's mood
- Parsing downstream output becomes fragile and requires defensive code
- Model upgrades can silently break your output format
