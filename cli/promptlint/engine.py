from typing import Dict, List

from .constants import SCORE_WEIGHTS
from .rules.cost import check_tokens
from .rules.quality import (
    check_actionability,
    check_clarity,
    check_completeness,
    check_consistency,
    check_hallucination_risk,
    check_output_format,
    check_politeness,
    check_role_clarity,
    check_specificity,
    check_structure,
    check_verbosity,
)
from .rules.security import (
    check_injection,
    check_injection_boundary,
    check_jailbreak,
    check_pii,
    check_secrets,
)


class LintEngine:
    def __init__(self, config):
        self.config = config

    def analyze(self, text: str):
        results = []
        results.extend(check_tokens(text, self.config))
        results.extend(check_structure(text, self.config))
        results.extend(check_injection(text, self.config))
        results.extend(check_jailbreak(text, self.config))
        results.extend(check_pii(text, self.config))
        results.extend(check_secrets(text, self.config))
        results.extend(check_injection_boundary(text, self.config))
        results.extend(check_clarity(text, self.config))
        results.extend(check_specificity(text, self.config))
        results.extend(check_verbosity(text, self.config))
        results.extend(check_actionability(text, self.config))
        results.extend(check_consistency(text, self.config))
        results.extend(check_completeness(text, self.config))
        results.extend(check_role_clarity(text, self.config))
        results.extend(check_output_format(text, self.config))
        results.extend(check_hallucination_risk(text, self.config))
        results.extend(check_politeness(text, self.config))

        if self.config.rule_severity_overrides:
            for result in results:
                rule_id = result.get("rule", "")
                if rule_id in self.config.rule_severity_overrides:
                    result["level"] = self.config.rule_severity_overrides[rule_id]

        return results


_SECURITY_RULES = frozenset({
    "prompt-injection", "jailbreak-pattern", "pii-in-prompt",
    "secret-in-prompt", "context-injection-boundary",
})
_COST_RULES = frozenset({"cost", "cost-limit", "politeness-bloat"})
_COMPLETENESS_RULES = frozenset({
    "completeness-edge-cases", "role-clarity", "output-format-missing",
    "hallucination-risk", "specificity-examples", "specificity-constraints",
})
_QUALITY_RULES = frozenset({
    "clarity-vague-terms", "verbosity-sentence-length", "verbosity-redundancy",
    "actionability-weak-verbs", "consistency-terminology", "structure-sections",
})


def compute_score(results: List[Dict]) -> Dict:
    """Return a health score dict: {overall, categories}."""

    def _cat_score(findings: List[Dict], critical_w: int = 25, warn_w: int = 10, info_w: int = 3,
                   critical_cap: int = 100, warn_cap: int = 30, info_cap: int = 15) -> int:
        crit = sum(1 for f in findings if f.get("level") == "CRITICAL")
        warn = sum(1 for f in findings if f.get("level") == "WARN")
        info = sum(1 for f in findings if f.get("level") == "INFO")
        deduction = (
            min(crit * critical_w, critical_cap)
            + min(warn * warn_w, warn_cap)
            + min(info * info_w, info_cap)
        )
        return max(0, 100 - deduction)

    sec = [r for r in results if r.get("rule") in _SECURITY_RULES]
    cost = [r for r in results if r.get("rule") in _COST_RULES]
    comp = [r for r in results if r.get("rule") in _COMPLETENESS_RULES]
    qual = [r for r in results if r.get("rule") in _QUALITY_RULES]

    sec_score = _cat_score(sec, critical_w=25, warn_w=10, critical_cap=50)
    cost_score = _cat_score(cost, critical_w=25, warn_w=10, warn_cap=30)
    qual_score = _cat_score(qual, critical_w=25, warn_w=8, info_w=3, warn_cap=30, info_cap=15)
    comp_score = _cat_score(comp, critical_w=25, warn_w=10, warn_cap=30)

    overall = int(
        sec_score * SCORE_WEIGHTS["security"]
        + cost_score * SCORE_WEIGHTS["cost"]
        + qual_score * SCORE_WEIGHTS["quality"]
        + comp_score * SCORE_WEIGHTS["completeness"]
    )

    return {
        "overall": overall,
        "categories": {
            "security": sec_score,
            "cost": cost_score,
            "quality": qual_score,
            "completeness": comp_score,
        },
    }
