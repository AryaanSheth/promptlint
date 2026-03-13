import type { PromptlintConfig } from "../config";
import { preview } from "./utils";

export interface Finding {
  level: "INFO" | "WARN" | "CRITICAL";
  rule: string;
  message: string;
  line: number | "-";
  context: string;
  tokens?: number;
  cost_per_call?: number;
  annual_cost?: number;
  savings?: number;
}

/** Approximate token count: chars / 4 is a standard heuristic. */
export function countTokens(text: string): number {
  return Math.ceil(text.length / 4);
}

export function checkTokens(text: string, config: PromptlintConfig): Finding[] {
  const costEnabled = config.enabledRules["cost"] ?? true;
  const limitEnabled = config.enabledRules["cost-limit"] ?? true;
  if (!costEnabled && !limitEnabled) return [];

  const tokens = countTokens(text);
  const costPerCall = (tokens / 1000) * config.costPer1kTokens;
  const annualCost = costPerCall * config.callsPerDay * 365;

  const results: Finding[] = [];

  if (costEnabled) {
    let message = `Prompt is ~${tokens} tokens (~$${costPerCall.toFixed(4)} input per call on ${config.model}).`;
    if (config.callsPerDay < 100_000) {
      const dailyCost = costPerCall * config.callsPerDay;
      message += `\nAt ${config.callsPerDay.toLocaleString()} calls/day -> ~$${dailyCost.toFixed(2)}/day input.`;
    }
    results.push({
      level: "INFO",
      rule: "cost",
      message,
      tokens,
      cost_per_call: costPerCall,
      annual_cost: annualCost,
      line: "-",
      context: preview(text, config.previewLength),
    });
  }

  if (limitEnabled && tokens > config.tokenLimit) {
    const overBy = tokens - config.tokenLimit;
    results.push({
      level: "WARN",
      rule: "cost-limit",
      message: `Prompt exceeds token limit by ${overBy} tokens (${tokens} > ${config.tokenLimit}).`,
      tokens,
      line: "-",
      context: preview(text, config.previewLength),
    });
  }

  return results;
}
