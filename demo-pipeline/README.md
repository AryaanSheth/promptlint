# PromptLint Demo Pipeline

A chatbot-style UI that demos promptlint: chat with PromptLint and it automatically analyzes and optimizes your prompts.

## Run

```bash
# From repo root
cd /path/to/promptlint
pip install -e cli
pip install flask
python demo-pipeline/app.py
```

Open http://localhost:5051

## Flow

1. Type or paste a prompt (or click a suggested example)
2. Hit Enter or Send — PromptLint analyzes and auto-fixes automatically
3. See the fix log and optimized prompt in the response
