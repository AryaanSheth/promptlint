import type { PromptlintConfig } from "./config";
import { checkTokens, countTokens } from "./rules/cost";
import type { Finding } from "./rules/cost";
import {
  checkInjection,
  checkJailbreak,
  checkPii,
  checkSecrets,
  checkInjectionBoundary,
} from "./rules/security";
import {
  checkStructure,
  checkClarity,
  checkSpecificity,
  checkVerbosity,
  checkActionability,
  checkConsistency,
  checkCompleteness,
  checkRoleClarity,
  checkOutputFormat,
  checkHallucinationRisk,
} from "./rules/quality";
import { lineNumber, lineContext } from "./rules/utils";

export type { Finding };

export function analyze(text: string, config: PromptlintConfig): Finding[] {
  const results: Finding[] = [];

  results.push(...checkTokens(text, config));
  results.push(...checkStructure(text, config));
  results.push(...checkInjection(text, config));
  results.push(...checkJailbreak(text, config));
  results.push(...checkPii(text, config));
  results.push(...checkSecrets(text, config));
  results.push(...checkInjectionBoundary(text, config));
  results.push(...checkClarity(text, config));
  results.push(...checkSpecificity(text, config));
  results.push(...checkVerbosity(text, config));
  results.push(...checkActionability(text, config));
  results.push(...checkConsistency(text, config));
  results.push(...checkCompleteness(text, config));
  results.push(...checkRoleClarity(text, config));
  results.push(...checkOutputFormat(text, config));
  results.push(...checkHallucinationRisk(text, config));
  results.push(...checkPoliteness(text, config));

  // Apply rule severity overrides
  if (config.ruleSeverityOverrides && Object.keys(config.ruleSeverityOverrides).length > 0) {
    for (const r of results) {
      const override = config.ruleSeverityOverrides[r.rule];
      if (override) r.level = override as Finding["level"];
    }
  }

  return results;
}

function checkPoliteness(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["politeness-bloat"] ?? true)) return [];
  if (!config.politenessWords.length) return [];

  const escaped = config.politenessWords.map((w) =>
    w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  );
  const re = new RegExp(`(?<!\\w)(?:${escaped.join("|")})(?!\\w)`, "gi");

  const results: Finding[] = [];
  let m: RegExpExecArray | null;
  re.lastIndex = 0;
  while ((m = re.exec(text)) !== null) {
    const level = config.allowPoliteness ? "INFO" : ("WARN" as const);
    const message = config.allowPoliteness
      ? `Optional: Remove '${m[0]}' to save ~${config.politenessSavingsPerHit} tokens.`
      : `Consider removing '${m[0]}' (adds ${config.politenessSavingsPerHit} tokens without semantic value).`;

    results.push({
      level,
      rule: "politeness-bloat",
      message,
      savings: config.politenessSavingsPerHit,
      line: lineNumber(text, m.index),
      context: lineContext(text, m.index, config.contextWidth),
    });
  }
  return results;
}

// ── Auto-fix pipeline ────────────────────────────────────────────────────

export function applyFixes(
  text: string,
  config: PromptlintConfig
): string {
  if (!config.fixEnabled) return text;

  let out = text;

  if (config.fixRules["prompt-injection"]) {
    out = removeInjectionContent(out, config.injectionPatterns);
  }
  if (config.fixRules["politeness-bloat"]) {
    out = applyPolitenessFix(out, config.politenessWords);
  }
  if (config.fixRules["verbosity-redundancy"]) {
    out = fixRedundancy(out);
  }
  if (config.fixRules["structure-scaffold"]) {
    out = applyStructureScaffold(out, config.requiredTags);
  }

  return out;
}

function removeInjectionContent(text: string, patterns: string[]): string {
  if (!patterns.length) return text;
  const lines = text.split("\n");
  const filtered = lines.filter((line) => {
    for (const p of patterns) {
      try {
        if (new RegExp(p, "i").test(line)) return false;
      } catch {
        // invalid regex
      }
    }
    return true;
  });
  return normalizeSpacing(filtered.join("\n")).trim();
}

function applyPolitenessFix(text: string, words: string[]): string {
  if (!words.length) return text;
  const escaped = words.map((w) => w.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  const re = new RegExp(`(?<!\\w)(?:${escaped.join("|")})(?!\\w)`, "gi");
  let out = text.replace(re, "");

  const fragments = [
    /\b(?:for|to)\s+(?:your|the)\s+(?:help|time|effort|assistance|consideration)\s*[.!?]*/gi,
    /\b(?:i\s+would\s+appreciate|would\s+appreciate)\s*[.!?]*/gi,
    /\b(?:be\s+so\s+kind\s+as\s+to)\s*[.!?]*/gi,
    /\b(?:for)\s+(?:implementing|doing|creating|making|writing)\s+(?:this|that)\s*/gi,
    /\b(?:very\s+much|so\s+much)\s*[.!?,;:]*/gi,
  ];
  for (const frag of fragments) out = out.replace(frag, "");

  return normalizeSpacing(out).trim();
}

function fixRedundancy(text: string): string {
  const replacements: [RegExp, string][] = [
    [/\bin order to\b/gi, "to"],
    [/\bdue to the fact that\b/gi, "because"],
    [/\bat this point in time\b/gi, "now"],
    [/\bfor the purpose of\b/gi, "for"],
    [/\bin the event that\b/gi, "if"],
    [/\bprior to\b/gi, "before"],
    [/\bsubsequent to\b/gi, "after"],
  ];
  let out = text;
  for (const [re, repl] of replacements) out = out.replace(re, repl);
  return normalizeSpacing(out);
}

function applyStructureScaffold(text: string, requiredTags: string[]): string {
  if (!requiredTags.length) return text;
  const missing = requiredTags.filter(
    (tag) => !new RegExp(`<${escapeRe(tag)}\\b[^>]*>`, "i").test(text)
  );
  if (!missing.length) return text;

  const outLines: string[] = [];
  const lowerText = text.toLowerCase();
  let contentWrapped = false;

  for (const tag of missing) {
    if (tag.toLowerCase() === "task" && !contentWrapped) {
      outLines.push(`<task>${text.trim()}</task>`);
      contentWrapped = true;
    } else if (tag.toLowerCase() === "context" && lowerText.includes("context")) {
      outLines.push("<context></context>");
    } else if (tag.toLowerCase() === "output_format" && lowerText.includes("output")) {
      outLines.push("<output_format></output_format>");
    } else {
      outLines.push(`<${tag}></${tag}>`);
    }
  }

  if (!contentWrapped) {
    const scaffold = outLines.join("\n");
    return scaffold ? `${scaffold}\n\n${text.trim()}` : text;
  }
  return outLines.join("\n");
}

function normalizeSpacing(text: string): string {
  let out = text.replace(/[ \t]{2,}/g, " ");
  out = out.replace(/\n{3,}/g, "\n\n");
  return out;
}

function escapeRe(s: string): string {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}

// ── Prompt health score ──────────────────────────────────────────────────

const SECURITY_RULES = new Set([
  "prompt-injection", "jailbreak-pattern", "pii-in-prompt",
  "secret-in-prompt", "context-injection-boundary",
]);
const COST_RULES = new Set(["cost", "cost-limit", "politeness-bloat"]);
const COMPLETENESS_RULES = new Set([
  "completeness-edge-cases", "role-clarity", "output-format-missing",
  "hallucination-risk", "specificity-examples", "specificity-constraints",
]);
const QUALITY_RULES = new Set([
  "clarity-vague-terms", "verbosity-sentence-length", "verbosity-redundancy",
  "actionability-weak-verbs", "consistency-terminology", "structure-sections",
]);

function catScore(
  findings: Finding[],
  criticalW = 25, warnW = 10, infoW = 3,
  criticalCap = 100, warnCap = 30, infoCap = 15,
): number {
  const crit = findings.filter((f) => f.level === "CRITICAL").length;
  const warn = findings.filter((f) => f.level === "WARN").length;
  const info = findings.filter((f) => f.level === "INFO").length;
  const deduction =
    Math.min(crit * criticalW, criticalCap) +
    Math.min(warn * warnW, warnCap) +
    Math.min(info * infoW, infoCap);
  return Math.max(0, 100 - deduction);
}

export interface ScoreResult {
  overall: number;
  grade: string;
  categories: { security: number; cost: number; quality: number; completeness: number };
}

export function computeScore(results: Finding[]): ScoreResult {
  const sec = results.filter((r) => SECURITY_RULES.has(r.rule));
  const cost = results.filter((r) => COST_RULES.has(r.rule));
  const comp = results.filter((r) => COMPLETENESS_RULES.has(r.rule));
  const qual = results.filter((r) => QUALITY_RULES.has(r.rule));

  const secScore = catScore(sec, 25, 10, 3, 50, 30, 15);
  const costScore = catScore(cost, 25, 10, 3, 100, 30, 15);
  const qualScore = catScore(qual, 25, 8, 3, 100, 30, 15);
  const compScore = catScore(comp, 25, 10, 3, 100, 30, 15);

  const overall = Math.round(
    secScore * 0.40 + costScore * 0.20 + qualScore * 0.25 + compScore * 0.15,
  );

  const grade =
    overall >= 90 ? "A" :
    overall >= 75 ? "B" :
    overall >= 60 ? "C" :
    overall >= 45 ? "D" : "F";

  return {
    overall,
    grade,
    categories: { security: secScore, cost: costScore, quality: qualScore, completeness: compScore },
  };
}

// ── Public API (programmatic use) ────────────────────────────────────────

export { loadConfig } from "./config";
export { countTokens } from "./rules/cost";
