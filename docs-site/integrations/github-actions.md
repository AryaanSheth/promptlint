# GitHub Actions

PromptLint has a dedicated GitHub Action on the Marketplace: `AryaanSheth/promptlint@v1`.

## Basic Usage

```yaml
# .github/workflows/lint-prompts.yml
name: Lint Prompts

on: [push, pull_request]

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AryaanSheth/promptlint@v1
        with:
          path: prompts/
```

## Inputs

| Input | Default | Description |
|-------|---------|-------------|
| `path` | `prompts/` | Directory or glob to scan |
| `prompt` | — | Inline prompt text (alternative to `path`) |
| `fail-level` | `critical` | Minimum severity for failure: `critical`, `warn`, `info`, `none` |
| `config` | `.promptlintrc` | Config file path |
| `show-score` | `false` | Display score/grade in workflow summary |
| `sarif-output` | `false` | Upload SARIF to GitHub Security tab |
| `annotations` | `true` | Add inline PR annotations for findings |

## Outputs

| Output | Description |
|--------|-------------|
| `findings-count` | Total number of findings |
| `critical-count` | Number of CRITICAL findings |
| `score` | Prompt quality score (0–100) |
| `grade` | Letter grade (A–F) |

## Common Configurations

### Strict — fail on warnings

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
    fail-level: warn
    show-score: true
```

### Security scan with SARIF upload

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
    fail-level: critical
    sarif-output: true
```

This uploads findings to the **Security** → **Code scanning** tab.

### Use score in downstream steps

```yaml
- uses: AryaanSheth/promptlint@v1
  id: promptlint
  with:
    path: prompts/

- name: Comment score on PR
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      github.rest.issues.createComment({
        ...context.repo,
        issue_number: context.issue.number,
        body: `PromptLint score: **${{ steps.promptlint.outputs.score }}/100** (${{ steps.promptlint.outputs.grade }})`
      })
```

### Custom config per environment

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: prompts/
    config: .promptlintrc.ci      # stricter config for CI
    fail-level: warn
```

### Scan inline prompt

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    prompt: |
      You are a helpful assistant.
      Answer questions about our product.
    fail-level: warn
```

## Full Workflow Example

```yaml
name: Prompt Quality Gate

on:
  pull_request:
    paths:
      - 'prompts/**'
      - '.promptlintrc'

jobs:
  lint:
    runs-on: ubuntu-latest
    permissions:
      security-events: write
      pull-requests: write

    steps:
      - uses: actions/checkout@v4

      - name: Lint prompts
        uses: AryaanSheth/promptlint@v1
        id: lint
        with:
          path: prompts/
          fail-level: warn
          sarif-output: true
          show-score: true
          annotations: true

      - name: PR comment
        if: always() && github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const score = '${{ steps.lint.outputs.score }}';
            const grade = '${{ steps.lint.outputs.grade }}';
            const count = '${{ steps.lint.outputs.findings-count }}';
            const critical = '${{ steps.lint.outputs.critical-count }}';
            const emoji = grade === 'A' ? '✅' : grade <= 'C' ? '⚠️' : '❌';
            github.rest.issues.createComment({
              ...context.repo,
              issue_number: context.issue.number,
              body: `${emoji} **PromptLint**: ${score}/100 (${grade}) · ${count} findings (${critical} critical)`
            });
```
