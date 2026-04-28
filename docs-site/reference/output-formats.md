# Output Formats

PromptLint supports three output formats: `text`, `json`, and `sarif`.

## Text (default)

Colored terminal output for human reading. Uses ANSI colors and the `rich` library (Python) or ANSI escapes (Node.js).

```bash
promptlint --file prompt.txt
# or explicitly:
promptlint --file prompt.txt --format text
```

**Example output:**
```
  PromptLint v1.3.0

  ┌─────────────────────────────────────────────────────────────┐
  │  File: prompt.txt  (97 tokens · ~$0.0005)                  │
  └─────────────────────────────────────────────────────────────┘

  [ CRITICAL ] prompt-injection (line 2)
    Injection pattern detected: 'ignore previous instructions'

  [ WARN ] structure-sections (line -)
    No explicit sections detected (Task / Context / Output)

  [ INFO ] specificity-examples (line -)
    No examples provided

  ────────────────────────────────────────────────────────────────
  Score: 55/100  Grade: F   3 findings  (1 critical · 1 warn · 1 info)
  Run with --fix to auto-resolve 2 of these issues
```

### Disable Color

```bash
promptlint --file prompt.txt --no-color
```

## JSON

Machine-readable format for CI/CD parsing and downstream tooling.

```bash
promptlint --file prompt.txt --format json
```

**Schema:**
```typescript
{
  version: string,
  file: string | null,
  token_count: number,
  score: number,        // 0-100
  grade: string,        // "A" | "B" | "C" | "D" | "F"
  findings: Array<{
    rule_id: string,
    level: "CRITICAL" | "WARN" | "INFO",
    line: number,       // -1 for file-level findings
    message: string
  }>,
  summary: {
    total: number,
    critical: number,
    warn: number,
    info: number
  }
}
```

**Example:**
```json
{
  "version": "1.3.0",
  "file": "prompt.txt",
  "token_count": 97,
  "score": 55,
  "grade": "F",
  "findings": [
    {
      "rule_id": "prompt-injection",
      "level": "CRITICAL",
      "line": 2,
      "message": "Injection pattern detected: 'ignore previous instructions'"
    },
    {
      "rule_id": "structure-sections",
      "level": "WARN",
      "line": -1,
      "message": "No explicit sections detected (Task / Context / Output)"
    }
  ],
  "summary": {
    "total": 2,
    "critical": 1,
    "warn": 1,
    "info": 0
  }
}
```

### Working with JSON in CI

```bash
# Count critical findings
promptlint --file prompt.txt --format json | jq '.summary.critical'

# Extract all critical messages
promptlint --file prompt.txt --format json \
  | jq '[.findings[] | select(.level == "CRITICAL") | .message]'

# Fail if score < 70
SCORE=$(promptlint --file prompt.txt --format json | jq '.score')
[ "$SCORE" -ge 70 ] || (echo "Score too low: $SCORE" && exit 1)
```

## SARIF (v2.1.0)

[Static Analysis Results Interchange Format](https://sarifweb.azurewebsites.net/) — the standard format for security scanning tools. Integrates with GitHub's Security tab.

```bash
promptlint --file prompt.txt --format sarif > results.sarif
```

### GitHub Security Tab Integration

```yaml
# .github/workflows/prompt-security.yml
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Install PromptLint
        run: pip install promptlint-cli
      - name: Scan prompts
        run: promptlint --file "prompts/**/*.txt" --format sarif > results.sarif
      - name: Upload to Security tab
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: results.sarif
```

Or use the dedicated GitHub Action which handles this automatically:

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    sarif-output: true
```
