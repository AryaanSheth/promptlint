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
)
from .rules.security import check_injection


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
        
        # Advanced quality checks
        results.extend(check_clarity(text, self.config))
        results.extend(check_specificity(text, self.config))
        results.extend(check_verbosity(text, self.config))
        results.extend(check_actionability(text, self.config))
        results.extend(check_consistency(text, self.config))
        results.extend(check_completeness(text, self.config))

        if not self.config.enabled_rules.get("politeness-bloat", True):
            return results

        escaped_words = [re.escape(word) for word in self.config.politeness_words]
        bloat_regex = r"(?<!\w)(?:" + "|".join(escaped_words) + r")(?!\w)"
        bloat_matches = list(re.finditer(bloat_regex, text, re.IGNORECASE))

        if bloat_matches:
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
                results.append(
                    {
                        "level": "WARN",
                        "rule": "politeness-bloat",
                        "message": (
                            f"Politeness filler detected: '{match.group(0)}'. "
                            "AI doesn't need manners."
                        ),
                    "savings": self.config.politeness_savings_per_hit,
                        "line": line,
                        "context": context,
                    }
                )

        return results
