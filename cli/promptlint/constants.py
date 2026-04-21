from __future__ import annotations

# Hard limit for file and stdin reads — prevents OOM on huge inputs
MAX_INPUT_BYTES: int = 10 * 1024 * 1024

# Above this call volume, daily/monthly financial projections are suppressed
CALLS_PER_DAY_DISPLAY_LIMIT: int = 100_000

# Category weights used by compute_score() — must sum to 1.0
SCORE_WEIGHTS: dict[str, float] = {
    "security": 0.40,
    "cost": 0.20,
    "quality": 0.25,
    "completeness": 0.15,
}
