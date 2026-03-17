# PromptLint — Growth PRD
**Version:** 1.2 | **Date:** 2026-03-16 | **Author:** Internal

> This document acts as a system rewrite directive. It is grounded in the actual codebase as it exists today. Every recommendation references a specific file or architectural reality. Follow this in order.

---

## Changelog — 2026-03-16 Next Steps Update

### Situation Assessment

Tasks 1–5 from the original task list are complete in a single session. The product is now in a materially better state than it was 48 hours ago:

- The VS Code extension works without Python installed
- The fix pipeline no longer silently lies about fixing weak verbs
- CI/CD is live — no more manual, error-prone publishes
- Every new signup gets an email that activates them instead of telling them to wait

**What this means:** The product is no longer embarrassing to show. You can now do outreach, press, and investor meetings without worrying that the first experience will break.

**Current bottleneck:** Zero customer conversations. Zero revenue. One investor meeting scheduled. The next 30 days are not a code sprint — they are a customer discovery sprint with one major technical deliverable (the GitHub Action).

---

## Next Steps — Ordered and Specific

### This Week (March 16–22)

#### Code — Ship the GitHub Action (3–4 days)

This is the only code that matters right now. Everything else in the backlog is blocked on real customer signal.

**What to build:**

Create a new `action/` directory in the repo (or a separate `promptlint-action` repo on GitHub). The action must:

1. Accept `path`, `fail-level`, and `config` inputs
2. Run using `npx promptlint-cli` — no Python, works in any repo
3. Output findings as GitHub annotations (inline on the diff, not just console output) using the `::error file=...,line=...::message` syntax
4. Exit non-zero on the configured `fail-level` so PRs fail

**`action.yml` skeleton:**
```yaml
name: 'PromptLint'
description: 'Lint LLM prompts for injection attacks, token waste, and quality issues'
inputs:
  path:
    description: 'Files or glob pattern to lint'
    default: '.'
  fail-level:
    description: 'Severity that causes a non-zero exit: none, warn, critical'
    default: 'critical'
  config:
    description: 'Path to .promptlintrc'
    default: ''
runs:
  using: 'node20'
  main: 'dist/index.js'
```

**Implementation:** Write `src/index.js` using `@actions/core` and `@actions/github`. Import the npm engine directly (`promptlint-cli`) rather than shelling out. Bundle with `@vercel/ncc` into `dist/index.js`. This keeps the action self-contained with no install step.

**Done when:** A test repo with a prompt file containing `"ignore previous instructions"` fails a PR check with an inline annotation on the offending line.

---

#### Outreach — Start today, in parallel with code

Do not wait until the GitHub Action ships to start talking to people. These run simultaneously.

**Daily target:** 10 DMs sent per day, every day this week.

**Where to find people:**
- Twitter/X: search `"prompt injection"`, `"langchain production"`, `"openai api costs"` — quote-tweet or reply first, then DM
- LinkedIn: "AI Engineer" at companies 50–500 employees, Series A–C
- Discord: LangChain `#production`, LlamaIndex `#showcases`, Hugging Face `#llm-apps`

**DM template (copy exactly):**
> "Hey — built a static analyzer for LLM prompts that catches injection attacks and token waste before they hit prod. Works like ESLint but for your system messages. Trying to understand if this is a real pain for teams building on LLMs. 15-min call? No pitch, just learning."

**Goal this week:** 5 calls booked. Not 5 yeses — 5 calendar invites.

**What to listen for:** Anyone who says they manually review prompts, had a prompt injection incident, or is surprised by their OpenAI bill. These are your buyers.

---

### The Jens Ingelstedt Meeting

**Who he is:** Pre-seed/seed angel (Futurology Ventures, ~30 portfolio companies). Currently Global Head of AI Accelerators at New Native — actively building an AI accelerator right now. Former Managing Director, Techstars Stockholm. Named one of Sweden's 199 most important angels by Breakit. He is not a traditional fund manager writing $5M checks.

**What he can actually give you:**
1. Introductions to his 30 portfolio companies — many of which likely build on LLMs and are your ideal early customers
2. Honest feedback from someone who has evaluated hundreds of early AI companies
3. Potential partnership with New Native's accelerator (they give tools to cohort companies — PromptLint could be one of them)
4. A small angel check ($25k–$100k range) — possible but not the primary goal

**How to run the meeting:**

Open with a question, not a pitch:
> "Before I show you the product — in your accelerator work, what's the most common problem you see AI companies have with their prompts in production?"

His answer tells you which angle to demo (security vs. cost vs. reliability). Then show the VS Code extension live — type a prompt with `"ignore previous instructions"` embedded, watch the squiggle appear, apply the fix. That visual is worth ten slide decks.

Be honest about your stage:
> "I've been coding this for two weeks. It's live on PyPI, npm, and the VS Code Marketplace. I haven't charged anyone yet. I'm doing customer conversations now to find out what the real pain is before I build the paid tier."

This is the correct answer. Founders who know what they don't know yet are more fundable than founders who oversell a week of code.

**The specific ask:**
> "The most valuable thing you could do for me right now is intro me to 3–5 people in your portfolio who are building on LLMs in production. Not a sales call — just 15 minutes to understand how they handle prompts today."

**If he asks about fundraising:**
> "I'm not actively raising. I want to get to 10 paying customers first so I know what I'm selling before I take money. But if the right person wanted to come in early, I'd consider it."

**Prepare before the meeting:**
- Know the total install count across all channels
- Know his portfolio list — check Dealroom or LinkedIn for Futurology Ventures companies
- Know what New Native's accelerator does specifically
- Have the VS Code extension demoed and tested on a clean machine the night before

---

### Next 30 Days (March 16 – April 15)

| Week | Code | Outreach | Investor |
|---|---|---|---|
| Mar 16–22 | Ship GitHub Action | 10 DMs/day, 5 calls booked | Jens meeting — ask for 5 portfolio intros |
| Mar 23–29 | GitHub Action in GitHub Marketplace. Add Action tab to landing page | 5 calls conducted. Document top 3 pains heard | Follow up Jens intros. Add to pipeline. |
| Mar 30–Apr 5 | Write first SEO article ("How we caught a prompt injection before prod") | 10 more DMs/day. 5 more calls. | If Jens intros delivered, run those calls |
| Apr 6–12 | If 5+ people said "yes I'd pay" → start org config hosting backend | Synthesize 20 calls. Identify ICP. | Decide: raise or not? |
| Apr 13–15 | — | Reach out to LangChain integrations team | Show HN post (with injection-detection GIF) |

**The decision point at Apr 12:** After 20 customer conversations you will know:
- Whether the security angle (injection) or cost angle (token waste) drives more urgency
- Whether your buyer is an individual engineer or a team/org
- Whether anyone is willing to pay now

If 5+ people said they'd pay: start building the paid tier immediately.
If nobody would pay but people are using it: your ICP or pricing angle is wrong, go back to outreach with a different frame.
If nobody is using it: distribution is the problem, not the product. Pivot the channel.

---

### Phase 2 Trigger Conditions (Do Not Build Until These Are Met)

Do not start building org config hosting, Stripe, or any paid feature until:

- [ ] GitHub Action shipped and tested
- [ ] 20 customer conversations completed and documented
- [ ] At least 5 people have explicitly said they would pay for a team feature
- [ ] At least 3 people from different companies are using it in their real workflow

---

## Changelog — 2026-03-15 Implementation Update

The following items from the ordered task list (§11) were completed in a single session. All changes are committed to `main`.

### What was done and why it matters

#### ✅ Task 1 — Removed `_strengthen_verbs` no-op from the fix pipeline

**Commits:** `5af9297`
**Files:** `cli/promptlint/cli.py`, `cli/promptlint/__init__.py`

The `_strengthen_verbs()` function at `cli.py:377` returned `text` unchanged. It was called inside `_run_lint_on_text()` during every `--fix` run, giving users no feedback and no improvement while silently consuming a step in the pipeline. Every `--fix` invocation was lying about fixing weak verbs.

Removed the function entirely and stripped its call from the pipeline. The fix pipeline now only runs operations that actually do something. A real implementation can be added later when there is time to do it properly.

Also synced `__version__` to `"1.0.2"` to match the version already live on PyPI. The mismatch (`"1.0.0"` in code, `1.0.2` on PyPI) would have caused confusing version output for users running `promptlint --version`.

---

#### ✅ Task 3 — Fixed stale waitlist email

**Commit:** `f4626dc`
**File:** `landing/server.js:144–150`

The signup confirmation email told new users: *"We'll email you when the VS Code extension is live and the CLI hits v1."* Both shipped. Every person who signed up was receiving messaging that made the product look unfinished.

Replaced with a direct welcome email containing:
- Two-line install instructions (`pip install` + first command)
- VS Code Marketplace link
- GitHub link
- Personal signature from Aryaan

This turns every signup into an activation moment instead of a holding pattern.

---

#### ✅ Task 4 — Added GitHub Actions CI/CD

**Commit:** `dbd9aa7`
**File:** `.github/workflows/ci.yml`

The repo had no automation. Every publish was a manual, error-prone process. The `.github/workflows/` directory existed but was empty.

Created a full CI/CD pipeline with four jobs:

| Job | Trigger | What it does |
|---|---|---|
| `python` | every push / PR | `pip install` + `pytest tests/` |
| `npm` | every push / PR | `npm install` + `tsc` (build + typecheck) |
| `vscode` | every push / PR | build npm engine + compile extension |
| `publish-pypi` | tag `v*` | builds wheel, publishes to PyPI via `PYPI_TOKEN` |
| `publish-npm` | tag `v*` | `npm publish` via `NPM_TOKEN` |

The vscode job explicitly builds the npm engine first (since the extension now depends on it — see below), mirroring the correct build order.

---

#### ✅ Task 5 — Fixed VS Code extension to use native npm engine

**Commit:** `08b505f`
**Files:** `vscode/src/linter.ts`, `vscode/src/extension.ts`, `vscode/package.json`

This was the highest-priority architectural fix. The extension called `execFile(pythonPath, ["-m", "promptlint", ...])` for every lint and fix operation (`extension.ts:44–62`). Users who installed the VS Code extension from the Marketplace still had to separately `pip install promptlint-cli` or face a silent failure popup. On Windows, every lint cold-started a Python process — measurably slow.

The npm engine (`npm/src/engine.ts`) already existed and already implemented the full rule set. It was unused by the extension.

**What changed:**

- Added `"promptlint-cli": "file:../npm"` to `vscode/package.json` dependencies — the engine is now bundled into the extension package
- Rewrote `vscode/src/linter.ts` to import `analyze()`, `applyFixes()`, and `loadConfig()` directly from the npm engine — no temp files, no subprocess, no cold-start
- Rewrote `vscode/src/extension.ts`:
  - Removed `runCli()` and the `execFile` import entirely
  - Lint, fix, dashboard, and init commands all run in-process
  - `promptlint.init` writes `.promptlintrc` natively via `fs.writeFileSync` using a bundled starter config — no Python needed
  - `promptlint.explainRule` uses a built-in `RULE_DOCS` map — no Python needed
  - `promptlint.dashboard` computes token/cost data directly from `analyze()` output
  - Added `resolveConfigPath()` to correctly locate `.promptlintrc` relative to the workspace root rather than relying on `process.cwd()` (which points to the VS Code installation directory in extension context)
  - Removed `checkCLI()` — the activation-time popup nagging users to `pip install` is gone

**Net effect:** A user can now install the VS Code extension from the Marketplace and use lint, fix, dashboard, and init with zero additional setup. Python is no longer a dependency for any core feature.

---

### Updated task list status (§11)

| # | Task | Status |
|---|---|---|
| 1 | Remove `_strengthen_verbs` from fix pipeline | ✅ Done |
| 2 | Sync `__version__` to `"1.0.2"` | ✅ Done |
| 3 | Fix stale waitlist email | ✅ Done |
| 4 | Add GitHub Actions CI | ✅ Done |
| 5 | Fix VS Code extension to bundle npm engine | ✅ Done |
| 6 | Ship GitHub Action (`promptlint-action`) | ⬜ Next |
| 7 | Send 10 DMs/day for 14 days | ⬜ Parallel with 1–6 |
| 8 | Add GitHub Action tab to landing page | ⬜ Pending |
| 9 | Build org config hosting | ⬜ Pending |
| 10 | Add Stripe + pricing page | ⬜ Pending |
| 11 | Write first SEO article | ⬜ Pending |
| 12 | Reach out to LangChain integrations team | ⬜ Pending |

**The immediate next action is task 6: ship the GitHub Action** (`promptlint-action`). Tasks 1–5 are now complete and unblock it. Task 7 (customer outreach) should be running in parallel starting today — it does not depend on any code.

---

---

## 1. Current State Diagnosis

### What exists and what's actually broken

| Component | File(s) | Real Problem |
|---|---|---|
| Python CLI | `cli/promptlint/cli.py` | `_strengthen_verbs()` at line 377 is a no-op stub — it's in the live fix pipeline but does nothing |
| VS Code Extension | `vscode/src/extension.ts:44–62` | Calls `execFile(pythonPath, ["-m", "promptlint", ...])` — every lint spawns a Python subprocess. Users must install the Python CLI separately or the extension silently fails |
| Two engines | `cli/promptlint/` + `npm/src/engine.ts` | Two completely separate implementations of the same rules. Already diverged: Python uses tiktoken, npm uses `chars/4`. Will drift further. |
| Landing server | `landing/server.js:144–150` | Waitlist email says "We'll email when VS Code extension is live" — the extension IS live. Sending stale messaging to every signup. |
| Version mismatch | `cli/promptlint/__init__.py` | `__version__` = `"1.0.0"`, PyPI ships `1.0.2` |
| No tests (npm) | `npm/` | No test suite. Rules can break silently on publish. |
| No CI/CD | repo root | No GitHub Actions. Manual publish process. Will cause regressions. |
| No GitHub Action | — | The single highest-value integration is missing entirely |
| Telemetry | everywhere | Zero usage data. Can't make informed product decisions. |

### The critical architectural problem

The VS Code extension (`vscode/src/extension.ts:44`) shells out to Python for every lint operation:

```typescript
execFile(pythonPath, ["-m", "promptlint", ...args], ...)
```

This means:
- Users who install the VS Code extension from the marketplace still need to separately `pip install promptlint-cli`
- If Python isn't in PATH, it silently fails with a pop-up
- The extension has a TypeScript engine (`npm/src/engine.ts`) that could run natively in the extension — it's already there and unused in this context
- Every lint = cold-starting a Python process = slow on Windows

This is your biggest UX problem and the #1 reason users churn from the VS Code extension.

---

## 2. What to Kill / Remove

Do this first. Removing things creates clarity and reduces maintenance burden.

### Kill immediately

**`_strengthen_verbs()` stub** — `cli/promptlint/cli.py:377–378`
- It returns `text` unchanged
- It's called in the live fix pipeline at line 432
- Every `--fix` run is lying to users that weak verbs are being fixed
- Either implement it or remove it from the pipeline entirely
- Recommendation: **remove from pipeline**. Ship a real implementation only when you have time to do it right.

**Stale waitlist email** — `landing/server.js:144–150`
- Currently tells signups "we'll email you when VS Code extension is live"
- The extension shipped. This is wrong.
- Replace with a useful welcome message that gets them installing and using the tool now.

**npm/Python rule duplication**
- Long-term, maintain ONE canonical engine
- The npm engine (`npm/src/engine.ts`) is cleaner and more portable
- Recommendation: make the Python CLI call the npm engine via a subprocess, OR accept divergence is acceptable short-term but explicitly document which is canonical

### Don't add (yet)

- SSO/SAML
- Custom rule authoring UI
- Historical dashboard
- Any feature requiring a new database table
- `promptlint audit` (repo history scan)

These are real paid features. Build them only after your first 10 paying customers ask for them.

---

## 3. Fix Immediately (Before Any Growth Work)

These are blockers. They will kill word-of-mouth and make press coverage backfire.

### P0 — Fix the VS Code extension architecture

**Problem:** `vscode/src/extension.ts:44–62` shells out to Python. Users install the VS Code extension and get a broken experience if Python isn't installed.

**Fix:** Bundle the npm engine directly into the VS Code extension. The engine is already in `npm/src/engine.ts` and compiles to `npm/dist/engine.js`. Import it directly instead of spawning Python.

```
vscode/src/extension.ts  →  import { analyze, applyFixes } from "../../npm/dist/engine"
```

This eliminates the Python dependency for the core lint/fix flow. Python can remain optional for advanced features. This is a 1–2 day change that will dramatically improve activation rate.

**Why this matters for growth:** The VS Code extension is your highest-leverage distribution. It creates daily active usage. If it requires a separate pip install to work, most users who install it will uninstall it within 10 minutes.

### P0 — Fix the stale waitlist email

`landing/server.js:144–150` — replace the email body with:

```
Subject: Welcome to PromptLint

Get started in 30 seconds:

  pip install promptlint-cli
  promptlint --file your-prompt.txt

VS Code extension: [marketplace link]
GitHub: https://github.com/AryaanSheth/promptlint

Reply to this email with questions — I read every one.
— Aryaan
```

Personal signature. Direct install instructions. Makes you human, not a product.

### P1 — Remove the no-op stub from the fix pipeline

`cli/promptlint/cli.py:432` — remove the `_strengthen_verbs` call from `_run_lint_on_text`. The function at line 377 returns `text` unchanged. Keeping it in the pipeline is a silent lie.

### P1 — Sync version strings

`cli/promptlint/__init__.py` — set `__version__ = "1.0.2"` to match PyPI.

### P1 — Add CI/CD (GitHub Actions)

Create `.github/workflows/ci.yml`:
- Run Python tests on every push to `main` and every PR
- Run npm build + typecheck on every push
- Publish to PyPI on tag `v*` (using PYPI_TOKEN secret)
- Publish to npm on tag `v*` (using NPM_TOKEN secret)

Without this, every publish is a manual, error-prone process. You will introduce regressions.

---

## 4. The GitHub Action — Build This Next

This is the single most important feature you can ship. It's missing entirely.

**Why:** A GitHub Action puts promptlint permanently into engineering workflows. A failed PR check is unavoidable. An inline squiggle is ignorable.

**What to build:** A new repo `promptlint-action` (or `action/` folder in this repo):

```yaml
# .github/workflows/promptlint.yml
name: Lint Prompts
on: [push, pull_request]
jobs:
  promptlint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: promptlint/action@v1
        with:
          path: "prompts/"           # default: scan whole repo
          fail-level: "warn"         # default: critical
          config: ".promptlintrc"    # optional
```

**Implementation:** The action should use the npm package (not Python) so it works in any repo without Python installed. Use `npx promptlint-cli` or bundle the engine.

**Timeline:** 3–4 days including testing. Ship before doing any marketing.

---

## 5. Distribution Strategy — Pick a Primary

You currently have four distribution channels. Treat them with this priority order:

| Priority | Channel | Why |
|---|---|---|
| 1 | GitHub Action | Enters CI/CD permanently. Team adoption. |
| 2 | VS Code Extension | Daily active usage. Visible to every engineer on the team. |
| 3 | npm CLI | JS/TS engineers. LangChain/LlamaIndex ecosystem is TypeScript-heavy. |
| 4 | Python CLI (PyPI) | Keep maintained but don't spend time here. Python engineers will find it. |

**What this means concretely:**
- Next 30 days: GitHub Action + VS Code extension fix (P0 above)
- Don't add new PyPI-only features unless users explicitly ask for them
- The npm engine (`npm/src/engine.ts`) is your canonical implementation going forward

---

## 6. The Paid Tier — What to Build and When

### The one feature to build first: Org Config Hosting

**Why this and not something else:** It requires a server (so it's naturally a paid gate), it solves a real team problem (everyone using different configs), it's a weekend build on top of the Supabase infrastructure you already have in `landing/server.js`, and it creates account creation which gives you emails and identity.

**How it works:**

```bash
# Free: local config file
promptlint --config .promptlintrc

# Paid: org config pulled from your server
promptlint --config https://api.promptlint.dev/org/acme-corp/config
```

**Backend changes needed:**
- Add `orgs` table to Supabase (id, slug, config_yaml, api_key, plan)
- Add `GET /org/:slug/config` endpoint to `landing/server.js` (or split into a separate API server)
- Add API key auth middleware
- Add `POST /org/:slug/config` for config upload

**CLI changes needed (`cli/promptlint/utils/config.py`):**
- Detect if `--config` value starts with `https://`
- Fetch over HTTP, cache locally for 1 hour
- Pass through normally to `load_config()`

**Pricing:** $49/month flat per org. No per-seat. No usage metering. Simple.

**When to build:** After the GitHub Action ships and you have evidence that teams are adopting the tool (measure by: GitHub Action installs, or multiple people from the same company email domain signing up).

### The second paid feature: Team Dashboard

Only build this after you have 3 paying org customers who have explicitly asked for it. Don't build it speculatively.

---

## 7. Monetization Implementation Plan

### Phase 1 (Now → Day 30): Zero revenue, maximum distribution

Goal: 500 installs across all channels. 20 customer conversations.

- Fix VS Code extension architecture (P0)
- Ship GitHub Action
- Fix stale email + version strings
- Add CI/CD
- No pricing page, no Stripe, no new backend

### Phase 2 (Day 30 → Day 60): First revenue

Goal: 3 paying orgs at $49/month = $147 MRR (this is validation, not scale)

- Build org config hosting (backend + CLI changes)
- Add pricing page to `landing/index.html`
- Add Stripe Checkout (single SKU: $49/month org plan)
- Wire Stripe webhook to Supabase to provision org
- Reach out personally to your top 10 most-engaged users and offer them 3 months free in exchange for feedback

### Phase 3 (Day 60 → Day 90): Scale distribution

Goal: 2,000 installs. 10 paying orgs = $490 MRR.

- LangChain/LlamaIndex integration listing
- SEO content (2 articles/week — see article list in the 90-day playbook)
- Show HN post (with GIF of injection detection)
- GitHub Action listed in GitHub Marketplace

---

## 8. Landing Page Changes

The current `landing/index.html` needs two changes only. Do not redesign.

### Add: Install tabs that include GitHub Action

Currently the install tabs show `pip install` and `npm install`. Add a third tab:

```yaml
# GitHub Action
- uses: promptlint/action@v1
  with:
    path: prompts/
```

This is the distribution channel that matters most. It should be visible on the homepage.

### Add: Pricing section (when Phase 2 begins)

Simple three-column layout:
- **Free** — everything that runs locally (list features)
- **Team** — $49/month — org config, (future) dashboard, priority support
- **Enterprise** — contact us — SSO, private rule registry, SLA

Don't build the Enterprise tier. Just list it. It signals you're serious about enterprise without committing to build it.

---

## 9. What Not to Change

- The brand, name, and color scheme — they're good
- The dark terminal aesthetic — it resonates with the target user
- The Apache 2.0 license — open source is a distribution strategy, not a mistake
- The core rule engine — it works, it's fast, 12ms is genuinely impressive
- The `.promptlintrc` format — it's clean and familiar
- The security positioning — "catches injection attacks" has enterprise budget attached to it

---

## 10. Success Metrics

Track these weekly. Nothing else.

| Metric | Now | 30-day target | 90-day target |
|---|---|---|---|
| Total installs (all channels) | ~unknown | 500 | 2,000 |
| GitHub Action installs | 0 | 50 | 500 |
| VS Code extension installs | unknown | 200 | 800 |
| Customer conversations had | 0 | 20 | 50 |
| Paying orgs | 0 | 0 | 10 |
| MRR | $0 | $0 | $490 |
| Waitlist emails | unknown | 200 | 1,000 |

The first metric that matters is customer conversations, not installs. You can manufacture installs with a Reddit post. You can't manufacture someone giving you 15 minutes of their time to describe a real pain.

---

## 11. Ordered Task List

Do these in order. Do not skip ahead.

1. [ ] Remove `_strengthen_verbs` from the fix pipeline (`cli/promptlint/cli.py:432`)
2. [ ] Sync `__version__` to `"1.0.2"` in `cli/promptlint/__init__.py`
3. [ ] Fix stale waitlist email in `landing/server.js:144–150`
4. [ ] Add GitHub Actions CI (`.github/workflows/ci.yml`)
5. [ ] Fix VS Code extension to bundle npm engine instead of shelling to Python
6. [ ] Ship GitHub Action (`promptlint-action`)
7. [ ] Send 10 DMs/day for 14 days using the outreach template
8. [ ] Add GitHub Action tab to landing page install section
9. [ ] Build org config hosting (Supabase + CLI changes)
10. [ ] Add Stripe + pricing page
11. [ ] Write first SEO article
12. [ ] Reach out to LangChain integrations team

---

*This PRD is a living document. Update it as you learn from customers. The order of task 7 (customer conversations) runs in parallel with tasks 1–6, not after them.*
