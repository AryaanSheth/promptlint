# Integrations

Guide to integrating PromptLint with CI/CD, pre-commit hooks, and development workflows.

## Table of Contents

- [GitHub Actions (first-party)](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Pre-commit Hooks](#pre-commit-hooks)
- [VS Code](#vs-code)
- [Docker](#docker)
- [Make / Taskfile](#maketaskfile)
- [Custom Scripts](#custom-scripts)

---

## GitHub Actions

PromptLint is published on the [GitHub Marketplace](https://github.com/marketplace/actions/promptlint-action) as a first-party action. No Python or Node.js setup required.

### Minimal — scan files, block merges on CRITICAL findings

```yaml
# .github/workflows/promptlint.yml
name: Lint Prompts
on: [pull_request]

jobs:
  promptlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: AryaanSheth/promptlint@v1
        with:
          path: 'prompts/**/*.txt'
```

Fails the job when any CRITICAL finding is detected (injection, leaked secrets, PII). Inline annotations appear on the PR diff automatically.

### Inline prompt string — lint text directly

Use the `prompt` input to lint a string instead of files. No `actions/checkout` step required when linting strings stored in secrets or env vars.

```yaml
name: Lint System Prompt
on: [push]

jobs:
  promptlint:
    runs-on: ubuntu-latest
    steps:
      - uses: AryaanSheth/promptlint@v1
        with:
          prompt: 'You are a helpful assistant. Always be concise.'
          fail-level: critical
          show-score: true
```

Lint a prompt stored in a GitHub secret:

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    prompt: ${{ secrets.SYSTEM_PROMPT }}
    fail-level: warn
```

> **Note:** When `prompt` is set, the `path` input is ignored.

### Strict mode — fail on WARN or CRITICAL

```yaml
- uses: AryaanSheth/promptlint@v1
  with:
    path: 'prompts/'
    fail-level: warn
    show-score: true
```

### With SARIF upload — findings in the Security tab

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
      fail-level: critical

  - uses: github/codeql-action/upload-sarif@v3
    with:
      sarif_file: promptlint.sarif
    if: always()
```

### Full workflow — all options, score comment

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
        uses: AryaanSheth/promptlint@v1
        with:
          path: 'prompts/'
          fail-level: critical
          show-score: true
          sarif-output: promptlint.sarif
          config: '.github/promptlintrc.yml'

      - uses: github/codeql-action/upload-sarif@v3
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
      - '**/*.txt'
```

### Action inputs

| Input | Default | Description |
|---|---|---|
| `path` | `.` | File path or glob pattern to scan. Ignored when `prompt` is set. |
| `prompt` | `` | Inline prompt text to lint. When set, `path` is ignored. |
| `fail-level` | `critical` | Exit non-zero on: `none` \| `warn` \| `critical` |
| `config` | `` | Path to `.promptlintrc`. Auto-detects repo root if blank. |
| `show-score` | `false` | Print A–F health score in the workflow log |
| `sarif-output` | `` | Write SARIF v2.1.0 for the GitHub Security tab |
| `annotations` | `true` | Emit inline annotations on the PR diff |

### Action outputs

| Output | Description |
|---|---|
| `findings-count` | Total findings across all scanned files |
| `critical-count` | CRITICAL severity findings |
| `score` | Health score 0–100 |
| `grade` | Health grade A–F |

---

## GitLab CI

### Basic pipeline

`.gitlab-ci.yml`:

```yaml
stages:
  - lint

promptlint:
  stage: lint
  image: node:20-slim
  script:
    - npx promptlint-cli prompts/**/*.txt --fail-level critical --format json
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

### With artifacts and Python

```yaml
stages:
  - lint

promptlint:
  stage: lint
  image: python:3.11-slim
  before_script:
    - pip install promptlint-cli
  script:
    - |
      for file in prompts/*.txt; do
        promptlint --file "$file" --fail-level warn --format json \
          > "reports/$(basename $file .txt).json"
      done
  artifacts:
    paths:
      - reports/
    expire_in: 30 days
  rules:
    - if: '$CI_PIPELINE_SOURCE == "merge_request_event"'
    - if: '$CI_COMMIT_BRANCH == "main"'
```

---

## Pre-commit Hooks

### Using pre-commit framework

`.pre-commit-config.yaml`:

```yaml
repos:
  - repo: local
    hooks:
      - id: promptlint
        name: PromptLint
        language: system
        entry: promptlint
        args: [--fail-level, warn]
        files: \.(txt|prompt|md)$
        pass_filenames: true
```

Install and enable:

```bash
pip install pre-commit promptlint-cli
pre-commit install
```

### Manual git hook

`.git/hooks/pre-commit`:

```bash
#!/bin/bash

STAGED_PROMPTS=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\.(txt|prompt)$')

if [ -z "$STAGED_PROMPTS" ]; then
  exit 0
fi

echo "Running PromptLint..."
EXIT_CODE=0

for file in $STAGED_PROMPTS; do
  promptlint --file "$file" --fail-level warn || EXIT_CODE=$?
  if [ $EXIT_CODE -ne 0 ]; then
    echo "Tip: run 'promptlint --file $file --fix' to auto-fix"
  fi
done

exit $EXIT_CODE
```

```bash
chmod +x .git/hooks/pre-commit
```

---

## VS Code

Install the [PromptLint VS Code extension](https://marketplace.visualstudio.com/items?itemName=PromptLint.promptlint-vscode) for real-time inline linting as you write prompts — no terminal needed.

### Tasks (without extension)

`.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "PromptLint: Current File",
      "type": "shell",
      "command": "promptlint",
      "args": ["--file", "${file}", "--show-dashboard"],
      "group": { "kind": "test", "isDefault": true },
      "presentation": { "reveal": "always", "panel": "new" }
    },
    {
      "label": "PromptLint: Auto-fix Current File",
      "type": "shell",
      "command": "promptlint",
      "args": ["--file", "${file}", "--fix"],
      "group": "test",
      "presentation": { "reveal": "always", "panel": "new" }
    },
    {
      "label": "PromptLint: All Prompts",
      "type": "shell",
      "command": "promptlint",
      "args": ["prompts/**/*.txt"],
      "group": "test",
      "presentation": { "reveal": "always", "panel": "new" }
    }
  ]
}
```

Run with `Ctrl+Shift+P` → "Run Task" → select task.

### Keyboard shortcuts

`.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+l",
    "command": "workbench.action.tasks.runTask",
    "args": "PromptLint: Current File"
  },
  {
    "key": "ctrl+shift+alt+f",
    "command": "workbench.action.tasks.runTask",
    "args": "PromptLint: Auto-fix Current File"
  }
]
```

---

## Docker

### Simple one-shot scan

```bash
docker run --rm \
  -v "$(pwd)/prompts:/prompts:ro" \
  node:20-slim \
  sh -c "npx promptlint-cli /prompts/**/*.txt --fail-level critical"
```

### Dockerfile (for custom images)

```dockerfile
FROM python:3.11-slim
RUN pip install --no-cache-dir promptlint-cli
ENTRYPOINT ["promptlint"]
CMD ["--help"]
```

```bash
docker build -t promptlint .

# Scan a directory
docker run --rm -v "$(pwd)/prompts:/prompts:ro" promptlint \
  /prompts/system_prompt.txt --fail-level warn

# With config
docker run --rm \
  -v "$(pwd)/prompts:/prompts:ro" \
  -v "$(pwd)/.promptlintrc:/.promptlintrc:ro" \
  promptlint /prompts/system_prompt.txt
```

### Docker Compose

`docker-compose.yml`:

```yaml
services:
  promptlint:
    image: python:3.11-slim
    volumes:
      - ./prompts:/prompts:ro
      - ./.promptlintrc:/.promptlintrc:ro
    command: >
      sh -c "pip install -q promptlint-cli &&
             promptlint /prompts/system_prompt.txt --format json"
```

```bash
docker compose run --rm promptlint
```

---

## Make/Taskfile

### Makefile

```makefile
.PHONY: lint lint-all fix ci

lint:
	promptlint --file $(FILE)

lint-all:
	promptlint prompts/**/*.txt

fix:
	promptlint --file $(FILE) --fix

ci:
	promptlint prompts/**/*.txt --fail-level critical --quiet

help:
	@echo "Usage:"
	@echo "  make lint FILE=prompts/system.txt"
	@echo "  make lint-all"
	@echo "  make fix  FILE=prompts/system.txt"
	@echo "  make ci"
```

```bash
make lint FILE=prompts/system_prompt.txt
make lint-all
make ci
```

### Taskfile

`Taskfile.yml`:

```yaml
version: '3'

tasks:
  lint:
    desc: Lint a single prompt file
    cmds:
      - promptlint --file {{.FILE}}
    requires:
      vars: [FILE]

  lint-all:
    desc: Lint all prompt files
    cmds:
      - promptlint prompts/**/*.txt

  fix:
    desc: Auto-fix a prompt file
    cmds:
      - promptlint --file {{.FILE}} --fix
    requires:
      vars: [FILE]

  ci:
    desc: CI check (block on CRITICAL)
    cmds:
      - promptlint prompts/**/*.txt --fail-level critical --quiet
```

```bash
task lint FILE=prompts/system_prompt.txt
task lint-all
task ci
```

---

## Custom Scripts

### Python — library API

```python
from promptlint import analyze, applyFixes, loadConfig

config = loadConfig()   # reads .promptlintrc
findings = analyze("Please kindly write some code", config)

critical = [f for f in findings if f["level"] == "CRITICAL"]
if critical:
    raise RuntimeError(f"{len(critical)} critical issue(s) found")

fixed = applyFixes("Please kindly write some code", config)
print(fixed)
```

### Node.js / TypeScript — library API

```typescript
import { analyze, applyFixes, computeScore, loadConfig } from "promptlint-cli";

const config = loadConfig();
const text = "Please kindly write some code";

const findings = analyze(text, config);
const score = computeScore(findings);

console.log(`Grade: ${score.grade} (${score.overall}/100)`);

const critical = findings.filter(f => f.level === "CRITICAL");
if (critical.length > 0) {
  process.exit(2);
}

const fixed = applyFixes(text, config);
```

### GitHub Actions — use outputs in downstream steps

```yaml
- name: Run PromptLint
  id: lint
  uses: AryaanSheth/promptlint@v1
  with:
    path: 'prompts/'
    fail-level: none   # capture outputs without failing

- name: Post PR comment with score
  if: github.event_name == 'pull_request'
  uses: actions/github-script@v7
  with:
    script: |
      const score = '${{ steps.lint.outputs.score }}';
      const grade = '${{ steps.lint.outputs.grade }}';
      const critical = '${{ steps.lint.outputs.critical-count }}';
      github.rest.issues.createComment({
        issue_number: context.issue.number,
        owner: context.repo.owner,
        repo: context.repo.repo,
        body: `## PromptLint Score: ${score}/100 (${grade})\n\n${critical} critical finding(s).`
      });
```

### Slack notification

```python
import subprocess, json, os, requests

def lint_and_notify(path: str):
    result = subprocess.run(
        ["promptlint", "--file", path, "--format", "json"],
        capture_output=True, text=True
    )
    data = json.loads(result.stdout)
    critical = sum(1 for f in data["findings"] if f["level"] == "CRITICAL")

    requests.post(os.environ["SLACK_WEBHOOK_URL"], json={
        "text": f"PromptLint: {path} — {critical} critical finding(s), "
                f"{len(data['findings'])} total"
    })
```

---

## Next Steps

- [CLI Reference](cli-reference.md) — all command-line options
- [Configuration Reference](configuration.md) — `.promptlintrc` guide
- [Rules Reference](rules-reference.md) — every rule explained
- [Best Practices](best-practices.md) — writing production-ready prompts
