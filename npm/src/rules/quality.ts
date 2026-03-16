import type { PromptlintConfig } from "../config";
import type { Finding } from "./cost";
import { preview, lineNumber, lineContext } from "./utils";

export function checkStructure(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["structure-sections"] ?? true)) return [];

  const hasXmlTags = /<\w+>/.test(text);
  const hasHeadings = /(?:^|\n)(?:Task|Context|Output|Goal|Requirements|Instructions):\s/im.test(text);
  const hasMarkdownHeaders = /(?:^|\n)#{1,6}\s+\w+/.test(text);
  const hasJsonStructure =
    (text.includes("{") || text.includes("[")) &&
    (text.includes("}") || text.includes("]")) &&
    (text.includes('"') || text.includes("'"));
  const hasDelimiters = /```|^---\s*$/m.test(text);
  const hasNumberedSections = /(?:^|\n)\d+\.\s+\w+/.test(text);

  if (hasXmlTags || hasHeadings || hasMarkdownHeaders || hasJsonStructure || hasDelimiters || hasNumberedSections) {
    return [];
  }

  return [
    {
      level: "WARN",
      rule: "structure-sections",
      message: "No explicit sections detected (Task/Context/Output).",
      line: "-",
      context: preview(text, config.previewLength),
    },
    {
      level: "INFO",
      rule: "structure-recommendations",
      message: "Recommended templates: headings (Task:, Context:, Output:) / XML tags (<task>) / Markdown (## sections).",
      line: "-",
      context: preview(text, config.previewLength),
    },
  ];
}

// Bug 1.3: Tightened vague-term patterns — removed good/bad/nice/better/best,
// appropriate/suitable/relevant/proper which caused high false-positive rates.
export function checkClarity(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["clarity-vague-terms"] ?? true)) return [];

  const vaguePatterns: [RegExp, string][] = [
    [/\b(some|several|various|many|few)\b/gi, "vague quantifier — specify a number or range"],
    [/\b(stuff|things|etc|and so on|and more)\b/gi, "trailing vague catch-all — enumerate explicitly"],
    [/\b(somehow|somewhere|sometime)\b/gi, "unspecified manner/place/time"],
    [/\bmaybe\b(?!\s+(?:null|undefined|none|empty))/gi, "uncertain language in an instruction context"],
  ];

  const results: Finding[] = [];
  for (const [re, issueType] of vaguePatterns) {
    let m: RegExpExecArray | null;
    re.lastIndex = 0;
    while ((m = re.exec(text)) !== null) {
      results.push({
        level: "WARN",
        rule: "clarity-vague-terms",
        message: `Vague term '${m[0]}' detected (${issueType}). Be more specific.`,
        line: lineNumber(text, m.index),
        context: lineContext(text, m.index, config.contextWidth),
        savings: 2.0,
      });
    }
  }
  return results;
}

export function checkSpecificity(text: string, config: PromptlintConfig): Finding[] {
  const results: Finding[] = [];

  if (config.enabledRules["specificity-examples"] ?? true) {
    const hasInstruction = /\b(write|create|generate|build|implement|design)\b/i.test(text);
    const hasExample = /\b(example|e\.g\.|such as|like|for instance)\b/i.test(text);
    if (hasInstruction && !hasExample && text.length > 100) {
      results.push({
        level: "INFO",
        rule: "specificity-examples",
        message: "Consider adding examples to clarify expected output format.",
        line: "-",
        context: preview(text, config.previewLength),
      });
    }
  }

  if (config.enabledRules["specificity-constraints"] ?? true) {
    const hasTask = /\b(write|create|generate|list|explain)\b/i.test(text);
    const hasConstraint = /\b(must|should|limit|maximum|minimum|between|exactly|only)\b/i.test(text);
    if (hasTask && !hasConstraint && text.length > 80) {
      results.push({
        level: "INFO",
        rule: "specificity-constraints",
        message: "Consider adding constraints (length, format, scope) for clearer results.",
        line: "-",
        context: preview(text, config.previewLength),
      });
    }
  }

  return results;
}

// Bug 1.4: Smarter sentence splitting avoiding abbreviations (e.g., i.e., decimals).
// Bug 1.7: Expanded redundancy patterns (7 → 41).
export function checkVerbosity(text: string, config: PromptlintConfig): Finding[] {
  const results: Finding[] = [];

  if (config.enabledRules["verbosity-sentence-length"] ?? true) {
    // Split on sentence-ending punctuation followed by whitespace+capital,
    // avoiding splits on abbreviations (e.g., v1.0, decimals, Mr. etc.)
    const sentences = text.split(/(?<=[^A-Z\d][.!?])\s+(?=[A-Z])|(?<=[.!?]{2})\s+/);
    for (const sentence of sentences) {
      const words = sentence.trim().split(/\s+/).filter(Boolean);
      if (words.length > 40) {
        results.push({
          level: "INFO",
          rule: "verbosity-sentence-length",
          message: `Long sentence detected (${words.length} words). Consider breaking it up.`,
          line: "-",
          context: preview(sentence.trim(), config.previewLength),
          savings: 3.0,
        });
      }
    }
  }

  if (config.enabledRules["verbosity-redundancy"] ?? true) {
    const redundantPatterns: RegExp[] = [
      /\bin order to\b/gi,
      /\bdue to the fact that\b/gi,
      /\bat this point in time\b/gi,
      /\bfor the purpose of\b/gi,
      /\bin the event that\b/gi,
      /\bprior to\b/gi,
      /\bsubsequent to\b/gi,
      /\ba total of\b/gi,
      /\beach and every\b/gi,
      /\bfirst and foremost\b/gi,
      /\bfuture plans\b/gi,
      /\bpast history\b/gi,
      /\bend result\b/gi,
      /\bbasic fundamentals\b/gi,
      /\bclose proximity\b/gi,
      /\bgather together\b/gi,
      /\bjoin together\b/gi,
      /\brefer back\b/gi,
      /\breturn back\b/gi,
      /\bunexpected surprise\b/gi,
      /\bcompletely eliminate\b/gi,
      /\bcompletely finished\b/gi,
      /\badvance planning\b/gi,
      /\bpast experience\b/gi,
      /\bnew innovation\b/gi,
      /\bpersonal opinion\b/gi,
      /\brepeat again\b/gi,
      /\bstill remains\b/gi,
      /\btrue fact\b/gi,
      /\bwith the exception of\b/gi,
      /\bin close proximity to\b/gi,
      /\bhas the ability to\b/gi,
      /\bis able to\b/gi,
      /\bin spite of the fact that\b/gi,
      /\bwith regard to\b/gi,
      /\bin relation to\b/gi,
      /\bfor the reason that\b/gi,
      /\bin the near future\b/gi,
      /\bat the present time\b/gi,
      /\buntil such time as\b/gi,
      /\bon a (?:daily|weekly|monthly) basis\b/gi,
    ];
    for (const re of redundantPatterns) {
      re.lastIndex = 0;
      const m = re.exec(text);
      if (m) {
        results.push({
          level: "INFO",
          rule: "verbosity-redundancy",
          message: `Redundant phrase '${m[0]}' detected. Use simpler alternative.`,
          line: lineNumber(text, m.index),
          context: lineContext(text, m.index, config.contextWidth),
          savings: 2.0,
        });
      }
    }
  }

  return results;
}

// Bug 1.5: Add real weak-verb detection; raise passive threshold from 3 to 5.
const WEAK_VERB_PATTERNS: [RegExp, string][] = [
  [/\b(consider|try to|attempt to|endeavor to)\b/gi, "weak directive — use imperative form"],
  [/\byou might want to\b/gi, "hedged instruction — use direct imperative"],
  [/\bfeel free to\b/gi, "unnecessary hedge — remove"],
  [/\bit would be (?:good|nice|helpful|great) (?:if|to)\b/gi, "indirect instruction — state directly"],
  [/\bif possible\b/gi, "conditional hedge — commit to the instruction"],
  [/\bwhenever (?:possible|you can)\b/gi, "weak conditional — use 'always' or state the condition explicitly"],
];

export function checkActionability(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["actionability-weak-verbs"] ?? true)) return [];

  const results: Finding[] = [];

  for (const [re, issueType] of WEAK_VERB_PATTERNS) {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(text)) !== null) {
      results.push({
        level: "INFO",
        rule: "actionability-weak-verbs",
        message: `Weak directive '${m[0]}' (${issueType}).`,
        line: lineNumber(text, m.index),
        context: lineContext(text, m.index, config.contextWidth),
      });
    }
  }

  const passiveRe = /\b(is|are|was|were|be|been|being)\s+\w+ed\b/gi;
  const passiveMatches = [...text.matchAll(passiveRe)];
  if (passiveMatches.length > 5) {
    results.push({
      level: "INFO",
      rule: "actionability-weak-verbs",
      message: `Multiple passive voice constructions (${passiveMatches.length}) detected. Use active voice for clarity.`,
      line: "-",
      context: preview(text, config.previewLength),
    });
  }
  return results;
}

// Bug 1.6: Expanded from 3 to 12 built-in term pairs; custom_term_pairs support.
const BUILTIN_TERM_PAIRS: [RegExp, RegExp][] = [
  [/\buser\b/i, /\bcustomer\b/i],
  [/\bfunction\b/i, /\bmethod\b/i],
  [/\berror\b/i, /\bexception\b/i],
  [/\bAI\b/, /\bmodel\b/i],
  [/\bLLM\b/, /\bmodel\b/i],
  [/\bquery\b/i, /\brequest\b/i],
  [/\bresponse\b/i, /\breply\b/i],
  [/\boutput\b/i, /\bresult\b/i],
  [/\bprompt\b/i, /\bmessage\b/i],
  [/\bsystem prompt\b/i, /\binstruction\b/i],
  [/\btask\b/i, /\bgoal\b/i],
  [/\bagent\b/i, /\bassistant\b/i],
];

export function checkConsistency(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["consistency-terminology"] ?? true)) return [];

  const results: Finding[] = [];

  function checkPair(re1: RegExp, re2: RegExp): void {
    const m1 = re1.exec(text);
    const m2 = re2.exec(text);
    if (m1 && m2) {
      results.push({
        level: "INFO",
        rule: "consistency-terminology",
        message: `Mixed terminology: '${m1[0]}' and '${m2[0]}'. Use one term consistently.`,
        line: "-",
        context: preview(text, config.previewLength),
      });
    }
  }

  for (const [re1, re2] of BUILTIN_TERM_PAIRS) {
    checkPair(re1, re2);
  }

  for (const group of (config.customTermPairs ?? [])) {
    for (let i = 0; i < group.length; i++) {
      for (let j = i + 1; j < group.length; j++) {
        const esc = (s: string) => s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
        checkPair(new RegExp(`\\b${esc(group[i])}\\b`, "i"), new RegExp(`\\b${esc(group[j])}\\b`, "i"));
      }
    }
  }

  return results;
}

export function checkCompleteness(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["completeness-edge-cases"] ?? true)) return [];

  const hasTask = /\b(write|create|implement|build|generate)\b/i.test(text);
  const hasEdgeCases = /\b(edge case|error|exception|invalid|empty|null|missing)\b/i.test(text);
  if (hasTask && !hasEdgeCases && text.length > 100) {
    return [{
      level: "INFO",
      rule: "completeness-edge-cases",
      message: "Consider specifying how to handle edge cases and errors.",
      line: "-",
      context: preview(text, config.previewLength),
    }];
  }
  return [];
}

// ── Rule 2.2: Role clarity ─────────────────────────────────────────────────

export function checkRoleClarity(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["role-clarity"] ?? true)) return [];
  if (text.split(/\s+/).length < 30) return [];

  const isInstructional = /\b(you|your|respond|answer|help|assist|always|never|must|should)\b/i.test(text);
  if (!isInstructional) return [];

  const hasRole = /\b(you are|you're|act as|your role is|you will serve as|you are a|you are an|you work as|your job is|your task is|you are responsible for|you specialize in)\b/i.test(text);
  if (!hasRole) {
    return [{
      level: "WARN",
      rule: "role-clarity",
      message: "No role or persona defined. Add 'You are a [role]...' to improve output consistency.",
      line: "-",
      context: preview(text, config.previewLength),
    }];
  }
  return [];
}

// ── Rule 2.3: Output format missing ───────────────────────────────────────

const OUTPUT_INSTRUCTION_VERBS = /\b(list|extract|find|return|give me|provide|output|generate|create|show|summarize|identify|enumerate)\b/i;
const OUTPUT_FORMAT_KEYWORDS = /\b(JSON|XML|CSV|markdown|bullet|numbered|table|plain text|HTML|YAML|format:|return as|output as|structured as|schema)\b/i;

export function checkOutputFormat(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["output-format-missing"] ?? true)) return [];
  if (text.length < 60) return [];

  if (OUTPUT_INSTRUCTION_VERBS.test(text) && !OUTPUT_FORMAT_KEYWORDS.test(text)) {
    return [{
      level: "WARN",
      rule: "output-format-missing",
      message: "Output instruction detected but no format specified (JSON, markdown, bullet list, etc.). Unspecified format produces inconsistent results.",
      line: "-",
      context: preview(text, config.previewLength),
    }];
  }
  return [];
}

// ── Rule 2.6: Hallucination risk ──────────────────────────────────────────

const FACTUAL_PATTERNS = [
  /\b(what is|what are|who is|who are|when did|when was|where is|how many|how much)\b/i,
  /\b(current(ly)?|latest|recent(ly)?|today|now|as of|up to date)\b/i,
  /\b(tell me about|give me (?:the|a) (?:list|summary|overview) of)\b/i,
];

const GROUNDING_PATTERNS = [
  /\{[\w\s]+\}/,
  /<context>/i,
  /Context:/i,
  /```/,
  /Given the following/i,
  /Based on the (?:following|above|provided)/i,
  /Using the (?:data|information|context|text) (?:below|above|provided)/i,
];

export function checkHallucinationRisk(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["hallucination-risk"] ?? true)) return [];

  const hasFactual = FACTUAL_PATTERNS.some((re) => re.test(text));
  const hasGrounding = GROUNDING_PATTERNS.some((re) => re.test(text));

  if (hasFactual && !hasGrounding) {
    return [{
      level: "WARN",
      rule: "hallucination-risk",
      message: "Prompt requests factual/current information without grounding context. Consider adding a {context} variable or <context> section with source data.",
      line: "-",
      context: preview(text, config.previewLength),
    }];
  }
  return [];
}
