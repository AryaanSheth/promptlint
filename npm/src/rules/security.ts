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
  // Collapse zero-width chars
  let out = text.replace(ZERO_WIDTH, "");
  // Apply leet substitutions
  out = out.replace(/[013457@$!(|+]/g, (ch) => LEET_MAP[ch] ?? ch);
  // Collapse repeated characters (aaa -> a)
  out = out.replace(/(.)\1{2,}/g, "$1");
  return out;
}

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
      // invalid regex in config — skip
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
      break; // one injection finding is enough
    }
  }

  return results;
}
