# Integrations

Guide to integrating PromptLint with CI/CD, pre-commit hooks, and development workflows.

## Table of Contents

- [GitHub Actions](#github-actions)
- [GitLab CI](#gitlab-ci)
- [Pre-commit Hooks](#pre-commit-hooks)
- [VS Code Integration](#vs-code-integration)
- [Docker](#docker)
- [Make/Taskfile](#maketaskfile)
- [Custom Integrations](#custom-integrations)

---

## GitHub Actions

### Basic Workflow

`.github/workflows/promptlint.yml`:

```yaml
name: PromptLint

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-prompts:
    runs-on: ubuntu-latest
    
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -e ./cli
      
      - name: Run PromptLint
        run: |
          python -m promptlint.cli \
            --file prompts/system_prompt.txt \
            --fail-level warn \
            --format json \
            --show-dashboard
```

### Advanced: Lint All Prompts

```yaml
name: PromptLint - All Files

on: [push, pull_request]

jobs:
  lint-prompts:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install PromptLint
        run: |
          pip install -r requirements.txt
      
      - name: Find and lint all prompts
        run: |
          EXIT_CODE=0
          for file in $(find prompts/ -name "*.txt"); do
            echo "Linting $file..."
            python -m promptlint.cli --file "$file" --fail-level warn --format json || EXIT_CODE=$?
          done
          exit $EXIT_CODE
      
      - name: Upload results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: promptlint-results
          path: '**/*.json'
```

### With Cost Reporting

```yaml
name: PromptLint - Cost Report

on: [pull_request]

jobs:
  cost-analysis:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run cost analysis
        id: analysis
        run: |
          RESULT=$(python -m promptlint.cli \
            --file prompts/system_prompt.txt \
            --format json \
            --show-dashboard)
          
          TOKENS=$(echo $RESULT | jq '.dashboard.current_tokens')
          SAVINGS=$(echo $RESULT | jq '.dashboard.savings_per_call')
          
          echo "tokens=$TOKENS" >> $GITHUB_OUTPUT
          echo "savings=$SAVINGS" >> $GITHUB_OUTPUT
      
      - name: Comment on PR
        uses: actions/github-script@v6
        with:
          script: |
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: `## PromptLint Report
              
              **Current Tokens:** ${{ steps.analysis.outputs.tokens }}
              **Potential Savings:** $$${{ steps.analysis.outputs.savings }} per call
              
              Run \`--fix\` to optimize your prompts!`
            })
```

---

## GitLab CI

### Basic Pipeline

`.gitlab-ci.yml`:

```yaml
stages:
  - lint

promptlint:
  stage: lint
  image: python:3.9
  
  before_script:
    - pip install -r requirements.txt
  
  script:
    - python -m promptlint.cli --file prompts/system_prompt.txt --fail-level warn --format json
  
  only:
    - merge_requests
    - main
    - develop
```

### With Artifacts

```yaml
stages:
  - lint
  - report

promptlint:
  stage: lint
  image: python:3.9
  
  before_script:
    - pip install -r requirements.txt
  
  script:
    - |
      for file in prompts/*.txt; do
        python -m promptlint.cli \
          --file "$file" \
          --format json > "reports/$(basename $file .txt).json"
      done
  
  artifacts:
    paths:
      - reports/
    expire_in: 30 days
  
  only:
    - merge_requests
    - main

generate-report:
  stage: report
  image: python:3.9
  dependencies:
    - promptlint
  
  script:
    - python scripts/aggregate_results.py reports/ > summary.txt
  
  artifacts:
    paths:
      - summary.txt
```

---

## Pre-commit Hooks

### Local Git Hook

Create `.git/hooks/pre-commit`:

```bash
#!/bin/bash

echo "🔍 Running PromptLint..."

# Find staged prompt files
STAGED_PROMPTS=$(git diff --cached --name-only --diff-filter=ACM | grep -E 'prompts/.*\.txt$')

if [ -z "$STAGED_PROMPTS" ]; then
  echo "✅ No prompt files to lint"
  exit 0
fi

# Lint each file
EXIT_CODE=0
for file in $STAGED_PROMPTS; do
  echo "  Checking $file..."
  python -m promptlint.cli --file "$file" --fail-level warn
  
  if [ $? -ne 0 ]; then
    echo "❌ PromptLint failed for $file"
    EXIT_CODE=1
  fi
done

if [ $EXIT_CODE -eq 0 ]; then
  echo "✅ PromptLint passed!"
else
  echo "❌ PromptLint found issues. Fix them or use --no-verify to skip."
fi

exit $EXIT_CODE
```

Make executable:
```bash
chmod +x .git/hooks/pre-commit
```

### With Auto-fix Suggestion

```bash
#!/bin/bash

echo "🔍 Running PromptLint..."

STAGED_PROMPTS=$(git diff --cached --name-only --diff-filter=ACM | grep -E 'prompts/.*\.txt$')

if [ -z "$STAGED_PROMPTS" ]; then
  exit 0
fi

EXIT_CODE=0
for file in $STAGED_PROMPTS; do
  python -m promptlint.cli --file "$file" --fail-level warn
  
  if [ $? -ne 0 ]; then
    echo ""
    echo "💡 Tip: Run 'python -m promptlint.cli --file $file --fix' to auto-fix issues"
    EXIT_CODE=1
  fi
done

exit $EXIT_CODE
```

---

## VS Code Integration

### Task Configuration

Create `.vscode/tasks.json`:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "PromptLint: Current File",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "promptlint.cli",
        "--file",
        "${file}",
        "--show-dashboard"
      ],
      "group": {
        "kind": "test",
        "isDefault": true
      },
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "PromptLint: Auto-fix Current File",
      "type": "shell",
      "command": "python",
      "args": [
        "-m",
        "promptlint.cli",
        "--file",
        "${file}",
        "--fix"
      ],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    },
    {
      "label": "PromptLint: All Prompts",
      "type": "shell",
      "command": "bash",
      "args": [
        "-c",
        "for file in prompts/*.txt; do python -m promptlint.cli --file \"$file\"; done"
      ],
      "group": "test",
      "presentation": {
        "reveal": "always",
        "panel": "new"
      }
    }
  ]
}
```

**Usage:**
1. Open a prompt file
2. Press `Ctrl+Shift+P` (Cmd+Shift+P on Mac)
3. Type "Run Task"
4. Select "PromptLint: Current File"

### Keyboard Shortcut

Add to `.vscode/keybindings.json`:

```json
[
  {
    "key": "ctrl+shift+l",
    "command": "workbench.action.tasks.runTask",
    "args": "PromptLint: Current File"
  },
  {
    "key": "ctrl+shift+f",
    "command": "workbench.action.tasks.runTask",
    "args": "PromptLint: Auto-fix Current File"
  }
]
```

### Problem Matcher

For better error highlighting in VS Code:

```json
{
  "version": "2.0.0",
  "tasks": [
    {
      "label": "PromptLint",
      "type": "shell",
      "command": "python -m promptlint.cli --file ${file}",
      "problemMatcher": {
        "owner": "promptlint",
        "fileLocation": "relative",
        "pattern": {
          "regexp": "^\\[ (INFO|WARN|CRITICAL) \\] ([\\w-]+) \\(line (\\d+)\\) (.*)$",
          "severity": 1,
          "code": 2,
          "line": 3,
          "message": 4
        }
      }
    }
  ]
}
```

---

## Docker

### Dockerfile

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# Copy CLI package and install
COPY cli/ /app/cli/
WORKDIR /app/cli
RUN pip install --no-cache-dir -r requirements.txt && pip install -e .
WORKDIR /app
ENTRYPOINT ["python", "-m", "promptlint.cli"]
CMD ["--help"]
```

### Build and Run

```bash
# Build image
docker build -t promptlint:latest .

# Run on local file
docker run --rm -v $(pwd)/prompts:/prompts promptlint:latest \
  --file /prompts/system_prompt.txt

# Run with custom config
docker run --rm \
  -v $(pwd)/prompts:/prompts \
  -v $(pwd)/cli/.promptlintrc:/app/.promptlintrc \
  promptlint:latest \
  --file /prompts/system_prompt.txt \
  --show-dashboard
```

### Docker Compose

`docker-compose.yml`:

```yaml
version: '3.8'

services:
  promptlint:
    build: .
    volumes:
      - ./prompts:/prompts:ro
      - ./cli/.promptlintrc:/app/.promptlintrc:ro
    command: --file /prompts/system_prompt.txt --format json
```

**Usage:**
```bash
docker-compose run --rm promptlint
```

---

## Make/Taskfile

### Makefile

`Makefile`:

```makefile
.PHONY: lint lint-all fix dashboard help

# Lint single file
lint:
	@python -m promptlint.cli --file $(FILE)

# Lint all prompts
lint-all:
	@for file in prompts/*.txt; do \
		echo "Linting $$file..."; \
		python -m promptlint.cli --file "$$file" --fail-level warn; \
	done

# Auto-fix single file
fix:
	@python -m promptlint.cli --file $(FILE) --fix

# Show dashboard
dashboard:
	@python -m promptlint.cli --file $(FILE) --show-dashboard

# CI check (strict)
ci:
	@python -m promptlint.cli --file prompts/*.txt --fail-level warn --format json

help:
	@echo "PromptLint Makefile"
	@echo ""
	@echo "Usage:"
	@echo "  make lint FILE=prompts/system.txt    Lint single file"
	@echo "  make lint-all                        Lint all prompts"
	@echo "  make fix FILE=prompts/system.txt     Auto-fix single file"
	@echo "  make dashboard FILE=prompts/system.txt  Show cost dashboard"
	@echo "  make ci                              Run CI checks"
```

**Usage:**
```bash
make lint FILE=prompts/system_prompt.txt
make lint-all
make fix FILE=prompts/system_prompt.txt
make dashboard FILE=prompts/system_prompt.txt
```

### Taskfile

`Taskfile.yml`:

```yaml
version: '3'

tasks:
  lint:
    desc: Lint a prompt file
    cmds:
      - python -m promptlint.cli --file {{.FILE}}
    requires:
      vars: [FILE]

  lint-all:
    desc: Lint all prompt files
    cmds:
      - for: { var: PROMPTS, split: '\n' }
        cmd: python -m promptlint.cli --file {{.ITEM}}
    vars:
      PROMPTS:
        sh: find prompts/ -name "*.txt"

  fix:
    desc: Auto-fix a prompt file
    cmds:
      - python -m promptlint.cli --file {{.FILE}} --fix
    requires:
      vars: [FILE]

  dashboard:
    desc: Show cost dashboard
    cmds:
      - python -m promptlint.cli --file {{.FILE}} --show-dashboard
    requires:
      vars: [FILE]

  ci:
    desc: CI check (strict mode)
    cmds:
      - python -m promptlint.cli --file prompts/*.txt --fail-level warn --format json
```

**Usage:**
```bash
task lint FILE=prompts/system_prompt.txt
task lint-all
task fix FILE=prompts/system_prompt.txt
task dashboard FILE=prompts/system_prompt.txt
```

---

## Custom Integrations

### Python Script Integration

```python
#!/usr/bin/env python3
"""Custom PromptLint integration."""

import subprocess
import json
import sys

def lint_prompt(file_path: str) -> dict:
    """Run PromptLint on a file and return results."""
    result = subprocess.run(
        [
            'python', '-m', 'promptlint.cli',
            '--file', file_path,
            '--format', 'json'
        ],
        capture_output=True,
        text=True
    )
    
    return json.loads(result.stdout)

def main():
    # Lint a file
    results = lint_prompt('prompts/system_prompt.txt')
    
    # Check for critical issues
    critical_issues = [
        f for f in results['findings']
        if f['level'] == 'CRITICAL'
    ]
    
    if critical_issues:
        print(f"❌ Found {len(critical_issues)} critical issues!")
        for issue in critical_issues:
            print(f"  - {issue['rule']}: {issue['message']}")
        sys.exit(1)
    
    # Check token count
    tokens = results['dashboard']['current_tokens']
    if tokens > 1000:
        print(f"⚠️  Prompt is large: {tokens} tokens")
    
    print("✅ PromptLint checks passed!")

if __name__ == '__main__':
    main()
```

### Slack Notification

```python
#!/usr/bin/env python3
"""Send PromptLint results to Slack."""

import subprocess
import json
import requests
import os

SLACK_WEBHOOK = os.environ.get('SLACK_WEBHOOK_URL')

def lint_and_notify(file_path: str):
    """Lint file and send results to Slack."""
    result = subprocess.run(
        ['python', '-m', 'promptlint.cli', '--file', file_path, '--format', 'json'],
        capture_output=True,
        text=True
    )
    
    data = json.loads(result.stdout)
    dashboard = data['dashboard']
    
    # Build Slack message
    message = {
        "text": f"PromptLint Report: {file_path}",
        "blocks": [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"📊 PromptLint Report"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*File:*\n{file_path}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Tokens:*\n{dashboard['current_tokens']}"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Savings:*\n{dashboard['reduction_percentage']}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Issues:*\n{len(data['findings'])}"
                    }
                ]
            }
        ]
    }
    
    # Send to Slack
    response = requests.post(SLACK_WEBHOOK, json=message)
    if response.status_code == 200:
        print("✅ Notification sent to Slack")
    else:
        print(f"❌ Failed to send notification: {response.status_code}")

if __name__ == '__main__':
    lint_and_notify('prompts/system_prompt.txt')
```

---

## Analytics Dashboard

### Aggregate Results Script

`scripts/aggregate_results.py`:

```python
#!/usr/bin/env python3
"""Aggregate PromptLint results for analytics."""

import json
import sys
from pathlib import Path
from collections import Counter

def aggregate_results(reports_dir: str):
    """Aggregate JSON reports from multiple files."""
    reports_path = Path(reports_dir)
    all_findings = []
    total_tokens = 0
    total_savings = 0
    
    for report_file in reports_path.glob('*.json'):
        with open(report_file) as f:
            data = json.load(f)
            all_findings.extend(data['findings'])
            total_tokens += data['dashboard']['current_tokens']
            total_savings += data['dashboard'].get('tokens_saved', 0)
    
    # Statistics
    level_counts = Counter(f['level'] for f in all_findings)
    rule_counts = Counter(f['rule'] for f in all_findings)
    
    print("=" * 60)
    print("PromptLint Aggregate Report")
    print("=" * 60)
    print(f"\nTotal Files Analyzed: {len(list(reports_path.glob('*.json')))}")
    print(f"Total Tokens: {total_tokens:,}")
    print(f"Total Potential Savings: {total_savings:,} tokens")
    print(f"\nFindings by Level:")
    for level, count in level_counts.most_common():
        print(f"  {level:10s}: {count:3d}")
    print(f"\nTop Issues:")
    for rule, count in rule_counts.most_common(10):
        print(f"  {rule:30s}: {count:3d}")

if __name__ == '__main__':
    aggregate_results(sys.argv[1] if len(sys.argv) > 1 else 'reports/')
```

**Usage:**
```bash
python scripts/aggregate_results.py reports/
```

---

## Next Steps

- **[CLI Reference](cli-reference.md)** - Command-line options
- **[Configuration Reference](configuration.md)** - Configure behavior
- **[Best Practices](best-practices.md)** - Write better prompts
