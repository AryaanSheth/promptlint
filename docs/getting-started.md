# Getting Started with PromptLint

## What is PromptLint?

PromptLint is a comprehensive prompt quality analyzer that helps teams shipping AI features catch cost waste, quality issues, structural problems, and security risks before prompts hit production.

**Key Benefits:**
- 🔍 **15+ intelligent checks** covering cost, quality, security, and structure
- ⚡ **Auto-fix capabilities** for 5 common issues
- 💰 **Measurable savings** with detailed cost analytics
- 🛡️ **Security scanning** for injection attacks
- ⚙️ **Fully configurable** via `.promptlintrc`

## Quick Start (5 minutes)

### 1. Installation

```bash
# Clone the repository
git clone https://github.com/your-org/promptlint.git
cd promptlint

# Install the CLI (from repo root)
pip install -e ./cli
# Or from inside cli/: pip install -r requirements.txt  or  pip install -e .
```

### 2. Run Your First Lint

```bash
# Analyze a prompt file (paths relative to current directory)
python -m promptlint.cli --file cli/demo/example_bad_prompt.txt

# Analyze inline text
python -m promptlint.cli --text "Please write me a function"

# With auto-fix
python -m promptlint.cli --text "Please write me a function" --fix

# With savings dashboard
python -m promptlint.cli --file demo/example_bad_prompt.txt --show-dashboard
```

### 3. Basic Example

**Input Prompt:**
```
Please kindly write some code that does various things with several functions.
```

**PromptLint Output:**
```
PromptLint Findings
[ WARN ] structure-sections (line -) No explicit sections detected (Task/Context/Output).
[ WARN ] clarity-vague-terms (line 1) Vague term 'some' detected. Be more specific.
[ WARN ] politeness-bloat (line 1) Consider removing 'Please' (adds 1.5 tokens without semantic value).
```

**Auto-Fix Output (`--fix`):**
```
<task>Write code that does various things with several functions.</task>
```

## Understanding the Output

### Finding Levels

PromptLint uses three severity levels:

| Level | Icon | Meaning | Example |
|-------|------|---------|---------|
| **INFO** | `[ INFO ]` | Suggestions for improvement | "Consider adding examples" |
| **WARN** | `[ WARN ]` | Issues that should be fixed | "Vague term 'some' detected" |
| **CRITICAL** | `[ CRITICAL ]` | Security risks or hard limits | "Injection pattern detected" |

### Finding Format

```
[ LEVEL ] rule-name (line N) Message text
Context line with issue
                    ^
```

- **LEVEL**: Severity (INFO, WARN, CRITICAL)
- **rule-name**: Which rule triggered (e.g., `politeness-bloat`, `cost-limit`)
- **line N**: Line number in your prompt (or `-` for file-level issues)
- **Message**: What's wrong and how to fix it
- **Caret (`^`)**: Points to the exact location of the issue

## Output Modes

### 1. Text Output (Default)

Human-readable terminal output with colors and formatting.

```bash
python -m promptlint.cli --file prompt.txt
```

### 2. JSON Output

Machine-readable format for CI/CD pipelines and tools.

```bash
python -m promptlint.cli --file prompt.txt --format json
```

**JSON Structure:**
```json
{
  "findings": [
    {
      "level": "WARN",
      "rule": "politeness-bloat",
      "message": "Consider removing 'Please'...",
      "line": 1,
      "context": "Please write...\n^"
    }
  ],
  "optimized_prompt": "<task>Write...</task>",
  "dashboard": {
    "current_tokens": 97,
    "optimized_tokens": 59,
    "tokens_saved": 38,
    "reduction_percentage": 39.2,
    "savings_per_call": 0.00019
  }
}
```

### 3. Fix Mode

Applies automatic fixes and outputs the optimized prompt.

```bash
python -m promptlint.cli --file prompt.txt --fix
```

**What gets fixed:**
- Removes politeness bloat (`please`, `thank you`, etc.)
- Simplifies redundant phrases (`in order to` → `to`)
- Removes injection attempts
- Adds missing structure tags
- Normalizes spacing and punctuation

## Configuration

PromptLint is configured via a `.promptlintrc` file in YAML format.

### Minimal Configuration

```yaml
# .promptlintrc
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
```

### Full Configuration

See [Configuration Reference](configuration.md) for all options.

## Common Use Cases

### 1. Pre-Commit Hook

Catch issues before they reach your repo:

```bash
# In your pre-commit hook
python -m promptlint.cli --file prompts/system.txt --fail-level warn
```

### 2. CI/CD Pipeline

```bash
# GitHub Actions, GitLab CI, etc.
python -m promptlint.cli --file prompts/*.txt --format json --fail-level critical
```

### 3. Cost Analysis

See potential savings across your prompts:

```bash
python -m promptlint.cli --file prompt.txt --show-dashboard
```

**Dashboard Output:**
```
Savings Dashboard
Current Tokens: 97
Optimized Tokens: 59 (39.2% reduction)
Savings per Call: ~$0.0002
Monthly Savings: ~$57.00 at 10,000 calls/day
Annual Savings: ~$693.50
```

## Exit Codes

Control CI/CD behavior with fail levels:

| Flag | Behavior | Use Case |
|------|----------|----------|
| `--fail-level none` | Always exit 0 | Advisory only |
| `--fail-level warn` | Exit 1 on WARN or CRITICAL | Strict quality |
| `--fail-level critical` | Exit 2 on CRITICAL only | Security only (default) |

**Example:**
```bash
# Fail only on security issues (injection)
python -m promptlint.cli --file prompt.txt --fail-level critical

# Fail on any quality issue
python -m promptlint.cli --file prompt.txt --fail-level warn
```

## Next Steps

- **[Configuration Reference](configuration.md)** - Complete `.promptlintrc` guide
- **[Rules Reference](rules-reference.md)** - Detailed explanation of all 15+ rules
- **[CLI Reference](cli-reference.md)** - All command-line options
- **[Integrations](integrations.md)** - CI/CD, pre-commit, and IDE setup
- **[Best Practices](best-practices.md)** - How to write great prompts

## Need Help?

- **Documentation**: See `docs/` folder
- **Examples**: Check `demo/` folder
- **Issues**: Open an issue on GitHub
- **Config problems**: Run with `--config path/to/.promptlintrc` to test
