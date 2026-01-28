# PromptLint Demo

This folder contains demonstration files and examples for PromptLint.

## Files

### demo.py
Interactive demonstration script that runs all 5 test scenarios:
1. Bad prompt analysis (20+ issues)
2. Bad prompt with savings dashboard
3. Auto-fix demonstration
4. Good prompt analysis (minimal issues)
5. JSON output for CI/CD

**Usage:**
```bash
# From the project root directory
python demo/demo.py
```

### example_bad_prompt.txt
A deliberately poorly-written prompt that demonstrates multiple quality issues:
- Politeness bloat ("please", "kindly", "thank you")
- Vague terms ("some", "various", "stuff", "appropriate")
- Uncertain language ("maybe", "perhaps", "might")
- Redundant phrases ("in order to", "due to the fact that")
- Prompt injection attempt
- Missing structure tags
- Mixed terminology

Expected to trigger 20+ issues across all quality categories.

**Usage:**
```bash
python -m promptlint.cli --file demo/example_bad_prompt.txt
python -m promptlint.cli --file demo/example_bad_prompt.txt --fix
```

### example_good_prompt.txt
A well-written prompt that follows best practices:
- Clear structure with XML tags
- Proper delimiters
- Specific requirements and constraints
- Examples provided
- Edge cases addressed
- No vague or uncertain language
- No politeness bloat

Expected to pass most checks with minimal issues.

**Usage:**
```bash
python -m promptlint.cli --file demo/example_good_prompt.txt
```

## Quick Start

Run all demonstrations at once:
```bash
python demo/demo.py
```

Or test individual examples:
```bash
# See all quality issues
python -m promptlint.cli --file demo/example_bad_prompt.txt --show-dashboard

# See auto-fix in action
python -m promptlint.cli --file demo/example_bad_prompt.txt --fix

# Verify best practices
python -m promptlint.cli --file demo/example_good_prompt.txt

# JSON output for CI/CD
python -m promptlint.cli --file demo/example_good_prompt.txt --format json
```

## What to Expect

### Bad Prompt Results
- **Issues detected:** 20+ across all categories
- **Token reduction:** ~39% (97 → 59 tokens)
- **Categories flagged:** 
  - Security (CRITICAL): Prompt injection
  - Clarity (WARN): 13 vague/uncertain terms
  - Verbosity (INFO): 4 redundant phrases
  - Consistency (INFO): Mixed terminology
  - Structure (WARN): Missing tags and delimiters

### Good Prompt Results
- **Issues detected:** 1-2 minor INFO-level suggestions
- **Categories passed:** ✓ Security, ✓ Structure, ✓ Clarity, ✓ Specificity, ✓ Completeness
- **Quality score:** Excellent

## Learning from the Examples

Compare `example_bad_prompt.txt` and `example_good_prompt.txt` side-by-side to understand:
- How structure improves clarity
- Why specificity matters
- The cost of politeness bloat
- The importance of examples and constraints
- Security implications of injection patterns
