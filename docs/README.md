# PromptLint Documentation

Comprehensive technical documentation for PromptLint - a powerful prompt quality analyzer for teams shipping AI features.

## Quick Links

| Document | Description |
|----------|-------------|
| **[Getting Started](getting-started.md)** | Quick start guide, installation, and basic usage (5 minutes) |
| **[Configuration Reference](configuration.md)** | Complete `.promptlintrc` configuration guide with all options |
| **[Rules Reference](rules-reference.md)** | Detailed explanation of all 15+ rules with examples |
| **[CLI Reference](cli-reference.md)** | Command-line interface reference and all options |
| **[Integrations](integrations.md)** | CI/CD, pre-commit hooks, VS Code, and Docker setup |
| **[Best Practices](best-practices.md)** | How to write high-quality, cost-effective prompts |

---

## Documentation Overview

### For New Users

Start here if you're new to PromptLint:

1. **[Getting Started](getting-started.md)** - Install and run your first lint
2. **[Best Practices](best-practices.md)** - Learn prompt writing fundamentals
3. **[Rules Reference](rules-reference.md)** - Understand what each rule checks

### For Configuration

Customize PromptLint for your team:

1. **[Configuration Reference](configuration.md)** - Complete `.promptlintrc` guide
2. **[Rules Reference](rules-reference.md)** - Details on each rule's behavior

### For Integration

Set up PromptLint in your workflow:

1. **[CLI Reference](cli-reference.md)** - Command-line usage
2. **[Integrations](integrations.md)** - CI/CD, pre-commit, Docker, etc.

---

## What is PromptLint?

PromptLint is a comprehensive prompt quality analyzer that detects:

- 💰 **Cost waste** - Token bloat and redundancies
- ✨ **Quality issues** - Vague terms, unclear requirements
- 🔒 **Security risks** - Injection attacks
- 🏗️ **Structural problems** - Missing organization

With **15+ intelligent checks** and **5 auto-fix capabilities**, PromptLint ensures your prompts are clear, efficient, and production-ready.

---

## Key Features

| Feature | Description |
|---------|-------------|
| **15+ Rules** | Comprehensive checks covering cost, quality, security, and structure |
| **Auto-Fix** | Automatically optimize 5 common issues (politeness, redundancy, injection, etc.) |
| **Cost Analytics** | Token counting, cost projection, and savings dashboard |
| **Security** | Injection pattern detection with CRITICAL-level alerts |
| **Configurable** | Fully customizable via `.promptlintrc` YAML file |
| **CI/CD Ready** | JSON output, exit codes, and integration examples |

---

## Quick Start

```bash
# Install the CLI from the cli/ package (run from repo root)
pip install -e ./cli

# Lint a prompt
python -m promptlint.cli --file prompt.txt

# Auto-fix issues
python -m promptlint.cli --file prompt.txt --fix

# Show cost dashboard
python -m promptlint.cli --file prompt.txt --show-dashboard
```

See [Getting Started](getting-started.md) for detailed instructions.

---

## Documentation Structure

### [Getting Started](getting-started.md)
- Installation
- Basic usage
- Output modes (text, JSON, fix)
- Exit codes
- Common use cases

### [Configuration Reference](configuration.md)
- Global settings (model, token_limit, costs)
- Display options
- All 15+ rule configurations
- Auto-fix settings
- Team presets (security-first, cost-first, quality-first)
- Troubleshooting

### [Rules Reference](rules-reference.md)
- Detailed explanation of each rule
- Examples (bad vs good)
- Why it matters
- Configuration options
- Auto-fix behavior

**Rule categories:**
- Cost & Tokens (2 rules)
- Security (1 rule)
- Structure (1 rule)
- Clarity (1 rule, 4 sub-checks)
- Specificity (2 rules)
- Verbosity (3 rules)
- Actionability (1 rule)
- Consistency (1 rule)
- Completeness (1 rule)

### [CLI Reference](cli-reference.md)
- All command-line options
- Input modes (--file, --text)
- Output formats (--format text/json)
- Auto-fix (--fix)
- Exit codes (--fail-level)
- Advanced usage (piping, JSON processing with jq)
- Batch processing
- Troubleshooting

### [Integrations](integrations.md)
- **CI/CD:** GitHub Actions, GitLab CI
- **Pre-commit hooks:** Local git hooks
- **VS Code:** Tasks, keyboard shortcuts, problem matchers
- **Docker:** Dockerfile, docker-compose
- **Make/Taskfile:** Build automation
- **Custom integrations:** Python scripts, Slack notifications
- **Analytics:** Aggregating results across multiple files

### [Best Practices](best-practices.md)
- Prompt structure (XML, Markdown, headings)
- Clarity & specificity (avoid vague language)
- Token optimization (remove bloat, simplify redundancies)
- Security considerations (injection prevention)
- Maintainability (versioning, configuration)
- Testing & iteration (A/B testing, metrics)
- Complete examples (before/after)
- Quick checklist for production-ready prompts

---

## Examples

### Example 1: Basic Lint

```bash
$ python -m promptlint.cli --text "Please write a function"

PromptLint Findings
[ WARN ] structure-sections (line -) No explicit sections detected.
[ WARN ] politeness-bloat (line 1) Consider removing 'Please'...
```

### Example 2: Auto-Fix

```bash
$ python -m promptlint.cli --text "Please write a function" --fix

Optimized Prompt
<task>Write a function</task>
```

### Example 3: Cost Dashboard

```bash
$ python -m promptlint.cli --file prompt.txt --show-dashboard

Savings Dashboard
Current Tokens: 97
Optimized Tokens: 59 (39.2% reduction)
Savings per Call: ~$0.0002
Monthly Savings: ~$57.00 at 10,000 calls/day
```

---

## Configuration Quick Reference

```yaml
# .promptlintrc
model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000
structure_style: xml

rules:
  cost: true
  cost_limit: true
  prompt_injection: true
  structure_sections: true
  clarity_vague_terms: true
  specificity_examples: true
  specificity_constraints: true
  politeness_bloat:
    enabled: true
    allow_politeness: false  # WARN level
  verbosity_redundancy: true
  verbosity_sentence_length: true
  actionability_weak_verbs: true
  consistency_terminology: true
  completeness_edge_cases: true

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
```

See [Configuration Reference](configuration.md) for all options.

---

## Rules Quick Reference

| Rule | Level | Auto-Fix | Description |
|------|-------|----------|-------------|
| `cost` | INFO | No | Token count & cost per call |
| `cost-limit` | CRITICAL | No | Token limit enforcement |
| `prompt-injection` | CRITICAL | Yes | Injection pattern detection |
| `structure-sections` | WARN | Yes | Prompt organization check |
| `clarity-vague-terms` | WARN | No | Vague/ambiguous language |
| `specificity-examples` | INFO | No | Suggests adding examples |
| `specificity-constraints` | INFO | No | Suggests adding constraints |
| `politeness-bloat` | WARN/INFO | Yes | Unnecessary politeness |
| `verbosity-redundancy` | INFO | Yes | Redundant phrases |
| `verbosity-sentence-length` | INFO | No | Long sentence detection |
| `actionability-weak-verbs` | INFO | No | Passive voice detection |
| `consistency-terminology` | INFO | No | Mixed terminology |
| `completeness-edge-cases` | INFO | No | Edge case reminders |

See [Rules Reference](rules-reference.md) for details.

---

## Common Workflows

### Development Workflow
```bash
# 1. Write prompt
vim prompts/my_prompt.txt

# 2. Lint
python -m promptlint.cli --file prompts/my_prompt.txt

# 3. Auto-fix
python -m promptlint.cli --file prompts/my_prompt.txt --fix

# 4. Final check
python -m promptlint.cli --file prompts/my_prompt.txt --fail-level warn
```

### CI/CD Workflow
```bash
# Strict mode in CI
python -m promptlint.cli --file prompts/*.txt --fail-level warn --format json
```

### Cost Analysis Workflow
```bash
# Show savings dashboard
python -m promptlint.cli --file prompts/*.txt --show-dashboard
```

---

## Support & Contributing

- **Issues:** Report bugs or request features on GitHub
- **Discussions:** Ask questions in GitHub Discussions
- **Contributing:** See CONTRIBUTING.md for guidelines
- **Documentation:** Help improve docs via pull requests

---

## Version History

- **v0.2.0** - Structure flexibility, politeness configuration, improved auto-fix
- **v0.1.0** - Initial release with 15+ rules and 5 auto-fixes

---

## License

MIT License - See LICENSE file for details.

---

## Next Steps

Choose your path:

- **New to PromptLint?** → [Getting Started](getting-started.md)
- **Want to configure?** → [Configuration Reference](configuration.md)
- **Need rule details?** → [Rules Reference](rules-reference.md)
- **Setting up CI/CD?** → [Integrations](integrations.md)
- **Writing prompts?** → [Best Practices](best-practices.md)
