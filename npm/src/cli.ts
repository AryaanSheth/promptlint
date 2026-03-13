#!/usr/bin/env node
import * as fs from "fs";
import * as path from "path";
import * as readline from "readline";
import { loadConfig, STARTER_CONFIG } from "./config";
import { analyze, applyFixes } from "./engine";
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
  quiet: boolean;
  exclude: string[];
  listRules: boolean;
  explain?: string;
  init: boolean;
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
    quiet: false,
    exclude: [],
    listRules: false,
    init: false,
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
  -q, --quiet                Summary only (CI mode)
      --exclude <glob>       Glob pattern to exclude (repeatable)
      --list-rules           Show all rules
      --explain <rule-id>    Explain a specific rule
      --init                 Create starter .promptlintrc
  -V, --version              Show version
  -h, --help                 Show this help
`;

const ALL_RULES = [
  { id: "cost",                     category: "Cost",     severity: "INFO",     fix: false, desc: "Reports token count and estimated API cost." },
  { id: "cost-limit",               category: "Cost",     severity: "WARN",     fix: false, desc: "Warns when prompt exceeds configured token limit." },
  { id: "prompt-injection",         category: "Security", severity: "CRITICAL", fix: true,  desc: "Detects prompt injection patterns (incl. obfuscated)." },
  { id: "structure-sections",       category: "Structure",severity: "WARN",     fix: true,  desc: "Warns when prompt has no explicit sections." },
  { id: "clarity-vague-terms",      category: "Quality",  severity: "WARN",     fix: false, desc: "Flags vague quantifiers and uncertain language." },
  { id: "specificity-examples",     category: "Quality",  severity: "INFO",     fix: false, desc: "Suggests adding examples to instruction prompts." },
  { id: "specificity-constraints",  category: "Quality",  severity: "INFO",     fix: false, desc: "Suggests adding constraints for clearer output." },
  { id: "politeness-bloat",         category: "Quality",  severity: "WARN",     fix: true,  desc: "Flags polite filler words that waste tokens." },
  { id: "verbosity-sentence-length",category: "Quality",  severity: "INFO",     fix: false, desc: "Flags sentences with more than 40 words." },
  { id: "verbosity-redundancy",     category: "Quality",  severity: "INFO",     fix: true,  desc: "Flags verbose phrases with simpler alternatives." },
  { id: "actionability-weak-verbs", category: "Quality",  severity: "INFO",     fix: false, desc: "Flags excessive passive voice." },
  { id: "consistency-terminology",  category: "Quality",  severity: "INFO",     fix: false, desc: "Flags mixed synonymous terms." },
  { id: "completeness-edge-cases",  category: "Quality",  severity: "INFO",     fix: false, desc: "Suggests specifying edge-case handling." },
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
  opts: { fix: boolean; showDashboard: boolean; format: string; quiet: boolean; label?: string }
): Finding[] {
  const config = loadConfig(configPath);
  let results = analyze(text, config);
  results = filterDisabled(results, text);

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
    console.log(JSON.stringify(payload, null, 2));
  } else {
    if (opts.label && !opts.quiet) console.log(`\n${bold(`File: ${opts.label}`)}`);
    renderFindings(results, opts.quiet);
    if (opts.showDashboard && !opts.quiet) {
      console.log("");
      renderDashboard(tokens, optimizedTokens, config.costPer1kTokens, config.callsPerDay);
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

  const opts = {
    fix: args.fix,
    showDashboard: args.showDashboard,
    format: args.format,
    quiet: args.quiet,
  };

  const t0 = Date.now();
  const allResults: Finding[] = [];

  if (resolvedFiles.length) {
    for (const fp of resolvedFiles) {
      const stat = fs.statSync(fp);
      if (stat.size > MAX_INPUT_BYTES) {
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
