import * as vscode from "vscode";
import { analyze, applyFixes, loadConfig } from "promptlint-cli";
import type { Finding } from "promptlint-cli";

export type LintLevel = "INFO" | "WARN" | "CRITICAL";

export interface LintFinding {
  level: LintLevel;
  rule: string;
  message: string;
  line: number | "-";
  context?: string;
  savings?: number;
}

export interface LintResult {
  findings: LintFinding[];
  optimized_prompt?: string;
  dashboard?: {
    current_tokens: number;
    optimized_tokens: number;
    tokens_saved: number;
    reduction_percentage: number;
    savings_per_call: number;
    monthly_savings?: number;
    annual_savings?: number;
    calls_per_day?: number;
  };
}

export interface Region {
  startLine: number;
  endLine: number;
  content: string;
}

export interface StrippedRegion {
  promptText: string;
  headerLineCount: number;
  footerLineCount: number;
}

const OPEN_WRAPPER_RE =
  /^\s*(?:(?:export\s+)?(?:const|let|var)\s+\w+\s*[:=]\s*|[\w]+\s*=\s*)?f?(?:"""|'''|`)\s*$/;
const CLOSE_WRAPPER_RE = /^\s*(?:"""|'''|`);?\s*$/;

export function stripCodeWrapper(content: string): StrippedRegion {
  const lines = content.split(/\r?\n/);
  let headerLineCount = 0;
  let footerLineCount = 0;

  if (lines.length > 0 && OPEN_WRAPPER_RE.test(lines[0])) {
    headerLineCount = 1;
  }

  const lastIdx = lines.length - 1;
  if (lastIdx > headerLineCount && CLOSE_WRAPPER_RE.test(lines[lastIdx])) {
    footerLineCount = 1;
  }

  const promptLines = lines.slice(
    headerLineCount,
    lines.length - footerLineCount
  );
  return {
    promptText: promptLines.join("\n"),
    headerLineCount,
    footerLineCount,
  };
}

function mapSeverity(level: LintLevel): vscode.DiagnosticSeverity {
  switch (level) {
    case "CRITICAL":
      return vscode.DiagnosticSeverity.Error;
    case "WARN":
      return vscode.DiagnosticSeverity.Warning;
    case "INFO":
    default:
      return vscode.DiagnosticSeverity.Information;
  }
}

export function extractRegions(text: string): Region[] {
  const lines = text.split(/\r?\n/);
  const regions: Region[] = [];
  let inRegion = false;
  let regionStart = 0;
  let buffer: string[] = [];
  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    if (!inRegion) {
      if (/promptlint-start/.test(line)) {
        inRegion = true;
        regionStart = i + 2;
        buffer = [];
      }
      continue;
    } else {
      if (/promptlint-end/.test(line)) {
        inRegion = false;
        const regionContent = buffer.join("\n");
        regions.push({ startLine: regionStart, endLine: i + 1, content: regionContent });
      } else {
        buffer.push(line);
      }
    }
  }
  return regions;
}

function buildDashboard(
  findings: Finding[],
  config: ReturnType<typeof loadConfig>
): LintResult["dashboard"] {
  const costFinding = findings.find((f) => f.rule === "cost");
  if (!costFinding?.tokens) return undefined;

  const currentTokens = costFinding.tokens;
  const totalSavingsTokens = findings.reduce(
    (sum, f) => sum + (f.savings ?? 0),
    0
  );
  const optimizedTokens = Math.max(currentTokens - totalSavingsTokens, 0);
  const tokensSaved = currentTokens - optimizedTokens;
  const reductionPct =
    currentTokens > 0
      ? Math.round((tokensSaved / currentTokens) * 1000) / 10
      : 0;
  const savingsPerCall = (tokensSaved / 1000) * config.costPer1kTokens;
  const monthlySavings = savingsPerCall * config.callsPerDay * 30;
  const annualSavings = savingsPerCall * config.callsPerDay * 365;

  return {
    current_tokens: currentTokens,
    optimized_tokens: optimizedTokens,
    tokens_saved: tokensSaved,
    reduction_percentage: reductionPct,
    savings_per_call: Math.round(savingsPerCall * 10000) / 10000,
    monthly_savings: Math.round(monthlySavings * 100) / 100,
    annual_savings: Math.round(annualSavings * 100) / 100,
    calls_per_day: config.callsPerDay,
  };
}

export function lintText(text: string, configPath?: string): LintResult {
  const config = loadConfig(configPath);
  const findings = analyze(text, config);
  const dashboard = buildDashboard(findings, config);
  return { findings: findings as LintFinding[], dashboard };
}

export function fixText(text: string, configPath?: string): string {
  const config = loadConfig(configPath);
  return applyFixes(text, config);
}

export async function lintDocument(
  document: vscode.TextDocument,
  configPath?: string
): Promise<{ diagnostics: vscode.Diagnostic[]; dashboard?: LintResult["dashboard"] }> {
  const fullText = document.getText();
  const regions = extractRegions(fullText);
  const diagnostics: vscode.Diagnostic[] = [];
  let lastDashboard: LintResult["dashboard"] = undefined;

  if (regions.length === 0) {
    try {
      const res = lintText(fullText, configPath);
      lastDashboard = res.dashboard;
      res.findings.forEach((f) => {
        const line = typeof f.line === "number" ? f.line - 1 : 0;
        const safeLine = Math.max(0, Math.min(line, document.lineCount - 1));
        const range = new vscode.Range(
          safeLine, 0, safeLine, document.lineAt(safeLine).text.length
        );
        const diag = new vscode.Diagnostic(range, f.message, mapSeverity(f.level));
        diag.code = f.rule;
        diag.source = "promptlint";
        diagnostics.push(diag);
      });
    } catch (e) {
      const msg = e instanceof Error ? e.message : "unknown error";
      diagnostics.push(
        new vscode.Diagnostic(
          new vscode.Range(0, 0, 0, document.lineAt(0).text.length),
          `promptlint failed: ${msg}`,
          vscode.DiagnosticSeverity.Error
        )
      );
    }
  } else {
    for (const region of regions) {
      try {
        const stripped = stripCodeWrapper(region.content);
        const res = lintText(stripped.promptText, configPath);
        lastDashboard = res.dashboard || lastDashboard;
        for (const f of res.findings) {
          const rel = typeof f.line === "number" ? (f.line as number) - 1 : 0;
          const line = region.startLine - 1 + stripped.headerLineCount + rel;
          if (line >= document.lineCount) continue;
          const lineText = document.lineAt(line).text;
          const range = new vscode.Range(line, 0, line, lineText.length);
          const diag = new vscode.Diagnostic(range, f.message, mapSeverity(f.level));
          diag.code = f.rule;
          diag.source = "promptlint";
          diagnostics.push(diag);
        }
      } catch {
        // ignore region if linting fails
      }
    }
  }

  return { diagnostics, dashboard: lastDashboard };
}
