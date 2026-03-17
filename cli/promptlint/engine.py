import re
from typing import Dict, List

from .rules.cost import check_tokens
from .rules.quality import (
    check_structure,
    check_clarity,
    check_specificity,
    check_verbosity,
    check_actionability,
    check_consistency,
    check_completeness,
    check_role_clarity,
    check_output_format,
    check_hallucination_risk,
)
from .rules.security import (
    check_injection,
    check_jailbreak,
    check_pii,
    check_secrets,
    check_injection_boundary,
)


class LintEngine:
    def __init__(self, config):
        self.config = config

    def analyze(self, text: str):
        results = []
        # Cost and token analysis
        results.extend(check_tokens(text, self.config))
        
        # Structure checks
        results.extend(check_structure(text, self.config))
        
        # Security checks
        results.extend(check_injection(text, self.config))
        results.extend(check_jailbreak(text, self.config))
        results.extend(check_pii(text, self.config))
        results.extend(check_secrets(text, self.config))
        results.extend(check_injection_boundary(text, self.config))

        # Advanced quality checks
        results.extend(check_clarity(text, self.config))
        results.extend(check_specificity(text, self.config))
        results.extend(check_verbosity(text, self.config))
        results.extend(check_actionability(text, self.config))
        results.extend(check_consistency(text, self.config))
        results.extend(check_completeness(text, self.config))
        results.extend(check_role_clarity(text, self.config))
        results.extend(check_output_format(text, self.config))
        results.extend(check_hallucination_risk(text, self.config))

        if not self.config.enabled_rules.get("politeness-bloat", True):
            return results

        if not self.config.politeness_words:
            return results

        escaped_words = [re.escape(word) for word in self.config.politeness_words]
        bloat_regex = r"(?<!\w)(?:" + "|".join(escaped_words) + r")(?!\w)"
        bloat_matches = list(re.finditer(bloat_regex, text, re.IGNORECASE))

        if bloat_matches:
            # Determine severity based on team preference
            level = "INFO" if self.config.allow_politeness else "WARN"
            
            for match in bloat_matches:
                line = text.count("\n", 0, match.start()) + 1
                line_start = text.rfind("\n", 0, match.start()) + 1
                line_end = text.find("\n", match.start())
                if line_end == -1:
                    line_end = len(text)
                raw_line = text[line_start:line_end]
                column = match.start() - line_start

                width = self.config.context_width
                if len(raw_line) > width:
                    half = width // 2
                    left = max(column - half, 0)
                    right = min(left + width, len(raw_line))
                    if right - left < width:
                        left = max(right - width, 0)
                    trimmed = raw_line[left:right]
                    caret_pos = column - left
                    prefix = "..." if left > 0 else ""
                    suffix = "..." if right < len(raw_line) else ""
                    display_line = f"{prefix}{trimmed}{suffix}"
                    caret_pos += len(prefix)
                else:
                    display_line = raw_line
                    caret_pos = column

                context = f"{display_line}\n{' ' * caret_pos}^"
                
                # Build message based on team preference
                if self.config.allow_politeness:
                    message = f"Optional: Remove '{match.group(0)}' to save ~{self.config.politeness_savings_per_hit} tokens."
                else:
                    message = f"Consider removing '{match.group(0)}' (adds {self.config.politeness_savings_per_hit} tokens without semantic value)."
                
                results.append(
                    {
                        "level": level,
                        "rule": "politeness-bloat",
                        "message": message,
                        "savings": self.config.politeness_savings_per_hit,
                        "line": line,
                        "context": context,
                    }
                )

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
    """Return a health score dict: {overall, grade, categories}."""

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
        sec_score * 0.40 + cost_score * 0.20 + qual_score * 0.25 + comp_score * 0.15
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
