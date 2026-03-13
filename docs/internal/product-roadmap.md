# Product Roadmap

## Technical Debt (fix before anything else)

| Item | Location | Fix |
|---|---|---|
| `_strengthen_verbs()` is a no-op stub | `cli/promptlint/cli.py:377` | Implement verb strengthening or remove from fix pipeline |
| Python `__version__` says `1.0.0`, PyPI ships `1.0.2` | `cli/promptlint/__init__.py:2` | Sync to `1.0.2` |
| npm package has no tests | `npm/` | Port the Python test suite to Vitest |
| No CI/CD pipeline | repo root | Add GitHub Actions (test on push, publish on tag) |

---

## Missing Base Features (blocking V1 "done")

### New Rules
- `hallucination-risk` — detects prompts with no grounding context that invite hallucinations
- `role-clarity` — detects missing system/user role separation
- `output-format-missing` — instruction prompts with no output format spec
- `temperature-hint` — flags creative prompts that don't acknowledge non-determinism

### Config & DX
- Config validation with clear error messages — right now a bad `.promptlintrc` silently falls back to defaults
- Pre-commit hook support — `promptlint --init` should offer to add a `.pre-commit-config.yaml` entry

### Integrations
- **GitHub Action** (`promptlint-action`) — lets teams add prompt linting to CI with 3 lines of YAML
- **npm/Python parity** — npm uses `chars/4` for token counting; Python uses `tiktoken`. Same prompt should produce identical results on both.

---

## Freemium Line

> **Free = everything that helps one developer. Paid = everything that helps a team or scales to production.**

### Free Forever
- All rules (local, offline, no account needed)
- CLI — Python (PyPI) and Node.js (npm)
- VS Code extension
- `.promptlintrc` config
- `--fix`, JSON output, CI exit codes
- GitHub Action (open source)

### Paid / Pro Tier

| Feature | Why it's paid |
|---|---|
| Custom rule authoring (UI) | Saves hours of config writing |
| Team rule-sharing / org config | Multi-user value |
| Dashboard with historical trends | Requires backend storage |
| Slack / Jira / Linear integrations | Ops and team value |
| `promptlint audit` — scan a repo's full prompt history | Compute-heavy |
| API with higher rate limits | Infrastructure cost |
| Private rule registry | Enterprise need |
| SSO / SAML | Enterprise checkbox |

---

## Order of Work

### Now
1. Fix `__init__.py` version mismatch + remove `_strengthen_verbs` stub
2. Add GitHub Actions CI (test on push, publish to PyPI/npm on tag)
3. Add 3–4 high-value new rules

### Next
4. Add npm test suite (Vitest)
5. Config validation with proper error messages
6. Pre-commit hook support
7. GitHub Action (`promptlint-action` repo)

### When base is solid
8. Build paid backend (auth, team config, dashboard)
9. Gate team features behind API key
10. Add usage-based billing (Stripe)

---

## Key Principle

Don't touch the backend/billing layer until the base is solid. Freemium only works if the free tier is genuinely great — users won't pay for the upgrade if the free experience is rough.
