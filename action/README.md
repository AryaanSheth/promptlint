# PromptLint GitHub Action

Lint LLM prompts in CI. Catches injection attacks, leaked API keys, PII, token waste, and quality issues — inline on the PR diff.

## Quick start

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: 'prompts/**/*.txt'
```

Add this to any workflow and PromptLint will scan your prompt files on every push, annotate the diff with findings, and fail the job if a CRITICAL issue (injection, leaked secret) is found.

## Inputs

| Input | Default | Description |
|---|---|---|
| `path` | `.` | File path or glob pattern to scan |
| `fail-level` | `critical` | Exit non-zero at: `none` \| `warn` \| `critical` |
| `config` | `` | Path to `.promptlintrc`. Auto-detects repo root config if blank. |
| `show-score` | `false` | Print A–F health score in the workflow log |
| `sarif-output` | `` | Write SARIF file to this path (upload separately with `codeql-action`) |
| `annotations` | `true` | Emit inline GitHub annotations on the PR diff |

## Outputs

| Output | Description |
|---|---|
| `findings-count` | Total findings across all scanned files |
| `critical-count` | CRITICAL severity findings |
| `score` | Health score 0–100 |
| `grade` | Health grade A–F |

## Usage examples

### Minimal — block merges with CRITICAL findings

```yaml
name: Lint Prompts
on: [pull_request]

jobs:
  promptlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AryaanSheth/promptlint@v1
        with:
          path: 'prompts/'
```

### Strict mode — block on any WARN or CRITICAL

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: 'prompts/'
    fail-level: warn
    show-score: true
```

### With SARIF upload (shows findings in the GitHub Security tab)

```yaml
permissions:
  contents: read
  security-events: write

steps:
  - uses: actions/checkout@v4

  - uses: AryaanSheth/promptlint@v1
    with:
      path: 'prompts/'
      sarif-output: promptlint.sarif

  - uses: github/codeql-action/upload-sarif@v3
    with:
      sarif_file: promptlint.sarif
    if: always()
```

### Full workflow with all options

```yaml
name: Lint Prompts

on:
  pull_request:
    paths:
      - 'prompts/**'
      - '**/*.prompt'
      - '**/*.txt'

jobs:
  promptlint:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      security-events: write

    steps:
      - uses: actions/checkout@v4

      - name: Run PromptLint
        id: lint
        uses: AryaanSheth/promptlint-action@v1
        with:
          path: 'prompts/'
          fail-level: critical
          show-score: true
          sarif-output: promptlint.sarif
          config: '.github/promptlintrc.yml'

      - name: Upload to Security tab
        uses: github/codeql-action/upload-sarif@v3
        with:
          sarif_file: promptlint.sarif
        if: always()

      - name: Print score
        run: echo "Score ${{ steps.lint.outputs.score }}/100 (${{ steps.lint.outputs.grade }})"
```

### Only run when prompt files change

```yaml
on:
  pull_request:
    paths:
      - 'prompts/**'
      - 'src/**/*.prompt'
```

## Configuration

PromptLint picks up a `.promptlintrc` from the repo root automatically. To generate one:

```bash
npx promptlint-cli --init
```

Example config to tune severity and disable specific rules:

```yaml
# .promptlintrc
model: gpt-4o
token_limit: 1000

rules:
  prompt_injection:
    enabled: true
  jailbreak_pattern:
    enabled: true
  pii_in_prompt:
    enabled: true
    check_email: true
    check_ssn: true
  secret_in_prompt:
    enabled: true
  role_clarity:
    enabled: true
    severity: warn        # downgrade from CRITICAL
  politeness_bloat:
    enabled: false        # disable entirely
```

## What gets flagged

| Rule | Severity | What it catches |
|---|---|---|
| `prompt-injection` | CRITICAL | `ignore previous instructions`, role-hijacking, obfuscated variants |
| `jailbreak-pattern` | CRITICAL | DAN prompts, "act as", "pretend you are" |
| `secret-in-prompt` | CRITICAL | API keys, tokens, passwords hardcoded in prompts |
| `pii-in-prompt` | CRITICAL | SSNs, credit cards, emails, phone numbers |
| `role-clarity` | WARN | Prompts with no system role definition |
| `output-format-missing` | WARN | No output format specified for instruction prompts |
| `hallucination-risk` | WARN | Asks model to recall facts without grounding |
| `clarity-vague-terms` | WARN | Vague language like "several", "some", "various" |
| `verbosity-redundancy` | INFO | Wordy phrases ("in order to" → "to") |
| `politeness-bloat` | WARN | Token-wasting filler ("please", "kindly", "thank you") |
| `cost` | INFO | Token count and estimated API cost |

## Annotations on the PR diff

Every finding appears inline on the changed lines. CRITICAL findings show as errors (red), WARN as warnings (yellow), INFO as notices.

## Security tab integration

When `sarif-output` is set and uploaded, findings appear in the **Security → Code scanning** tab of your repository, with filtering by rule, severity, and file.
