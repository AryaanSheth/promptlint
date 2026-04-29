# `cost` — Token Count & Cost Analysis

**Severity:** INFO · **Auto-fix:** No · **Category:** 💰 Cost

## What It Does

Reports the prompt's token count and estimated cost per API call. This is always informational — it never causes a pipeline failure on its own.

## Example Output

```
[ INFO ] cost (line -)
  Prompt is ~97 tokens (~$0.0005 input per call on gpt-4o).
  At 10,000 calls/day → ~$4.85/day input.
```

## Cost Dashboard

Run with `--show-dashboard` for a full savings breakdown:

```bash
promptlint --file prompt.txt --show-dashboard
```

```
  Savings Dashboard
  ──────────────────────────────────────────────────
  Current Tokens:    97
  Optimized Tokens:  59  (39.2% reduction)

  Savings per Call:  ~$0.0002
  Daily Savings:     ~$2.00 at 10,000 calls/day
  Monthly Savings:   ~$60.00
  Annual Savings:    ~$720.00
```

## Configuration

```yaml
model: gpt-4o
cost_per_1k_tokens: 0.005
calls_per_day: 10000

rules:
  cost: true  # or false to disable
```

### Token Counting

The Python CLI uses `tiktoken` for exact counts when installed:

```bash
pip install "promptlint-cli[tiktoken]"
```

Without tiktoken (or in the Node.js CLI), tokens are estimated as `len(text) / 4` (±15%).

### Common Model Prices

| Model | Input per 1K tokens |
|-------|:-------------------:|
| GPT-4o | $0.005 |
| GPT-4o mini | $0.00015 |
| GPT-4 | $0.030 |
| GPT-3.5 Turbo | $0.0015 |
| Claude 3.5 Sonnet | $0.003 |
| Claude 3 Haiku | $0.00025 |
| Gemini 1.5 Pro | $0.00125 |

## Relationship to `cost-limit`

The `cost` rule is purely informational. If you want to **enforce** a token budget, use [`cost-limit`](/rules/cost-limit).
