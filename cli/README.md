# PromptLint CLI

Command-line tool for linting prompts: cost, quality, and security (e.g. injection detection).

## Install

From this directory:

```bash
pip install -r requirements.txt
# or editable install
pip install -e .
```

From repo root:

```bash
pip install -e ./cli
```

## Run

```bash
# From cli/ (uses cli/.promptlintrc)
python -m promptlint.cli --file path/to/prompt.txt

# With options
python -m promptlint.cli --file prompt.txt --format json --fail-level warn --show-dashboard
python -m promptlint.cli --file prompt.txt --fix
```

If installed as a console script:

```bash
promptlint --file path/to/prompt.txt
```

## Config

- `.promptlintrc` in this directory (or pass `--config path/to/.promptlintrc`).
- See [../docs/configuration.md](../docs/configuration.md) for full options.

## Demo

```bash
python -m promptlint.cli --file demo/example_bad_prompt.txt --show-dashboard
python -m promptlint.cli --file demo/example_good_prompt.txt
```
