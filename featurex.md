# V1 Core Features (Private)

This document breaks down V1 core features into issue-ready scopes with goals,
deliverables, and acceptance criteria. Copy each section into a GitHub issue.

---

## 1) Policy Packs (Team-level Rules)

**Goal**  
Allow teams to apply consistent rule presets across repos and environments.

**Problem it solves**  
Teams need shared standards, not one-off configs.

**Scope**  
- Define a `policy` concept (e.g., `policy: cost-first`) in config.  
- Support built-in presets: `cost-first`, `security-first`, `quality-first`.  
- Allow overriding specific rules after a policy is selected.

**Deliverables**  
- Policy presets defined in code.  
- Config parsing + validation.  
- CLI displays active policy name in output.

**Acceptance Criteria**  
- Selecting `policy: cost-first` enables cost rules and disables others.  
- Overrides in `.promptlintrc` take precedence over policy defaults.  
- Output shows selected policy and applied overrides.

---

## 2) IDE Integration (Live Linting)

**Goal**  
Provide live feedback while editing prompts.

**Problem it solves**  
Developers won’t run a CLI manually.

**Scope**  
- Create a lightweight local server (`promptlint serve`).  
- Provide a JSON endpoint that accepts prompt text and returns findings.  
- Document how an IDE extension can call the endpoint.

**Deliverables**  
- Local server command.  
- `/lint` JSON endpoint.  
- README section with IDE integration guidance.

**Acceptance Criteria**  
- `promptlint serve` starts a local server.  
- POST `/lint` returns findings in JSON format.  
- Server handles multiple requests without crashing.

---

## 3) CI / Pre-commit Enforcement

**Goal**  
Make rule violations block merges automatically.

**Problem it solves**  
Teams need enforcement, not just suggestions.

**Scope**  
- Ensure exit codes match `--fail-level`.  
- Provide `--format json` for CI parsing.  
- Add a pre-commit example in README.

**Deliverables**  
- Stable exit code behavior.  
- CI-friendly JSON output.  
- Example pre-commit config.

**Acceptance Criteria**  
- `--fail-level warn` exits non-zero on WARN.  
- JSON output contains findings and metadata.  
- README includes a working pre-commit snippet.

---

## 4) Cost Modeling + Savings Summary

**Goal**  
Make ROI obvious and measurable.

**Problem it solves**  
Investors and buyers want hard numbers.

**Scope**  
- Include daily, monthly, and annual cost.  
- Show estimated savings after fixes (politeness removal).  
- Allow config for model cost and calls/day.

**Deliverables**  
- Expanded cost calculations.  
- Dashboard output (toggleable).  
- JSON output includes all cost metrics.

**Acceptance Criteria**  
- Costs match config settings.  
- Savings delta displayed in output.  
- JSON includes `daily_cost`, `monthly_cost`, `annual_cost`.

---

## 5) Security Scanner (Injection + PII)

**Goal**  
Detect risky prompt patterns before production.

**Problem it solves**  
Prompt injection and data leakage risks.

**Scope**  
- Expand injection pattern list.  
- Add PII detection (emails, phone numbers, SSNs).  
- Severity set to CRITICAL for security hits.

**Deliverables**  
- PII rule module.  
- Expanded injection patterns in config.  
- CRITICAL severity for all security hits.

**Acceptance Criteria**  
- PII matches are detected with line context.  
- Injection patterns trigger CRITICAL.  
- Security checks are configurable in `.promptlintrc`.

---

## 6) Auto-Fix / Suggest Mode

**Goal**  
Let users immediately clean prompts.

**Problem it solves**  
Reduces friction and shows instant value.

**Scope**  
- `--fix` removes politeness bloat.  
- Optional fix for missing tags (scaffold template).  
- Output optimized prompt.

**Deliverables**  
- `--fix` covers politeness and structure scaffolding.  
- Optimized prompt in output.  
- JSON output includes `optimized_prompt`.

**Acceptance Criteria**  
- Running with `--fix` outputs cleaned prompt.  
- Non-fix mode does not alter output.  
- Optimized prompt is valid and readable.

---

## 7) Analytics Dashboard (Optional Cloud)

**Goal**  
Show usage trends and ROI at team level.

**Problem it solves**  
Leadership needs visibility to justify spend.

**Scope**  
- Export metrics in JSON for dashboard ingestion.  
- Define metrics: tokens, cost, savings, security hits.  
- (Optional) simple hosted dashboard MVP.

**Deliverables**  
- JSON schema for analytics export.  
- Docs for dashboard ingestion.  
- Optional minimal dashboard prototype.

**Acceptance Criteria**  
- JSON export includes all metrics fields.  
- Dashboards can be built from output alone.  
- No sensitive prompt text stored by default.

---

## 8) Audit Logs + Report Export

**Goal**  
Enable compliance review and audits.

**Problem it solves**  
Enterprise buyers need auditability.

**Scope**  
- Export CSV/JSON reports of findings.  
- Include timestamps, rule name, severity, and line.  
- Provide a `--report` flag to save file.

**Deliverables**  
- Report exporter for CSV/JSON.  
- `--report` CLI option.  
- README documentation.

**Acceptance Criteria**  
- Report files generated correctly.  
- Fields match the spec.  
- Works with CI scripts.

---

## 9) Extensible Rule SDK

**Goal**  
Allow teams to write custom rules.

**Problem it solves**  
Every org has unique standards.

**Scope**  
- Define a rule interface contract.  
- Load rules from a `rules/` folder or entry point.  
- Document how to create a custom rule.

**Deliverables**  
- Rule interface spec.  
- Plugin loader.  
- Example custom rule.

**Acceptance Criteria**  
- Custom rule runs alongside built-ins.  
- Failing rule reports in output.  
- Docs show how to add custom rules.

