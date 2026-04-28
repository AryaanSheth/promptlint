# `verbosity-sentence-length` — Long Sentence Detection

**Severity:** INFO · **Auto-fix:** No · **Category:** 📝 Verbosity

## What It Does

Flags sentences longer than 40 words. Very long sentences are harder for models to parse and more likely to have parts de-emphasized or ignored.

## Example

**Prompt with long sentence:**
```
Write a Python function that accepts a list of dictionaries containing user data
including name, email address, phone number, and age and validates each field
according to the business rules defined in the specification document and returns
a list of validation errors for each invalid record along with the record index.
```

**Finding:**
```
[ INFO ] verbosity-sentence-length (line 1)
  Long sentence: 52 words. Consider splitting into multiple shorter sentences
  or using a bulleted list.
```

## Recommended Fix

Break long sentences into bullet points or numbered steps:

```
Write a Python function that:
1. Accepts a list of user dictionaries (name, email, phone, age)
2. Validates each field against the business rules in the spec
3. Returns a list of `{"index": int, "field": str, "error": str}` dicts
   for each invalid record
```

## Configuration

```yaml
rules:
  verbosity_sentence_length: true
```

The threshold is fixed at 40 words and cannot be configured in v1.3.0.

## Why It Matters

Models have attention patterns that can under-weight the end of very long sentences. Breaking complex instructions into lists or numbered steps improves both token efficiency and output accuracy.
