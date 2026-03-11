import * as vscode from "vscode";
import { execFile } from "child_process";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";

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
        regionStart = i + 2; // 1-based line of the first content line (line after marker)
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

export async function lintText(pythonPath: string, text: string, configPath?: string): Promise<LintResult> {
  const tmpFile = path.join(os.tmpdir(), `promptlint_${Date.now()}_${Math.random().toString(36).slice(2)}.txt`);
  fs.writeFileSync(tmpFile, text, { encoding: "utf8" });
  const args = ["-m", "promptlint", "-f", tmpFile, "--format", "json", "--show-dashboard"];
  if (configPath) {
    args.push("--config", configPath);
  }
  return new Promise<LintResult>((resolve, reject) => {
    execFile(pythonPath, args, { maxBuffer: 5 * 1024 * 1024 }, (err, stdout, stderr) => {
      // The CLI may exit with non-zero codes but still emit JSON on stdout; try to parse regardless
      try {
        const data = stdout || "{}";
        const parsed = JSON.parse(data) as LintResult;
        resolve(parsed);
      } catch (e) {
        // If parsing fails, reject
        reject(e);
      } finally {
        try { fs.unlinkSync(tmpFile); } catch {}
      }
    });
  });
}

export async function lintDocument(document: vscode.TextDocument, pythonPath: string, configPath?: string): Promise<{ diagnostics: vscode.Diagnostic[], dashboard?: any }> {
  const fullText = document.getText();
  const regions = extractRegions(fullText);
  const diagnostics: vscode.Diagnostic[] = [];
  let lastDashboard: any = undefined;
  if (regions.length === 0) {
    try {
      const res = await lintText(pythonPath, fullText, configPath);
      lastDashboard = res.dashboard;
      res.findings.forEach((f) => {
        const line = typeof f.line === "number" ? f.line - 1 : 0;
        const range = new vscode.Range(line, 0, line, document.lineAt(line).text.length);
        const diag = new vscode.Diagnostic(range, f.message, mapSeverity(f.level));
        diag.code = f.rule;
        diag.source = "promptlint";
        diagnostics.push(diag);
      });
    } catch (e) {
      // If CLI failed entirely, emit a generic diagnostic on the first line
      const line = 0;
      const range = new vscode.Range(line, 0, line, document.lineAt(line).text.length);
      const msg = e instanceof Error ? e.message : "unknown error";
      diagnostics.push(new vscode.Diagnostic(range, `promptlint failed: ${msg}`, vscode.DiagnosticSeverity.Error));
    }
  } else {
    for (const region of regions) {
      try {
        const stripped = stripCodeWrapper(region.content);
        const res = await lintText(pythonPath, stripped.promptText, configPath);
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
      } catch (e) {
        // ignore region if linting fails for it
      }
    }
  }
  return { diagnostics, dashboard: lastDashboard };
}
