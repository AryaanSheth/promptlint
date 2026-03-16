import type { PromptlintConfig } from "../config";
import type { Finding } from "./cost";
import { lineNumber, lineContext } from "./utils";

const LEET_MAP: Record<string, string> = {
  "0": "o", "1": "i", "3": "e", "4": "a", "5": "s",
  "7": "t", "8": "b", "@": "a", $: "s", "!": "i",
  "(": "c", "|": "l", "+": "t",
};

const ZERO_WIDTH = /[\u200b\u200c\u200d\u2060\ufeff\u00ad\u034f\u180e]/g;

function normalizeForMatching(text: string): string {
  let out = text.replace(ZERO_WIDTH, "");
  out = out.replace(/[013457@$!(|+]/g, (ch) => LEET_MAP[ch] ?? ch);
  out = out.replace(/(.)\1{2,}/g, "$1");
  return out;
}

const TEMPLATE_VAR = /\{\{?[\w\s]+\}?\}/g;

function isInTemplateVar(text: string, start: number, end: number): boolean {
  let m: RegExpExecArray | null;
  TEMPLATE_VAR.lastIndex = 0;
  while ((m = TEMPLATE_VAR.exec(text)) !== null) {
    if (m.index <= start && end <= m.index + m[0].length) return true;
  }
  return false;
}

// ── Prompt injection ──────────────────────────────────────────────────────

export function checkInjection(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["prompt-injection"] ?? true)) return [];

  const normalized = normalizeForMatching(text.toLowerCase());
  const results: Finding[] = [];

  for (const pattern of config.injectionPatterns) {
    let match: RegExpExecArray | null = null;
    let obfuscated = false;

    try {
      const re = new RegExp(pattern, "i");
      match = re.exec(text);
      if (!match) {
        match = re.exec(normalized);
        obfuscated = match !== null;
      }
    } catch {
      continue;
    }

    if (match) {
      const safeIdx = Math.min(match.index, Math.max(text.length - 1, 0));
      const lineNum = text.length > 0 ? lineNumber(text, safeIdx) : 1;
      const ctx = text.length > 0 ? lineContext(text, safeIdx, config.contextWidth) : "";
      const msg = obfuscated
        ? `Obfuscated injection pattern detected: '${pattern}' (after normalizing leetspeak/unicode).`
        : `Injection pattern detected: '${pattern}'.`;

      results.push({
        level: "CRITICAL",
        rule: "prompt-injection",
        message: msg,
        line: lineNum,
        context: ctx,
      });
      // No break — collect all matching patterns (Bug 1.1 fix)
    }
  }

  return results;
}

// ── Jailbreak patterns ────────────────────────────────────────────────────

const DEFAULT_JAILBREAK_PATTERNS = [
  String.raw`\b(?:you are now|pretend you are|act as if you are)\b`,
  String.raw`\b(?:DAN|do anything now)\b`,
  String.raw`\b(?:ignore your|forget your|disregard your)\s+(?:training|guidelines|instructions|rules|restrictions)`,
  String.raw`\b(?:for a (?:story|book|novel|game|roleplay|hypothetical))\b`,
  String.raw`\bhypothetically(?:\s+speaking)?,?\s+(?:if|suppose|imagine)`,
  String.raw`\b(?:no restrictions|no limits|no rules|no filters|no guidelines)\b`,
  String.raw`\b(?:you have no|you don't have|you no longer have)\s+(?:restrictions|filters|guidelines|rules)`,
  String.raw`\bjailbreak\b`,
  String.raw`\b(?:developer mode|god mode|unrestricted mode|admin mode)\b`,
  String.raw`(?:ignore|forget|disregard)\s+(?:all\s+)?(?:previous|prior|above|earlier)\s+(?:instructions|prompts|context|conversation)`,
];

export function checkJailbreak(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["jailbreak-pattern"] ?? true)) return [];

  const normalized = normalizeForMatching(text.toLowerCase());
  const results: Finding[] = [];
  const patterns = [...DEFAULT_JAILBREAK_PATTERNS, ...(config.jailbreakPatterns ?? [])];

  for (const pattern of patterns) {
    let match: RegExpExecArray | null = null;
    let obfuscated = false;

    try {
      const re = new RegExp(pattern, "i");
      match = re.exec(text);
      if (!match) {
        match = re.exec(normalized);
        obfuscated = match !== null;
      }
    } catch {
      continue;
    }

    if (match) {
      const safeIdx = Math.min(match.index, Math.max(text.length - 1, 0));
      const msg = obfuscated
        ? `Obfuscated jailbreak pattern detected: '${pattern}' (after normalizing leetspeak/unicode).`
        : `Jailbreak pattern detected: '${pattern}'.`;

      results.push({
        level: "CRITICAL",
        rule: "jailbreak-pattern",
        message: msg,
        line: text.length > 0 ? lineNumber(text, safeIdx) : 1,
        context: text.length > 0 ? lineContext(text, safeIdx, config.contextWidth) : "",
      });
    }
  }

  return results;
}

// ── PII detection ─────────────────────────────────────────────────────────

const PII_PATTERNS: [string, RegExp, string][] = [
  ["email", /\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b/g, "email address"],
  ["ssn", /\b\d{3}[-.\s]?\d{2}[-.\s]?\d{4}\b/g, "SSN pattern"],
  ["phone", /\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b/g, "phone number"],
  ["credit_card", /\b4[0-9]{12}(?:[0-9]{3})?\b/g, "Visa card number pattern"],
  ["credit_card", /\b5[1-5][0-9]{14}\b/g, "Mastercard number pattern"],
  ["ip", /\b(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\.(?:25[0-5]|2[0-4]\d|[01]?\d\d?)\b/g, "IP address"],
];

export function checkPii(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["pii-in-prompt"] ?? true)) return [];

  const piiCfg = config.piiChecks ?? {};
  const results: Finding[] = [];

  for (const [piiType, re, label] of PII_PATTERNS) {
    const cfgKey = `check_${piiType}`;
    if (piiCfg[cfgKey] === false) continue;

    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(text)) !== null) {
      if (isInTemplateVar(text, m.index, m.index + m[0].length)) continue;
      results.push({
        level: "WARN",
        rule: "pii-in-prompt",
        message: `Possible ${label} detected. Remove or replace with a template variable.`,
        line: lineNumber(text, m.index),
        context: lineContext(text, m.index, config.contextWidth),
      });
    }
  }

  return results;
}

// ── Secret / credential detection ────────────────────────────────────────

const SECRET_PATTERNS: [RegExp, string][] = [
  [/\bsk-[A-Za-z0-9]{20,}\b/g, "OpenAI API key"],
  [/\bsk-proj-[A-Za-z0-9]{20,}\b/g, "OpenAI project API key"],
  [/\bsk-ant-[A-Za-z0-9]{20,}\b/g, "Anthropic API key"],
  [/\bAIza[0-9A-Za-z_-]{35}\b/g, "Google API key"],
  [/\bghp_[A-Za-z0-9]{36}\b/g, "GitHub personal access token"],
  [/\bgho_[A-Za-z0-9]{36}\b/g, "GitHub OAuth token"],
  [/\bBearer\s+[A-Za-z0-9\-._~+/]+=*\b/g, "Bearer token"],
  [/\bapi[_-]?key\s*[:=]\s*['"]?[A-Za-z0-9\-._]{16,}['"]?/gi, "generic API key assignment"],
  [/\bpassword\s*[:=]\s*['"]?[^\s'"]{8,}['"]?/gi, "hardcoded password"],
  [/\b[A-Fa-f0-9]{32}\b/g, "MD5 hash / potential token"],
  [/\b[A-Fa-f0-9]{40}\b/g, "SHA1 / potential token"],
  [/\b[A-Fa-f0-9]{64}\b/g, "SHA256 / potential token"],
];

export function checkSecrets(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["secret-in-prompt"] ?? true)) return [];

  const results: Finding[] = [];

  for (const [re, label] of SECRET_PATTERNS) {
    re.lastIndex = 0;
    let m: RegExpExecArray | null;
    while ((m = re.exec(text)) !== null) {
      if (isInTemplateVar(text, m.index, m.index + m[0].length)) continue;
      results.push({
        level: "CRITICAL",
        rule: "secret-in-prompt",
        message: `Possible ${label} detected in prompt. Remove before committing.`,
        line: lineNumber(text, m.index),
        context: lineContext(text, m.index, config.contextWidth),
      });
    }
  }

  return results;
}

// ── Injection boundary check ──────────────────────────────────────────────

export function checkInjectionBoundary(text: string, config: PromptlintConfig): Finding[] {
  if (!(config.enabledRules["context-injection-boundary"] ?? true)) return [];

  const VAR_RE = /\{[\w\s]+\}|\{\{[\w\s]+\}\}/g;
  const results: Finding[] = [];
  let m: RegExpExecArray | null;

  VAR_RE.lastIndex = 0;
  while ((m = VAR_RE.exec(text)) !== null) {
    const varStart = m.index;
    const preceding = text.slice(0, varStart);
    const following = text.slice(varStart);

    const enclosedByXml =
      /<[\w_-]+>\s*$/.test(preceding) && /^\s*<\/[\w_-]+>/.test(following);
    const enclosedByFence =
      /```\w*\s*$/.test(preceding) && /^\s*```/.test(following);
    const precededByHeader =
      /(?:User Input|User Message|Input|Query):\s*$/i.test(preceding);

    if (!enclosedByXml && !enclosedByFence && !precededByHeader) {
      const lineNum = (text.slice(0, varStart).match(/\n/g) ?? []).length + 1;
      results.push({
        level: "WARN",
        rule: "context-injection-boundary",
        message: `Template variable '${m[0]}' is not enclosed by a structural delimiter. Wrap user input in XML tags or a labeled section to reduce injection risk.`,
        line: lineNum,
        context: lineContext(text, varStart, config.contextWidth),
      });
    }
  }

  return results;
}
