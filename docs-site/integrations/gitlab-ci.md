# GitLab CI

Integrate PromptLint into GitLab CI/CD pipelines.

## Basic Setup

```yaml
# .gitlab-ci.yml
lint-prompts:
  image: python:3.11-slim
  stage: test
  script:
    - pip install promptlint-cli
    - promptlint --file "prompts/**/*.txt" --fail-level warn
  rules:
    - changes:
        - prompts/**/*
        - .promptlintrc
```

## With JSON Report

```yaml
lint-prompts:
  image: python:3.11-slim
  stage: test
  script:
    - pip install promptlint-cli
    - promptlint --file "prompts/**/*.txt" --format json --fail-level warn | tee promptlint-report.json
  artifacts:
    paths:
      - promptlint-report.json
    expire_in: 1 week
    when: always
```

## SARIF Report

GitLab supports SARIF for security scanning:

```yaml
lint-prompts:
  image: python:3.11-slim
  stage: test
  script:
    - pip install promptlint-cli
    - promptlint --file "prompts/**/*.txt" --format sarif > promptlint.sarif || true
    - promptlint --file "prompts/**/*.txt" --fail-level warn
  artifacts:
    reports:
      sast: promptlint.sarif
```

## Caching pip

```yaml
lint-prompts:
  image: python:3.11-slim
  stage: test
  cache:
    paths:
      - .cache/pip
  variables:
    PIP_CACHE_DIR: "$CI_PROJECT_DIR/.cache/pip"
  script:
    - pip install promptlint-cli
    - promptlint --file "prompts/**/*.txt" --fail-level warn
```

## Node.js Pipeline

```yaml
lint-prompts:
  image: node:20-alpine
  stage: test
  script:
    - npm install -g promptlint-cli
    - promptlint --file "prompts/**/*.txt" --fail-level warn
```
