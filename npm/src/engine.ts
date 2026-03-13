import type { PromptlintConfig } from "./config";
import { checkTokens, countTokens } from "./rules/cost";
import type { Finding } from "./rules/cost";
import { checkInjection } from "./rules/security";
import {
  checkStructure,
  checkClarity,
  checkSpecificity,
  checkVerbosity,
  checkActionability,
  checkConsistency,
  checkCompleteness,
} from "./rules/quality";
import { lineNumber, lineContext } from "./rules/utils";

export type { Finding };

export function analyze(text: string, config: PromptlintConfig): Finding[] {
  const results: Finding[] = [];

  results.push(...checkTokens(text, config));
  results.push(...checkStructure(text, config));
  results.push(...checkInjection(text, config));
  results.push(...checkClarity(text, config));
  results.push(...checkSpecificity(text, config));
  results.push(...checkVerbosity(text, config));
  results.push(...checkActionability(text, config));
  results.push(...checkConsistency(text, config));
  results.push(...checkCompleteness(text, config));
  results.push(...checkPoliteness(text, config));

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

// ── Public API (programmatic use) ────────────────────────────────────────

export { loadConfig } from "./config";
export { countTokens } from "./rules/cost";
