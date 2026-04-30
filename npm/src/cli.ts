#!/usr/bin/env node
import * as crypto from "crypto";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { loadConfig, STARTER_CONFIG } from "./config";
import { analyze, applyFixes, computeScore } from "./engine";
import type { Finding } from "./rules/cost";

const VERSION = "1.0.0";
const MAX_INPUT_BYTES = 10 * 1024 * 1024; // 10 MB

// ── ANSI color helpers ───────────────────────────────────────────────────

const NO_COLOR = process.env.NO_COLOR || !process.stdout.isTTY;

function color(code: string, text: string): string {
  return NO_COLOR ? text : `\x1b[${code}m${text}\x1b[0m`;
}

const cyan = (t: string) => color("36", t);
const yellow = (t: string) => color("33", t);
const red = (t: string) => color("31", t);
const green = (t: string) => color("32", t);
const dim = (t: string) => color("2", t);
const bold = (t: string) => color("1", t);

// ── Argument parsing ─────────────────────────────────────────────────────

interface Args {
  files: string[];
  text: string;
  config?: string;
  format: "text" | "json";
  fix: boolean;
  failLevel: "none" | "warn" | "critical";
  showDashboard: boolean;
  showScore: boolean;
  badge: boolean;
  quiet: boolean;
  exclude: string[];
  listRules: boolean;
  explain?: string;
  init: boolean;
  installHooks: boolean;
  compare?: [string, string];
  updateBaseline: boolean;
  version: boolean;
  help: boolean;
}

function parseArgs(argv: string[]): Args {
  const args: Args = {
    files: [],
    text: "",
    format: "text",
    fix: false,
    failLevel: "critical",
    showDashboard: false,
    showScore: false,
    badge: false,
    quiet: false,
    exclude: [],
    listRules: false,
    init: false,
    installHooks: false,
    updateBaseline: false,
    version: false,
    help: false,
  };

  let i = 0;
  while (i < argv.length) {
    const arg = argv[i];
    switch (arg) {
      case "-V":
      case "--version":
        args.version = true;
        break;
      case "-h":
      case "--help":
        args.help = true;
        break;
      case "-f":
      case "--file":
        args.files.push(argv[++i]);
        break;
      case "-t":
      case "--text":
        args.text = argv[++i];
        break;
      case "-c":
      case "--config":
        args.config = argv[++i];
        break;
      case "--format":
        args.format = argv[++i] as "text" | "json";
        break;
      case "--fix":
        args.fix = true;
        break;
      case "--fail-level":
        args.failLevel = argv[++i] as "none" | "warn" | "critical";
        break;
      case "--show-dashboard":
        args.showDashboard = true;
        break;
      case "--show-score":
        args.showScore = true;
        break;
      case "--badge":
        args.badge = true;
        break;
      case "-q":
      case "--quiet":
        args.quiet = true;
        break;
      case "--exclude":
        args.exclude.push(argv[++i]);
        break;
      case "--list-rules":
        args.listRules = true;
        break;
      case "--explain":
        args.explain = argv[++i];
        break;
      case "--init":
        args.init = true;
        break;
      case "--install-hooks":
        args.installHooks = true;
        break;
      case "--compare":
        args.compare = [argv[++i], argv[++i]];
        break;
      case "--update-baseline":
        args.updateBaseline = true;
        break;
      default:
        if (!arg.startsWith("-")) args.files.push(arg);
    }
    i++;
  }

  return args;
}

// ── Help / list-rules / explain ──────────────────────────────────────────

const HELP = `
${bold("promptlint")} — static analysis for LLM prompts

${bold("Usage:")}
  promptlint [files...] [options]
  promptlint --text "your prompt here"
  echo "prompt" | promptlint

${bold("Options:")}
  -f, --file <path>          Single prompt file
  -t, --text <text>          Inline prompt text
  -c, --config <path>        Config file (default: .promptlintrc)
      --format text|json     Output format (default: text)
      --fix                  Apply auto-fixes and print optimised prompt
      --fail-level <level>   Exit non-zero at: none | warn | critical (default: critical)
      --show-dashboard       Show token savings breakdown
      --show-score           Show prompt health score (0-100) and grade
      --badge                Output a Shields.io badge URL for the health score
  -q, --quiet                Summary only (CI mode)
      --exclude <glob>       Glob pattern to exclude (repeatable)
      --compare <a> <b>      Compare two prompt files by health score
      --update-baseline      Write current findings to .promptlintbaseline
      --install-hooks        Install a pre-commit git hook
      --list-rules           Show all rules
      --explain <rule-id>    Explain a specific rule
      --init                 Create starter .promptlintrc
  -V, --version              Show version
  -h, --help                 Show this help
`;

const ALL_RULES = [
  { id: "cost",                      category: "Cost",       severity: "INFO",     fix: false, desc: "Reports token count and estimated API cost." },
  { id: "cost-limit",                category: "Cost",       severity: "WARN",     fix: false, desc: "Warns when prompt exceeds configured token limit." },
  { id: "prompt-injection",          category: "Security",   severity: "CRITICAL", fix: true,  desc: "Detects prompt injection patterns (incl. obfuscated)." },
  { id: "jailbreak-pattern",         category: "Security",   severity: "CRITICAL", fix: true,  desc: "Detects roleplay/hypothetical jailbreak patterns." },
  { id: "pii-in-prompt",             category: "Security",   severity: "WARN",     fix: false, desc: "Detects emails, SSNs, phone numbers and credit cards." },
  { id: "secret-in-prompt",          category: "Security",   severity: "CRITICAL", fix: false, desc: "Detects API keys, tokens and credentials." },
  { id: "context-injection-boundary",category: "Security",   severity: "WARN",     fix: false, desc: "Detects template vars not enclosed by structural delimiters." },
  { id: "structure-sections",        category: "Structure",  severity: "WARN",     fix: true,  desc: "Warns when prompt has no explicit sections." },
  { id: "clarity-vague-terms",       category: "Quality",    severity: "WARN",     fix: false, desc: "Flags vague quantifiers and uncertain language." },
  { id: "specificity-examples",      category: "Quality",    severity: "INFO",     fix: false, desc: "Suggests adding examples to instruction prompts." },
  { id: "specificity-constraints",   category: "Quality",    severity: "INFO",     fix: false, desc: "Suggests adding constraints for clearer output." },
  { id: "politeness-bloat",          category: "Quality",    severity: "WARN",     fix: true,  desc: "Flags polite filler words that waste tokens." },
  { id: "verbosity-sentence-length", category: "Quality",    severity: "INFO",     fix: false, desc: "Flags sentences with more than 40 words." },
  { id: "verbosity-redundancy",      category: "Quality",    severity: "INFO",     fix: true,  desc: "Flags verbose phrases with simpler alternatives." },
  { id: "actionability-weak-verbs",  category: "Quality",    severity: "INFO",     fix: false, desc: "Flags excessive passive voice." },
  { id: "consistency-terminology",   category: "Quality",    severity: "INFO",     fix: false, desc: "Flags mixed synonymous terms." },
  { id: "completeness-edge-cases",   category: "Quality",    severity: "INFO",     fix: false, desc: "Suggests specifying edge-case handling." },
  { id: "role-clarity",              category: "Quality",    severity: "WARN",     fix: false, desc: "Flags instructional prompts missing a role/persona definition." },
  { id: "output-format-missing",     category: "Quality",    severity: "WARN",     fix: false, desc: "Detects output instructions without a format spec." },
  { id: "output-length-missing",     category: "Quality",    severity: "INFO",     fix: false, desc: "Detects output instructions without a length constraint." },
  { id: "hallucination-risk",        category: "Quality",    severity: "WARN",     fix: false, desc: "Flags prompts requesting current facts without grounding." },
];

function cmdListRules(): void {
  const w = [32, 10, 10, 5];
  const header = [
    "ID".padEnd(w[0]),
    "CATEGORY".padEnd(w[1]),
    "SEVERITY".padEnd(w[2]),
    "FIX".padEnd(w[3]),
    "DESCRIPTION",
  ].join("  ");
  console.log(bold(header));
  console.log("─".repeat(100));
  for (const r of ALL_RULES) {
    const sev =
      r.severity === "CRITICAL" ? red(r.severity) :
      r.severity === "WARN" ? yellow(r.severity) : cyan(r.severity);
    console.log(
      [
        cyan(r.id.padEnd(w[0])),
        r.category.padEnd(w[1]),
        sev.padEnd(w[2] + (NO_COLOR ? 0 : 9)),
        (r.fix ? "yes" : "-").padEnd(w[3]),
        r.desc,
      ].join("  ")
    );
  }
}

function cmdExplain(ruleId: string): void {
  const rule = ALL_RULES.find((r) => r.id === ruleId);
  if (!rule) {
    console.error(red(`Unknown rule: ${ruleId}`));
    console.error(`Run ${cyan("promptlint --list-rules")} to see available IDs.`);
    process.exit(1);
  }
  console.log(`\n${bold(cyan(rule.id))}  (${rule.category})`);
  console.log(`Default severity: ${yellow(rule.severity)}`);
  console.log(`Auto-fixable:     ${rule.fix ? "yes" : "no"}`);
  console.log(`\n${rule.desc}\n`);
}

function cmdInit(): void {
  const dest = path.join(process.cwd(), ".promptlintrc");
  if (fs.existsSync(dest)) {
    console.error(yellow(".promptlintrc already exists. Remove it first to regenerate."));
    process.exit(1);
  }
  fs.writeFileSync(dest, STARTER_CONFIG, "utf8");
  console.log(green("Created .promptlintrc") + " with default settings.");
  console.log(dim("→") + " Example configs for common use cases: " + cyan("https://docs.promptlint.dev/guide/config-examples"));
}

function cmdInstallHooks(): void {
  const gitDir = path.join(process.cwd(), ".git");
  if (!fs.existsSync(gitDir) || !fs.statSync(gitDir).isDirectory()) {
    console.error(red("Not inside a git repository."));
    process.exit(1);
  }
  const hooksDir = path.join(gitDir, "hooks");
  if (!fs.existsSync(hooksDir)) fs.mkdirSync(hooksDir, { recursive: true });
  const hookPath = path.join(hooksDir, "pre-commit");
  if (fs.existsSync(hookPath)) {
    console.error(yellow("pre-commit hook already exists. Remove it first to reinstall."));
    process.exit(1);
  }
  const script = [
    "#!/bin/sh",
    "# Added by: promptlint --install-hooks",
    "# Lints staged .txt / .md / .prompt files before each commit.",
    "staged=$(git diff --cached --name-only --diff-filter=ACM | grep -E '\\.(txt|md|prompt)$')",
    "if [ -n \"$staged\" ]; then",
    "  promptlint $staged --fail-level critical",
    "fi",
    "",
  ].join(os.EOL);
  fs.writeFileSync(hookPath, script, { encoding: "utf8", mode: 0o755 });
  console.log(green("Installed pre-commit hook") + ` → ${hookPath}`);
  console.log(dim("Staged .txt/.md/.prompt files will be linted before each commit."));
}

// ── Message-array input parsing ──────────────────────────────────────────

function parseMessageText(text: string): string {
  const stripped = text.trim();
  if (!(stripped.startsWith("[") && stripped.endsWith("]"))) return text;
  try {
    const msgs = JSON.parse(stripped);
    if (!Array.isArray(msgs)) return text;
    if (!msgs.every((m: unknown) => typeof m === "object" && m !== null && "content" in (m as object))) return text;
    const parts = (msgs as Array<{ content: unknown }>)
      .map((m) => String(m.content ?? "").trim())
      .filter(Boolean);
    return parts.length ? parts.join("\n\n") : text;
  } catch {
    return text;
  }
}

// ── Baseline fingerprint helpers ─────────────────────────────────────────

const BASELINE_FILE = path.join(process.cwd(), ".promptlintbaseline");

function fingerprint(r: Finding): string {
  const key = `${r.rule}|${r.line}|${(r.message ?? "").slice(0, 60)}`;
  return crypto.createHash("md5").update(key).digest("hex").slice(0, 12);
}

function loadBaseline(): Set<string> {
  try {
    if (!fs.existsSync(BASELINE_FILE)) return new Set();
    const data = JSON.parse(fs.readFileSync(BASELINE_FILE, "utf8")) as { fingerprints?: string[] };
    return new Set(data.fingerprints ?? []);
  } catch {
    return new Set();
  }
}

function saveBaseline(results: Finding[]): void {
  const fps = [...new Set(results.map(fingerprint))].sort();
  fs.writeFileSync(
    BASELINE_FILE,
    JSON.stringify({ version: 1, fingerprints: fps, count: fps.length }, null, 2),
    "utf8",
  );
}

function filterBaseline(results: Finding[], baseline: Set<string>): Finding[] {
  return results.filter((r) => !baseline.has(fingerprint(r)));
}

// ── Score rendering ──────────────────────────────────────────────────────

function renderScore(score: ReturnType<typeof computeScore>): void {
  const g = score.grade;
  const gradeColor = g === "A" ? green : g === "B" ? cyan : g === "C" ? yellow : red;
  console.log(bold("\nPrompt Health Score"));
  console.log(`Overall: ${bold(gradeColor(`${score.overall}/100 (${g})`))}`)  ;
  const cats = score.categories;
  console.log(`  Security:     ${cats.security}`);
  console.log(`  Cost:         ${cats.cost}`);
  console.log(`  Quality:      ${cats.quality}`);
  console.log(`  Completeness: ${cats.completeness}`);
}

function renderBadge(score: ReturnType<typeof computeScore>): void {
  const o = score.overall;
  const badgeColor =
    o >= 90 ? "brightgreen" :
    o >= 75 ? "green" :
    o >= 60 ? "yellow" :
    o >= 45 ? "orange" : "red";
  const label = `promptlint%3A${o}%2F100%20(${score.grade})`;
  const url = `https://img.shields.io/badge/${label}-${badgeColor}`;
  console.log(`\n${cyan("Badge URL:")} ${url}`);
  console.log(`${dim("Markdown:")}  ![PromptLint Score](${url})`);
}

// ── Compare command ──────────────────────────────────────────────────────

function cmdCompare(fileA: string, fileB: string, configPath: string | undefined, fmt: string): void {
  for (const fp of [fileA, fileB]) {
    if (!fs.existsSync(fp)) {
      console.error(red(`File not found: ${fp}`));
      process.exit(1);
    }
  }
  const config = loadConfig(configPath);
  const textA = fs.readFileSync(fileA, "utf8");
  const textB = fs.readFileSync(fileB, "utf8");
  const rA = analyze(textA, config);
  const rB = analyze(textB, config);
  const sA = computeScore(rA);
  const sB = computeScore(rB);
  const deltaOverall = sB.overall - sA.overall;

  if (fmt === "json") {
    console.log(JSON.stringify({
      file_a: { path: fileA, score: sA, findings: rA.length },
      file_b: { path: fileB, score: sB, findings: rB.length },
      delta: {
        overall: deltaOverall,
        security: sB.categories.security - sA.categories.security,
        cost: sB.categories.cost - sA.categories.cost,
        quality: sB.categories.quality - sA.categories.quality,
        completeness: sB.categories.completeness - sA.categories.completeness,
      },
    }, null, 2));
    return;
  }

  const fmtDelta = (d: number) =>
    d > 0 ? green(`+${d}`) : d < 0 ? red(`${d}`) : dim("0");

  console.log(`\n${bold("Compare:")} ${fileA}  vs  ${fileB}`);
  console.log(`  Overall:      ${sA.overall} → ${sB.overall}  (${fmtDelta(deltaOverall)})`);
  for (const cat of ["security", "cost", "quality", "completeness"] as const) {
    const d = sB.categories[cat] - sA.categories[cat];
    console.log(`  ${(cat.charAt(0).toUpperCase() + cat.slice(1)).padEnd(14)}${sA.categories[cat]} → ${sB.categories[cat]}  (${fmtDelta(d)})`);
  }
  console.log(`  Findings:     ${rA.length} → ${rB.length}`);

  if (deltaOverall > 0)
    console.log(`\n${green(`${path.basename(fileB)} scores higher (+${deltaOverall} pts)`)}`);
  else if (deltaOverall < 0)
    console.log(`\n${red(`${path.basename(fileB)} scores lower (${deltaOverall} pts)`)}`);
  else
    console.log(`\n${dim("Scores are identical.")}`);
}

// ── Inline-disable support ───────────────────────────────────────────────

const DISABLE_RE = /#+\s*promptlint-disable(?:\s+(.+))?/i;

function disabledRulesForLine(text: string, lineNo: number): Set<string> {
  const lines = text.split("\n");
  if (lineNo < 1 || lineNo > lines.length) return new Set();
  const m = DISABLE_RE.exec(lines[lineNo - 1]);
  if (!m) return new Set();
  if (!m[1]) return new Set(["*"]);
  return new Set(m[1].split(",").map((s) => s.trim()).filter(Boolean));
}

function filterDisabled(results: Finding[], text: string): Finding[] {
  return results.filter((r) => {
    if (r.line === "-" || typeof r.line !== "number") return true;
    const disabled = disabledRulesForLine(text, r.line);
    return !disabled.has("*") && !disabled.has(r.rule);
  });
}

// ── Rendering ────────────────────────────────────────────────────────────

function renderFindings(results: Finding[], quiet: boolean): void {
  if (quiet) return;
  console.log(bold("PromptLint Findings"));
  for (const r of results) {
    const lvlStr =
      r.level === "CRITICAL" ? red(`[ ${r.level.padEnd(8)} ]`) :
      r.level === "WARN"     ? yellow(`[ ${r.level.padEnd(8)} ]`) :
                               cyan(`[ ${r.level.padEnd(8)} ]`);
    console.log(`${lvlStr} ${r.rule} (line ${r.line}) ${r.message}`);
    if (r.context && r.line !== "-") console.log(r.context);
  }
}

function renderDashboard(
  tokens: number,
  optimizedTokens: number,
  costPer1k: number,
  callsPerDay: number
): void {
  const safe = Math.max(optimizedTokens, 0);
  const saved = tokens - safe;
  const pct = tokens > 0 ? (saved / tokens) * 100 : 0;
  const currCost = (tokens / 1000) * costPer1k;
  const optCost = (safe / 1000) * costPer1k;
  const savingsPerCall = currCost - optCost;

  console.log(bold("Savings Dashboard"));
  console.log(`Current Tokens: ${tokens}`);
  console.log(`Optimized Tokens: ${safe} (${pct.toFixed(1)}% reduction)`);
  console.log(`Savings per Call: ~$${savingsPerCall.toFixed(4)}`);

  if (callsPerDay < 100_000) {
    const daily = savingsPerCall * callsPerDay;
    console.log(`Monthly Savings: ~$${(daily * 30).toFixed(2)} at ${callsPerDay.toLocaleString()} calls/day`);
    console.log(`Annual Savings: ~$${(daily * 365).toFixed(2)}`);
  }
}

// ── Core lint pipeline ───────────────────────────────────────────────────

function maxSeverity(results: Finding[]): number {
  const levels: Record<string, number> = { INFO: 0, WARN: 1, CRITICAL: 2 };
  return results.reduce((max, r) => Math.max(max, levels[r.level] ?? 0), 0);
}

function runLintOnText(
  text: string,
  configPath: string | undefined,
  opts: {
    fix: boolean;
    showDashboard: boolean;
    showScore: boolean;
    badge: boolean;
    format: string;
    quiet: boolean;
    label?: string;
    baseline?: Set<string>;
  }
): Finding[] {
  text = parseMessageText(text);
  const config = loadConfig(configPath);
  let results = analyze(text, config);
  results = filterDisabled(results, text);
  if (opts.baseline?.size) results = filterBaseline(results, opts.baseline);

  let tokens = 0;
  for (const r of results) {
    if (r.rule === "cost" && r.tokens) tokens = r.tokens;
  }

  const savings = results.reduce((s, r) => s + (r.savings ?? 0), 0);
  const optimizedTokens = tokens - savings;

  let optimizedPrompt: string | undefined;
  if (opts.fix) {
    optimizedPrompt = applyFixes(text, config);
  }

  if (opts.format === "json") {
    const safe = Math.max(optimizedTokens, 0);
    const saved = tokens - safe;
    const pct = tokens > 0 ? (saved / tokens) * 100 : 0;
    const currCost = (tokens / 1000) * config.costPer1kTokens;
    const optCost = (safe / 1000) * config.costPer1kTokens;
    const spc = currCost - optCost;

    const dashboard: Record<string, unknown> = {
      current_tokens: tokens,
      optimized_tokens: safe,
      tokens_saved: saved,
      reduction_percentage: Math.round(pct * 10) / 10,
      savings_per_call: Math.round(spc * 1e6) / 1e6,
    };
    if (config.callsPerDay < 100_000) {
      const daily = spc * config.callsPerDay;
      dashboard.monthly_savings = Math.round(daily * 30 * 100) / 100;
      dashboard.annual_savings = Math.round(daily * 365 * 100) / 100;
      dashboard.calls_per_day = config.callsPerDay;
    }

    const payload: Record<string, unknown> = {
      findings: results,
      optimized_prompt: optimizedPrompt,
    };
    if (opts.label) payload.file = opts.label;
    if (opts.showDashboard) payload.dashboard = dashboard;
    if (opts.showScore) payload.score = computeScore(results);
    console.log(JSON.stringify(payload, null, 2));
  } else {
    if (opts.label && !opts.quiet) console.log(`\n${bold(`File: ${opts.label}`)}`);
    renderFindings(results, opts.quiet);
    if (opts.showDashboard && !opts.quiet) {
      console.log("");
      renderDashboard(tokens, optimizedTokens, config.costPer1kTokens, config.callsPerDay);
    }
    if (opts.showScore && !opts.quiet) {
      const score = computeScore(results);
      renderScore(score);
      if (opts.badge) renderBadge(score);
    }
    if (optimizedPrompt !== undefined && !opts.quiet) {
      console.log(bold("Optimised Prompt"));
      console.log(optimizedPrompt);
    }
  }

  return results;
}

// ── File resolution (glob support) ───────────────────────────────────────

function resolveFiles(patterns: string[], exclude: string[]): string[] {
  const seen = new Set<string>();
  const results: string[] = [];

  for (const pattern of patterns) {
    // Basic glob: support ** and * via manual expansion when needed
    // For simplicity, treat each entry as a literal path or simple wildcard
    const expanded = expandGlob(pattern);
    for (const p of expanded) {
      const abs = path.resolve(p);
      if (!seen.has(abs) && fs.existsSync(abs) && fs.statSync(abs).isFile()) {
        seen.add(abs);
        results.push(abs);
      }
    }
  }

  if (exclude.length) {
    const excluded = new Set<string>();
    for (const pat of exclude) {
      for (const p of expandGlob(pat)) excluded.add(path.resolve(p));
    }
    return results.filter((p) => !excluded.has(p));
  }

  return results;
}

function expandGlob(pattern: string): string[] {
  // If no glob chars, return as-is
  if (!/[*?{[]/.test(pattern)) return [pattern];

  // Use a recursive walk
  const parts = pattern.split("/");
  return walkGlob(parts, process.cwd());
}

function walkGlob(parts: string[], dir: string): string[] {
  if (!parts.length) return [dir];
  const [head, ...rest] = parts;

  if (head === "**") {
    const all = [dir, ...getAllDirs(dir)];
    return all.flatMap((d) => walkGlob(rest.length ? rest : ["*"], d));
  }

  let entries: string[];
  try {
    entries = fs.readdirSync(dir);
  } catch {
    return [];
  }

  const re = globToRe(head);
  const matched = entries.filter((e) => re.test(e));
  if (!rest.length) return matched.map((e) => path.join(dir, e));
  return matched.flatMap((e) => walkGlob(rest, path.join(dir, e)));
}

function getAllDirs(dir: string): string[] {
  const result: string[] = [];
  try {
    for (const entry of fs.readdirSync(dir)) {
      const full = path.join(dir, entry);
      if (fs.statSync(full).isDirectory()) {
        result.push(full, ...getAllDirs(full));
      }
    }
  } catch {
    // permission error or not a dir
  }
  return result;
}

function globToRe(pattern: string): RegExp {
  const escaped = pattern.replace(/[.+^${}()|[\]\\]/g, "\\$&").replace(/\*/g, ".*").replace(/\?/g, ".");
  return new RegExp(`^${escaped}$`);
}

// ── Main ─────────────────────────────────────────────────────────────────

async function readStdin(): Promise<string> {
  return new Promise((resolve) => {
    const chunks: Buffer[] = [];
    let total = 0;
    process.stdin.on("data", (chunk: Buffer) => {
      total += chunk.length;
      if (total > MAX_INPUT_BYTES) {
        console.error(red("Stdin input exceeds 10 MB safety limit."));
        process.exit(1);
      }
      chunks.push(chunk);
    });
    process.stdin.on("end", () => resolve(Buffer.concat(chunks).toString("utf8")));
  });
}

async function main(): Promise<void> {
  const args = parseArgs(process.argv.slice(2));

  if (args.version) {
    console.log(`promptlint ${VERSION}`);
    return;
  }
  if (args.help) {
    console.log(HELP);
    return;
  }
  if (args.listRules) {
    cmdListRules();
    return;
  }
  if (args.explain) {
    cmdExplain(args.explain);
    return;
  }
  if (args.init) {
    cmdInit();
    return;
  }
  if (args.installHooks) {
    cmdInstallHooks();
    return;
  }
  if (args.compare) {
    cmdCompare(args.compare[0], args.compare[1], args.config, args.format);
    return;
  }

  const resolvedFiles = resolveFiles(args.files, args.exclude);

  // Validate explicit file paths
  for (const f of args.files) {
    if (!/[*?]/.test(f) && !fs.existsSync(f)) {
      console.error(red(`File not found: ${f}`));
      process.exit(1);
    }
  }
  if (args.config && !fs.existsSync(args.config)) {
    console.error(red(`Config file not found: ${args.config}`));
    process.exit(1);
  }

  const hasInput =
    resolvedFiles.length > 0 ||
    args.text.trim() ||
    !process.stdin.isTTY;

  if (!hasInput) {
    console.log(HELP);
    return;
  }

  const baseline = args.updateBaseline ? new Set<string>() : loadBaseline();

  const opts = {
    fix: args.fix,
    showDashboard: args.showDashboard,
    showScore: args.showScore,
    badge: args.badge,
    format: args.format,
    quiet: args.quiet,
    baseline,
  };

  const t0 = Date.now();
  const allResults: Finding[] = [];

  if (resolvedFiles.length) {
    for (const fp of resolvedFiles) {
      const fstat = fs.statSync(fp);
      if (fstat.size > MAX_INPUT_BYTES) {
        console.error(red(`Skipping ${fp}: exceeds 10 MB safety limit.`));
        continue;
      }
      const text = fs.readFileSync(fp, "utf8");
      const label = resolvedFiles.length > 1 ? fp : undefined;
      const results = runLintOnText(text, args.config, { ...opts, label });
      allResults.push(...results);
    }
  } else {
    const text = args.text.trim()
      ? args.text.replace(/\\n/g, "\n")
      : await readStdin();
    allResults.push(...runLintOnText(text, args.config, opts));
  }

  if (args.updateBaseline) {
    saveBaseline(allResults);
    console.log(green("Baseline updated") + ` → ${BASELINE_FILE} (${allResults.length} fingerprint(s))`);
    return;
  }

  const elapsed = ((Date.now() - t0) / 1000).toFixed(2);
  const nFiles = resolvedFiles.length || 1;

  if (args.format !== "json") {
    console.log(dim(`\n${nFiles} file(s) scanned, ${allResults.length} finding(s) in ${elapsed}s`));
  }

  const severity = maxSeverity(allResults);
  if (args.failLevel === "warn" && severity >= 1) process.exit(1);
  if (args.failLevel === "critical" && severity >= 2) process.exit(2);
}

main().catch((err) => {
  console.error(red(String(err)));
  process.exit(1);
});
