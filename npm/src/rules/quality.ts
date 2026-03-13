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

export function checkClarity(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["clarity-vague-terms"] ?? true)) return [];

  const vaguePatterns: [RegExp, string][] = [
    [/\b(some|several|various|many|few|stuff|things|etc)\b/gi, "vague quantifier"],
    [/\b(maybe|perhaps|possibly|probably|might|could)\b/gi, "uncertain language"],
    [/\b(good|bad|nice|better|best)\b/gi, "subjective term without criteria"],
    [/\b(appropriate|suitable|relevant|proper)\b/gi, "undefined standard"],
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

export function checkVerbosity(text: string, config: PromptlintConfig): Finding[] {
  const results: Finding[] = [];

  if (config.enabledRules["verbosity-sentence-length"] ?? true) {
    const sentences = text.split(/[.!?]+/);
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

export function checkActionability(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["actionability-weak-verbs"] ?? true)) return [];

  const passiveRe = /\b(is|are|was|were|be|been|being)\s+\w+ed\b/gi;
  const matches = [...text.matchAll(passiveRe)];
  if (matches.length > 3) {
    return [{
      level: "INFO",
      rule: "actionability-weak-verbs",
      message: `Multiple passive voice constructions (${matches.length}) detected. Use active voice for clarity.`,
      line: "-",
      context: preview(text, config.previewLength),
    }];
  }
  return [];
}

export function checkConsistency(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["consistency-terminology"] ?? true)) return [];

  const mixedTerms: [RegExp, RegExp][] = [
    [/\buser\b/i, /\bcustomer\b/i],
    [/\bfunction\b/i, /\bmethod\b/i],
    [/\berror\b/i, /\bexception\b/i],
  ];

  const results: Finding[] = [];
  for (const [re1, re2] of mixedTerms) {
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
