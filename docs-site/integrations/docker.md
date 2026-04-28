# Docker

Run PromptLint in a container for consistent environments across machines and pipelines.

## Quick Run

```bash
docker run --rm -v $(pwd):/workspace python:3.11-slim \
  sh -c "pip install -q promptlint-cli && promptlint --file /workspace/prompt.txt"
```

## Dockerfile

Build a dedicated image for faster pipeline runs:

```dockerfile
FROM python:3.11-slim

RUN pip install --no-cache-dir promptlint-cli

WORKDIR /workspace

ENTRYPOINT ["promptlint"]
```

Build and use:

```bash
docker build -t promptlint .
docker run --rm -v $(pwd):/workspace promptlint --file /workspace/prompt.txt
```

## Docker Compose

```yaml
# docker-compose.yml
services:
  promptlint:
    image: python:3.11-slim
    working_dir: /workspace
    volumes:
      - .:/workspace
    command: >
      sh -c "pip install -q promptlint-cli &&
             promptlint --file /workspace/prompts/*.txt --fail-level warn"
```

Run:

```bash
docker compose run --rm promptlint
```

## In GitHub Actions

```yaml
jobs:
  lint:
    runs-on: ubuntu-latest
    container:
      image: python:3.11-slim
    steps:
      - uses: actions/checkout@v4
      - run: pip install promptlint-cli
      - run: promptlint --file "prompts/**/*.txt" --fail-level warn
```

## Makefile Target

```makefile
lint-prompts-docker:
	docker run --rm \
	  -v $(PWD):/workspace \
	  python:3.11-slim \
	  sh -c "pip install -q promptlint-cli && promptlint --file /workspace/prompts/*.txt"

.PHONY: lint-prompts-docker
```
