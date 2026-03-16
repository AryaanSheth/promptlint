import * as fs from "fs";
import * as path from "path";
import * as yaml from "js-yaml";

export interface PromptlintConfig {
  model: string;
  tokenLimit: number;
  costPer1kTokens: number;
  callsPerDay: number;
  previewLength: number;
  contextWidth: number;
  enabledRules: Record<string, boolean>;
  injectionPatterns: string[];
  jailbreakPatterns: string[];
  piiChecks: Record<string, boolean>;
  politenessWords: string[];
  allowPoliteness: boolean;
  politenessSavingsPerHit: number;
  requiredTags: string[];
  customTermPairs: string[][];
  ruleSeverityOverrides: Record<string, string>;
  fixEnabled: boolean;
  fixRules: Record<string, boolean>;
}

const DEFAULTS: PromptlintConfig = {
  model: "gpt-4o",
  tokenLimit: 800,
  costPer1kTokens: 0.005,
  callsPerDay: 1_000_000,
  previewLength: 60,
  contextWidth: 80,
  enabledRules: {
    "cost": true,
    "cost-limit": true,
    "structure-sections": true,
    "prompt-injection": true,
    "jailbreak-pattern": true,
    "pii-in-prompt": true,
    "secret-in-prompt": true,
    "context-injection-boundary": true,
    "politeness-bloat": true,
    "clarity-vague-terms": true,
    "specificity-examples": true,
    "specificity-constraints": true,
    "verbosity-sentence-length": true,
    "verbosity-redundancy": true,
    "actionability-weak-verbs": true,
    "consistency-terminology": true,
    "completeness-edge-cases": true,
    "role-clarity": true,
    "output-format-missing": true,
    "hallucination-risk": true,
  },
  injectionPatterns: [
    "ignore previous instructions",
    "ignore all previous",
    "disregard previous",
    "forget previous instructions",
    "system prompt extraction",
    "reveal your (system )?prompt",
    "you are now a [a-zA-Z ]+",
    "act as (a |an )?[a-zA-Z ]+",
    "pretend (to be|you are)",
    "jailbreak",
    "bypass (safety|security|restrictions)",
    "do anything now",
  ],
  jailbreakPatterns: [],
  piiChecks: {
    check_email: true,
    check_phone: true,
    check_ssn: true,
    check_credit_card: true,
    check_ip: false,
  },
  politenessWords: [
    "please",
    "kindly",
    "i would appreciate",
    "thank you",
    "be so kind as to",
    "if possible",
  ],
  allowPoliteness: false,
  politenessSavingsPerHit: 1.5,
  requiredTags: [],
  customTermPairs: [],
  ruleSeverityOverrides: {},
  fixEnabled: true,
  fixRules: {
    "prompt-injection": true,
    "politeness-bloat": true,
    "verbosity-redundancy": true,
    "structure-scaffold": true,
  },
};

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getRulesEnabled(raw: any): Record<string, boolean> {
  const out: Record<string, boolean> = { ...DEFAULTS.enabledRules };
  if (!raw?.rules || typeof raw.rules !== "object") return out;
  for (const [key, val] of Object.entries(raw.rules)) {
    const normalized = key.replace(/_/g, "-");
    if (typeof val === "boolean") {
      out[normalized] = val;
    } else if (val && typeof val === "object" && "enabled" in (val as object)) {
      out[normalized] = Boolean((val as Record<string, unknown>).enabled);
    }
  }
  return out;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getSeverityOverrides(raw: any): Record<string, string> {
  const out: Record<string, string> = {};
  if (!raw?.rules || typeof raw.rules !== "object") return out;
  const valid = new Set(["INFO", "WARN", "CRITICAL"]);
  for (const [key, val] of Object.entries(raw.rules)) {
    const normalized = key.replace(/_/g, "-");
    if (val && typeof val === "object" && "severity" in (val as object)) {
      const sev = String((val as Record<string, unknown>).severity).toUpperCase();
      if (valid.has(sev)) out[normalized] = sev;
    }
  }
  return out;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getCustomTermPairs(raw: any): string[][] {
  const section = raw?.rules?.consistency_terminology ?? raw?.rules?.["consistency-terminology"];
  if (!section?.custom_pairs || !Array.isArray(section.custom_pairs)) return [];
  const result: string[][] = [];
  for (const item of section.custom_pairs) {
    if (Array.isArray(item) && item.length >= 2) {
      const pair = item.map(String).filter((s) => s.trim());
      if (pair.length >= 2) result.push(pair);
    }
  }
  return result;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getPiiChecks(raw: any): Record<string, boolean> {
  const out = { ...DEFAULTS.piiChecks };
  const section = raw?.rules?.pii_in_prompt ?? raw?.rules?.["pii-in-prompt"];
  if (!section || typeof section !== "object") return out;
  for (const key of ["check_email", "check_phone", "check_ssn", "check_credit_card", "check_ip"]) {
    if (typeof section[key] === "boolean") out[key] = section[key];
  }
  return out;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getFixRules(raw: any): Record<string, boolean> {
  const out: Record<string, boolean> = { ...DEFAULTS.fixRules };
  if (!raw?.fix || typeof raw.fix !== "object") return out;
  for (const [key, val] of Object.entries(raw.fix)) {
    if (key === "enabled") continue;
    const normalized = key.replace(/_/g, "-");
    out[normalized] = Boolean(val);
  }
  return out;
}

export function loadConfig(configPath?: string): PromptlintConfig {
  const candidates = configPath
    ? [configPath]
    : [
        path.join(process.cwd(), ".promptlintrc"),
        path.join(process.cwd(), ".promptlintrc.yml"),
        path.join(process.cwd(), ".promptlintrc.yaml"),
      ];

  let raw: unknown = null;
  for (const p of candidates) {
    if (fs.existsSync(p)) {
      try {
        raw = yaml.load(fs.readFileSync(p, "utf8"));
      } catch {
        // invalid config — fall through to defaults
      }
      break;
    }
  }

  if (!raw || typeof raw !== "object") return { ...DEFAULTS };

  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const r = raw as any;

  const politenessSection = r.rules?.politeness_bloat ?? r.rules?.["politeness-bloat"] ?? {};
  const jailbreakSection = r.rules?.jailbreak_pattern ?? r.rules?.["jailbreak-pattern"] ?? {};

  return {
    model: r.model ?? DEFAULTS.model,
    tokenLimit: clamp(r.token_limit ?? DEFAULTS.tokenLimit, 1, 1_000_000),
    costPer1kTokens: clamp(r.cost_per_1k_tokens ?? DEFAULTS.costPer1kTokens, 0, 1000),
    callsPerDay: clamp(r.calls_per_day ?? DEFAULTS.callsPerDay, 1, 1_000_000_000),
    previewLength: r.display?.preview_length ?? DEFAULTS.previewLength,
    contextWidth: r.display?.context_width ?? DEFAULTS.contextWidth,
    enabledRules: getRulesEnabled(r),
    injectionPatterns:
      (r.rules?.prompt_injection?.patterns as string[] | undefined) ??
      (r.rules?.["prompt-injection"]?.patterns as string[] | undefined) ??
      DEFAULTS.injectionPatterns,
    jailbreakPatterns:
      (jailbreakSection.patterns as string[] | undefined) ?? DEFAULTS.jailbreakPatterns,
    piiChecks: getPiiChecks(r),
    politenessWords:
      (politenessSection.words as string[] | undefined) ?? DEFAULTS.politenessWords,
    allowPoliteness: politenessSection.allow_politeness ?? DEFAULTS.allowPoliteness,
    politenessSavingsPerHit:
      politenessSection.savings_per_hit ?? DEFAULTS.politenessSavingsPerHit,
    requiredTags:
      (r.rules?.structure_sections?.required_tags as string[] | undefined) ??
      (r.rules?.["structure-sections"]?.required_tags as string[] | undefined) ??
      DEFAULTS.requiredTags,
    customTermPairs: getCustomTermPairs(r),
    ruleSeverityOverrides: getSeverityOverrides(r),
    fixEnabled: r.fix?.enabled ?? DEFAULTS.fixEnabled,
    fixRules: getFixRules(r),
  };
}

function clamp(v: number, min: number, max: number): number {
  return Math.max(min, Math.min(max, v));
}

export const STARTER_CONFIG = `model: gpt-4o
token_limit: 800
cost_per_1k_tokens: 0.005
calls_per_day: 10000

display:
  preview_length: 60
  context_width: 80

rules:
  cost:
    enabled: true
  cost_limit:
    enabled: true
  prompt_injection:
    enabled: true
    patterns:
      - ignore previous instructions
      - system prompt extraction
      - "you are now a [a-zA-Z ]+"
  structure_sections:
    enabled: true
  clarity_vague_terms:
    enabled: true
  specificity_examples:
    enabled: true
  specificity_constraints:
    enabled: true
  politeness_bloat:
    enabled: true
    allow_politeness: false
    words:
      - please
      - kindly
      - i would appreciate
      - thank you
      - be so kind as to
      - if possible
    savings_per_hit: 1.5
  verbosity_sentence_length:
    enabled: true
  verbosity_redundancy:
    enabled: true
  actionability_weak_verbs:
    enabled: true
  consistency_terminology:
    enabled: true
  completeness_edge_cases:
    enabled: true
  role_clarity:
    enabled: true
  output_format_missing:
    enabled: true
  hallucination_risk:
    enabled: true
  jailbreak_pattern:
    enabled: true
  pii_in_prompt:
    enabled: true
  secret_in_prompt:
    enabled: true
  context_injection_boundary:
    enabled: true

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
`;
