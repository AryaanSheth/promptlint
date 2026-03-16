"""Centralised rule catalogue used by --list-rules and --explain."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass(frozen=True)
class RuleMeta:
    id: str
    category: str
    default_severity: str
    fixable: bool
    short: str
    long: str


_RULES: List[RuleMeta] = [
    RuleMeta(
        id="cost",
        category="Cost & Tokens",
        default_severity="INFO",
        fixable=False,
        short="Token count and cost-per-call estimate.",
        long=(
            "Counts the tokens in your prompt using tiktoken and reports the\n"
            "estimated cost per API call based on the configured model and\n"
            "cost_per_1k_tokens.  When calls_per_day < 100 000 it also shows\n"
            "daily cost projections.\n\n"
            "Example output:\n"
            "  [ INFO ] cost (line -) Prompt is ~97 tokens (~$0.0005 input per call on gpt-4o)."
        ),
    ),
    RuleMeta(
        id="cost-limit",
        category="Cost & Tokens",
        default_severity="WARN",
        fixable=False,
        short="Alert when prompt exceeds the configured token limit.",
        long=(
            "Triggers when the prompt's token count is greater than the\n"
            "token_limit value in your .promptlintrc.  Set token_limit to\n"
            "60-70 %% of your model's actual context window to leave room for\n"
            "the response.\n\n"
            "Example output:\n"
            "  [ WARN ] cost-limit (line -) Prompt exceeds token limit by 50 tokens (850 > 800)."
        ),
    ),
    RuleMeta(
        id="prompt-injection",
        category="Security",
        default_severity="CRITICAL",
        fixable=True,
        short="Detect prompt-injection patterns.",
        long=(
            "Scans for regex patterns commonly used in injection attacks such\n"
            "as 'ignore previous instructions' or 'system prompt extraction'.\n"
            "Text is normalized before matching to catch leetspeak (1gn0r3),\n"
            "zero-width unicode characters, and character repetition evasion.\n"
            "Patterns are configurable under rules.prompt_injection.patterns\n"
            "in .promptlintrc.\n\n"
            "With --fix the offending lines are removed entirely.\n\n"
            "Example output:\n"
            "  [ CRITICAL ] prompt-injection (line 3) Injection pattern detected: 'ignore previous instructions'."
        ),
    ),
    RuleMeta(
        id="structure-sections",
        category="Structure",
        default_severity="WARN",
        fixable=True,
        short="Verify the prompt has explicit sections (XML, headings, etc.).",
        long=(
            "Checks that the prompt uses at least one structuring method:\n"
            "XML tags, markdown headers, numbered lists, headings (Task:,\n"
            "Context:), or fenced code blocks.  If nothing is detected a\n"
            "warning is raised.\n\n"
            "With --fix, missing XML tags (<task>, <context>, <output_format>)\n"
            "are scaffolded around the content."
        ),
    ),
    RuleMeta(
        id="clarity-vague-terms",
        category="Quality: Clarity",
        default_severity="WARN",
        fixable=False,
        short="Flag vague or ambiguous words.",
        long=(
            "Detects words like 'some', 'various', 'maybe', 'good', 'nice',\n"
            "'appropriate', etc. that make instructions imprecise.  Each hit\n"
            "is reported with the line and caret context.\n\n"
            "Tip: replace vague terms with specific counts, criteria, or\n"
            "enumerations."
        ),
    ),
    RuleMeta(
        id="specificity-examples",
        category="Quality: Specificity",
        default_severity="INFO",
        fixable=False,
        short="Suggest adding examples when instructions are complex.",
        long=(
            "If the prompt contains instruction verbs (write, create,\n"
            "generate ...) but no example markers (e.g., 'for example',\n"
            "'such as'), this rule suggests you add one.\n\n"
            "Only fires when the prompt is longer than 100 characters."
        ),
    ),
    RuleMeta(
        id="specificity-constraints",
        category="Quality: Specificity",
        default_severity="INFO",
        fixable=False,
        short="Suggest adding explicit constraints (length, format, scope).",
        long=(
            "Fires when the prompt contains a task verb but no constraint\n"
            "words like 'must', 'should', 'limit', 'maximum', 'only', etc.\n"
            "Adding constraints reduces ambiguity and improves first-try\n"
            "success rates."
        ),
    ),
    RuleMeta(
        id="politeness-bloat",
        category="Quality: Efficiency",
        default_severity="WARN",
        fixable=True,
        short="Detect unnecessary politeness words that waste tokens.",
        long=(
            "Finds words like 'please', 'kindly', 'thank you', 'if possible'\n"
            "that add tokens without improving LLM output.  Severity depends\n"
            "on allow_politeness in config (WARN when false, INFO when true).\n\n"
            "With --fix the words and leftover fragments are removed and the\n"
            "text is re-normalised."
        ),
    ),
    RuleMeta(
        id="verbosity-sentence-length",
        category="Quality: Efficiency",
        default_severity="INFO",
        fixable=False,
        short="Flag sentences longer than 40 words.",
        long=(
            "Extremely long sentences are harder for models to parse and\n"
            "often contain redundant information.  Consider splitting them\n"
            "into shorter, focused instructions."
        ),
    ),
    RuleMeta(
        id="verbosity-redundancy",
        category="Quality: Efficiency",
        default_severity="INFO",
        fixable=True,
        short="Detect redundant phrases that can be simplified.",
        long=(
            "Catches phrases like:\n"
            "  'in order to'         -> 'to'\n"
            "  'due to the fact that' -> 'because'\n"
            "  'at this point in time' -> 'now'\n"
            "  'for the purpose of'  -> 'for'\n"
            "  'in the event that'   -> 'if'\n"
            "  'prior to'           -> 'before'\n"
            "  'subsequent to'      -> 'after'\n\n"
            "With --fix the replacements are applied automatically."
        ),
    ),
    RuleMeta(
        id="actionability-weak-verbs",
        category="Quality: Actionability",
        default_severity="INFO",
        fixable=False,
        short="Detect heavy use of passive voice.",
        long=(
            "Reports when more than three passive-voice constructions\n"
            "(e.g. 'is generated', 'was written') appear in the prompt.\n"
            "Active voice ('generate', 'write') is clearer and more direct."
        ),
    ),
    RuleMeta(
        id="consistency-terminology",
        category="Quality: Consistency",
        default_severity="INFO",
        fixable=False,
        short="Detect mixed terminology (user/customer, function/method).",
        long=(
            "Checks for competing terms that refer to the same concept:\n"
            "  user vs customer\n"
            "  function vs method\n"
            "  error vs exception\n\n"
            "Pick one term and use it throughout the prompt."
        ),
    ),
    RuleMeta(
        id="completeness-edge-cases",
        category="Quality: Completeness",
        default_severity="INFO",
        fixable=False,
        short="Suggest specifying edge-case and error handling.",
        long=(
            "If the prompt asks the model to build or generate something but\n"
            "never mentions errors, edge cases, null, empty, or invalid\n"
            "inputs, this rule nudges you to add that guidance."
        ),
    ),
    RuleMeta(
        id="jailbreak-pattern",
        category="Security",
        default_severity="CRITICAL",
        fixable=True,
        short="Detect social-engineering and roleplay jailbreak patterns.",
        long=(
            "Scans for patterns that use roleplay, hypotheticals, or fictional\n"
            "framing to bypass AI guardrails: 'pretend you are', 'DAN', 'no\n"
            "restrictions', 'developer mode', etc. Applies the same leet-speak\n"
            "and unicode normalization as prompt-injection.\n\n"
            "With --fix the offending lines are removed."
        ),
    ),
    RuleMeta(
        id="role-clarity",
        category="Quality: Structure",
        default_severity="WARN",
        fixable=False,
        short="Flag instructional prompts missing a role/persona definition.",
        long=(
            "Detects system prompts that contain instructional language but\n"
            "never define the model's role. Prompts without 'You are a [role]'\n"
            "produce inconsistent, generic output. Only fires on prompts with\n"
            "30+ words that contain instructional verbs."
        ),
    ),
    RuleMeta(
        id="output-format-missing",
        category="Quality: Completeness",
        default_severity="WARN",
        fixable=False,
        short="Detect output instructions without a format specification.",
        long=(
            "Fires when the prompt contains output-instruction verbs (list,\n"
            "extract, return, generate, etc.) but no format specification\n"
            "(JSON, CSV, markdown, bullet list, etc.).\n\n"
            "Unspecified format is the #1 cause of inconsistent LLM outputs\n"
            "in production — the model invents its own format every call."
        ),
    ),
    RuleMeta(
        id="pii-in-prompt",
        category="Security",
        default_severity="WARN",
        fixable=False,
        short="Detect PII (emails, SSNs, phone numbers, credit cards) in prompts.",
        long=(
            "Scans for personally identifiable information hardcoded into\n"
            "prompt files: email addresses, SSNs, phone numbers, credit card\n"
            "numbers, and IP addresses. Skips template variables like {email}.\n\n"
            "Configurable per PII type under rules.pii_in_prompt in .promptlintrc.\n"
            "GDPR/HIPAA blocker for enterprise adoption."
        ),
    ),
    RuleMeta(
        id="secret-in-prompt",
        category="Security",
        default_severity="CRITICAL",
        fixable=False,
        short="Detect API keys, tokens, and credentials hardcoded in prompts.",
        long=(
            "Scans for API keys (OpenAI sk-, Anthropic sk-ant-, GitHub ghp_),\n"
            "Bearer tokens, generic api_key assignments, hardcoded passwords,\n"
            "and hex hashes that may be tokens. Skips template variables.\n\n"
            "Risk: system compromise. Remove before committing."
        ),
    ),
    RuleMeta(
        id="hallucination-risk",
        category="Quality: Reliability",
        default_severity="WARN",
        fixable=False,
        short="Flag prompts requesting current facts without grounding context.",
        long=(
            "Detects prompts that ask for current/recent information ('what is\n"
            "the latest', 'as of today') without providing a grounding context\n"
            "variable ({context}), <context> tag, or 'Based on the following'\n"
            "preamble. These prompts will hallucinate consistently.\n\n"
            "Fix: add a {context} variable and populate it with source data."
        ),
    ),
    RuleMeta(
        id="context-injection-boundary",
        category="Security",
        default_severity="WARN",
        fixable=False,
        short="Detect template variables not enclosed by structural delimiters.",
        long=(
            "Finds template variables ({user_input}, {{query}}) placed inside\n"
            "instructional text without a structural delimiter (XML tag, code\n"
            "fence, or labeled header like 'User Input:'). This is the\n"
            "architectural root cause of prompt injection: without a boundary,\n"
            "appending instructions to user content works trivially.\n\n"
            "Fix: wrap with <user_input>{user_input}</user_input> or a fence."
        ),
    ),
]

RULE_MAP: Dict[str, RuleMeta] = {r.id: r for r in _RULES}
ALL_RULES: List[RuleMeta] = list(_RULES)
