# `output-format-missing` — Output Format Specification

**Severity:** WARN · **Auto-fix:** No · **Category:** 🏗️ Structure

## What It Does

Checks that the prompt explicitly specifies the desired output format. Without a format spec, the model picks its own — and that choice varies by model, version, and temperature.

## Example

::: danger Missing format
```
You are a data analyst.
Extract the key metrics from the following report.
```

Finding:
```
[ WARN ] output-format-missing (line -)
  No output format specified. Define the expected format to ensure
  consistent, parseable output (e.g., JSON, Markdown table, plain text).
```
:::

::: tip With format
```
You are a data analyst.
Extract the key metrics from the following report.

<output_format>
Return a JSON object with this schema:
{
  "metrics": [
    {"name": string, "value": number, "unit": string}
  ],
  "period": string,
  "source": string
}
No prose before or after the JSON.
</output_format>
```
:::

## What Counts as a Format Spec

The rule looks for:
- `output_format`, `output-format`, `Output Format:` labels
- `Return ...` or `Respond with ...` instructions that specify a format
- Format keywords: `JSON`, `Markdown`, `CSV`, `XML`, `YAML`, `plain text`
- Schema definitions

## Configuration

```yaml
rules:
  output_format_missing: true  # or false to disable
```

## Why It Matters

Without a format spec:
- JSON responses may or may not include markdown code fences
- Lists may be bulleted, numbered, or prose depending on the model
- Parsing downstream output becomes fragile
- Model upgrades can silently break your output format

Always specify format explicitly, especially for programmatic consumers.
