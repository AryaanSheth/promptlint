# CLI Reference

Complete command-line interface reference for PromptLint.

## Basic Usage

```bash
python -m promptlint.cli [OPTIONS]
```

## Quick Examples

```bash
# Lint a file
python -m promptlint.cli --file prompt.txt

# Lint inline text
python -m promptlint.cli --text "Please write a function"

# Auto-fix issues
python -m promptlint.cli --file prompt.txt --fix

# JSON output for CI/CD
python -m promptlint.cli --file prompt.txt --format json

# Show cost savings dashboard
python -m promptlint.cli --file prompt.txt --show-dashboard

# Custom config
python -m promptlint.cli --file prompt.txt --config myconfig.yaml

# Strict mode (fail on warnings)
python -m promptlint.cli --file prompt.txt --fail-level warn
```

---

## Options

### Input Options

#### `--file, -f PATH`

Path to prompt file to analyze.

**Example:**
```bash
python -m promptlint.cli --file prompts/system_prompt.txt
```

**Multiple files:**
```bash
# Lint multiple files (run separately)
for file in prompts/*.txt; do
  python -m promptlint.cli --file "$file"
done
```

---

#### `--text, -t TEXT`

Inline prompt text to analyze (alternative to `--file`).

**Example:**
```bash
python -m promptlint.cli --text "Write a Python function to calculate fibonacci"
```

**With quotes:**
```bash
# Use quotes for multi-line text
python -m promptlint.cli --text "Task: Write a function
Context: For production API
Output: JSON format"
```

**Note:** Either `--file` or `--text` is required, but not both.

---

### Configuration Options

#### `--config, -c PATH`

Path to custom configuration file.

**Default:** `.promptlintrc` (in current directory)

**Example:**
```bash
# Use custom config
python -m promptlint.cli --file prompt.txt --config configs/production.yaml

# Use shared team config
python -m promptlint.cli --file prompt.txt --config ~/.promptlintrc
```

**Config search order:**
1. Path specified with `--config`
2. `.promptlintrc` in current directory
3. Default built-in configuration

---

### Output Options

#### `--format FORMAT`

Output format: `text` or `json`.

**Default:** `text`

**Text Format (default):**
```bash
python -m promptlint.cli --file prompt.txt --format text
```

**Output:**
```
PromptLint Findings
[ WARN ] politeness-bloat (line 1) Consider removing 'Please'...
Please write a function
^
```

**JSON Format:**
```bash
python -m promptlint.cli --file prompt.txt --format json
```

**Output:**
```json
{
  "findings": [
    {
      "level": "WARN",
      "rule": "politeness-bloat",
      "message": "Consider removing 'Please'...",
      "line": 1,
      "context": "Please write a function\n^"
    }
  ],
  "optimized_prompt": null,
  "dashboard": {
    "current_tokens": 12,
    "optimized_tokens": 12,
    "tokens_saved": 0,
    "reduction_percentage": 0.0,
    "savings_per_call": 0.0
  }
}
```

**Use cases for JSON:**
- CI/CD pipelines
- Analytics dashboards
- Integration with other tools
- Automated processing

---

#### `--show-dashboard`

Include savings dashboard in output.

**Example:**
```bash
python -m promptlint.cli --file prompt.txt --show-dashboard
```

**Output:**
```
PromptLint Findings
[ INFO ] cost (line -) Prompt is ~97 tokens...
[ WARN ] politeness-bloat (line 1)...

Savings Dashboard
Current Tokens: 97
Optimized Tokens: 59 (39.2% reduction)
Savings per Call: ~$0.0002
Monthly Savings: ~$57.00 at 10,000 calls/day
Annual Savings: ~$693.50
```

**Note:** Dashboard is always included in JSON output.

---

### Fix Options

#### `--fix`

Apply auto-fixes and output optimized prompt.

**Example:**
```bash
python -m promptlint.cli --file prompt.txt --fix
```

**Output:**
```
PromptLint Findings
(... findings ...)

Optimized Prompt
<task>Write a function that calculates fibonacci numbers.</task>
```

**What gets fixed:**
1. **Politeness bloat** - Removes `please`, `thank you`, etc.
2. **Redundancy** - Simplifies verbose phrases
3. **Injection** - Removes dangerous patterns
4. **Structure** - Adds missing tags (if configured)
5. **Punctuation** - Normalizes spacing and punctuation

**Control auto-fixes in config:**
```yaml
fix:
  enabled: true
  politeness_bloat: true
  verbosity_redundancy: true
  prompt_injection: true
  structure_scaffold: false  # Disable this fix
```

---

### Exit Code Options

#### `--fail-level LEVEL`

Exit code behavior based on finding severity.

**Options:**
- `none` - Always exit 0 (advisory mode)
- `warn` - Exit 1 on WARN or CRITICAL
- `critical` - Exit 2 on CRITICAL only (default)

**Default:** `critical`

**Examples:**

**Advisory mode (never fail):**
```bash
python -m promptlint.cli --file prompt.txt --fail-level none
echo $?  # Always 0
```

**Strict mode (fail on warnings):**
```bash
python -m promptlint.cli --file prompt.txt --fail-level warn
echo $?  # 1 if WARN or CRITICAL found, else 0
```

**Security mode (fail on security issues only):**
```bash
python -m promptlint.cli --file prompt.txt --fail-level critical
echo $?  # 2 if CRITICAL found, else 0
```

**Exit codes:**
- `0` - No issues or below fail threshold
- `1` - WARN-level issues (when `--fail-level warn`)
- `2` - CRITICAL-level issues (when `--fail-level critical` or `warn`)

---

## Advanced Usage

### Piping Input

Read from stdin:
```bash
echo "Please write a function" | python -m promptlint.cli --text "$(cat)"
```

### Redirect Output

Save findings to file:
```bash
python -m promptlint.cli --file prompt.txt > findings.txt 2>&1
```

### JSON Processing with jq

Extract specific data:
```bash
# Get token count only
python -m promptlint.cli --file prompt.txt --format json | jq '.dashboard.current_tokens'

# Get all WARN findings
python -m promptlint.cli --file prompt.txt --format json | jq '.findings[] | select(.level=="WARN")'

# Count findings by level
python -m promptlint.cli --file prompt.txt --format json | jq '.findings | group_by(.level) | map({level: .[0].level, count: length})'
```

### Batch Processing

**Process multiple files:**
```bash
#!/bin/bash
for file in prompts/*.txt; do
  echo "Analyzing $file..."
  python -m promptlint.cli --file "$file" --format json > "reports/$(basename $file .txt).json"
done
```

**Aggregate results:**
```bash
#!/bin/bash
total_savings=0
for file in prompts/*.txt; do
  savings=$(python -m promptlint.cli --file "$file" --format json | jq '.dashboard.savings_per_call')
  total_savings=$(echo "$total_savings + $savings" | bc)
done
echo "Total savings: $total_savings"
```

---

## CI/CD Integration

### GitHub Actions

```yaml
name: PromptLint

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          pip install -r requirements.txt
      
      - name: Run PromptLint
        run: |
          python -m promptlint.cli --file prompts/system_prompt.txt --fail-level warn --format json
```

### GitLab CI

```yaml
promptlint:
  image: python:3.9
  script:
    - pip install -r requirements.txt
    - python -m promptlint.cli --file prompts/*.txt --fail-level critical --format json
  only:
    - merge_requests
    - main
```

### Pre-commit Hook

`.git/hooks/pre-commit`:
```bash
#!/bin/bash

echo "Running PromptLint..."

# Find all prompt files that are staged
for file in $(git diff --cached --name-only --diff-filter=ACM | grep -E '\.txt$|prompts/'); do
  python -m promptlint.cli --file "$file" --fail-level warn
  if [ $? -ne 0 ]; then
    echo "PromptLint failed for $file"
    exit 1
  fi
done

echo "PromptLint passed!"
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

---

## Environment Variables

### `PROMPTLINT_CONFIG`

Override default config path:
```bash
export PROMPTLINT_CONFIG=/path/to/.promptlintrc
python -m promptlint.cli --file prompt.txt
```

### `PROMPTLINT_FAIL_LEVEL`

Default fail level:
```bash
export PROMPTLINT_FAIL_LEVEL=warn
python -m promptlint.cli --file prompt.txt  # Uses warn level
```

---

## Troubleshooting

### "No module named promptlint"

**Problem:** Python can't find the module.

**Solution:**
```bash
# Ensure you're in the project directory
cd /path/to/promptlint

# Install dependencies
pip install -r requirements.txt

# Run with python -m
python -m promptlint.cli --help
```

---

### "FileNotFoundError: [Errno 2] No such file or directory"

**Problem:** Specified file doesn't exist.

**Solution:**
```bash
# Check file path
ls -la prompt.txt

# Use absolute path
python -m promptlint.cli --file /absolute/path/to/prompt.txt

# Or relative from current directory
python -m promptlint.cli --file ./prompts/system.txt
```

---

### "Config file not loading"

**Problem:** PromptLint ignores `.promptlintrc`.

**Solution:**
```bash
# Verify config file exists
ls -la .promptlintrc

# Check YAML syntax
python -c "import yaml; yaml.safe_load(open('.promptlintrc'))"

# Explicitly specify config
python -m promptlint.cli --config .promptlintrc --file prompt.txt
```

---

### "UnicodeEncodeError" on Windows

**Problem:** Terminal can't display special characters.

**Solution:**
```bash
# Use JSON output (no special characters)
python -m promptlint.cli --file prompt.txt --format json

# Or set UTF-8 encoding
chcp 65001
python -m promptlint.cli --file prompt.txt
```

---

## Performance Tips

### Large Files

For prompts > 10KB:
```bash
# Use --format json (faster rendering)
python -m promptlint.cli --file large_prompt.txt --format json

# Disable unnecessary rules
python -m promptlint.cli --file large_prompt.txt --config minimal.yaml
```

### Batch Processing

Process multiple files efficiently:
```bash
# Parallel processing (GNU parallel)
parallel python -m promptlint.cli --file {} --format json ::: prompts/*.txt

# Or with xargs
find prompts/ -name "*.txt" | xargs -P 4 -I {} python -m promptlint.cli --file {}
```

---

## Aliases

Create shortcuts for common commands:

```bash
# In ~/.bashrc or ~/.zshrc

# Quick lint
alias plint='python -m promptlint.cli'

# Lint with fix
alias pfix='python -m promptlint.cli --fix'

# JSON output
alias pjson='python -m promptlint.cli --format json'

# Dashboard
alias pdash='python -m promptlint.cli --show-dashboard'

# Strict mode
alias pstrict='python -m promptlint.cli --fail-level warn'
```

**Usage:**
```bash
plint --file prompt.txt
pfix --file prompt.txt
pdash --file prompt.txt
```

---

## Examples

### Example 1: Basic Lint

```bash
$ python -m promptlint.cli --text "Please write a function"

PromptLint Findings
[ INFO ] cost (line -) Prompt is ~5 tokens (~$0.0000 input per call on gpt-4o).
[ WARN ] structure-sections (line -) No explicit sections detected (Task/Context/Output).
[ WARN ] politeness-bloat (line 1) Consider removing 'Please' (adds 1.5 tokens without semantic value).
Please write a function
^
```

### Example 2: Auto-fix

```bash
$ python -m promptlint.cli --text "Please write a function" --fix

PromptLint Findings
(... findings ...)

Optimized Prompt
<task>Write a function</task>
```

### Example 3: Dashboard

```bash
$ python -m promptlint.cli --file demo/example_bad_prompt.txt --show-dashboard

PromptLint Findings
(... 20+ findings ...)

Savings Dashboard
Current Tokens: 97
Optimized Tokens: 59 (39.2% reduction)
Savings per Call: ~$0.0002
Monthly Savings: ~$57.00 at 10,000 calls/day
Annual Savings: ~$693.50
```

### Example 4: JSON for CI

```bash
$ python -m promptlint.cli --file prompt.txt --format json --fail-level warn
{
  "findings": [...],
  "dashboard": {...}
}
$ echo $?
1  # Failed due to WARN findings
```

---

## Next Steps

- **[Configuration Reference](configuration.md)** - Configure rules and behavior
- **[Rules Reference](rules-reference.md)** - Understand all rules
- **[Integrations](integrations.md)** - Set up CI/CD and pre-commit
- **[Best Practices](best-practices.md)** - Write better prompts
