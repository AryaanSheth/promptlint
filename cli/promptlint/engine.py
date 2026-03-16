import re

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

        return results
