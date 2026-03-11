import * as vscode from "vscode";
import * as fs from "fs";
import * as os from "os";
import * as path from "path";
import { execFile } from "child_process";
import { getConfig, PromptLintConfig } from "./config";
import { lintDocument, extractRegions, stripCodeWrapper } from "./linter";
import { StatusBarManager } from "./statusBar";
import { PromptLintCodeActionProvider } from "./codeActions";

let currentConfig: PromptLintConfig;

function refreshConfig(): PromptLintConfig {
  currentConfig = getConfig();
  return currentConfig;
}

function isInPromptsFolder(filePath: string): boolean {
  return /prompts[\\/]/i.test(filePath);
}

function shouldLintDocument(doc: vscode.TextDocument): boolean {
  const cfg = currentConfig;
  return (
    cfg.languages.includes(doc.languageId) ||
    isInPromptsFolder(doc.fileName) ||
    /\.(prompt|promptlint)$/i.test(doc.fileName)
  );
}

function createTempFile(text: string, suffix: string = ".txt"): string | null {
  const tmpFile = path.join(
    os.tmpdir(),
    `promptlint_${Date.now()}_${Math.random().toString(36).slice(2)}${suffix}`
  );
  try {
    fs.writeFileSync(tmpFile, text, { encoding: "utf8" });
    return tmpFile;
  } catch {
    return null;
  }
}

function runCli(
  args: string[],
  cwd?: string
): Promise<{ stdout: string; stderr: string }> {
  const pythonPath = currentConfig.pythonPath;
  return new Promise((resolve, reject) => {
    execFile(
      pythonPath,
      ["-m", "promptlint", ...args],
      { maxBuffer: 5 * 1024 * 1024, cwd },
      (err, stdout, stderr) => {
        if (err && err.code !== 1 && err.code !== 2) {
          return reject(err);
        }
        resolve({ stdout: stdout || "", stderr: stderr || "" });
      }
    );
  });
}

export function activate(context: vscode.ExtensionContext) {
  currentConfig = getConfig();

  const diagCollection =
    vscode.languages.createDiagnosticCollection("promptlint");
  context.subscriptions.push(diagCollection);

  const statusBar = new StatusBarManager();
  context.subscriptions.push(statusBar);

  // Re-read config whenever settings change
  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("promptlint")) {
        refreshConfig();
      }
    })
  );

  // Register code action provider for all configured languages
  const codeActionProvider = new PromptLintCodeActionProvider();
  for (const lang of currentConfig.languages) {
    context.subscriptions.push(
      vscode.languages.registerCodeActionsProvider(
        { language: lang },
        codeActionProvider,
        { providedCodeActionKinds: [vscode.CodeActionKind.QuickFix] }
      )
    );
  }

  // Check CLI availability on activation
  checkCLI();

  // --- Lint helpers ---

  async function lintDoc(doc: vscode.TextDocument) {
    const { diagnostics, dashboard } = await lintDocument(
      doc,
      currentConfig.pythonPath,
      currentConfig.configPath || undefined
    );
    diagCollection.set(doc.uri, diagnostics);
    if (dashboard) {
      statusBar.updateFromDashboard(dashboard);
    }
  }

  // Lint on save
  context.subscriptions.push(
    vscode.workspace.onDidSaveTextDocument((doc) => {
      if (!currentConfig.lintOnSave) return;
      if (!shouldLintDocument(doc)) return;
      lintDoc(doc).catch(() => {});
    })
  );

  // Lint on type (debounced)
  const typeDebounce = new Map<string, NodeJS.Timeout>();
  context.subscriptions.push(
    vscode.workspace.onDidChangeTextDocument((event) => {
      if (!currentConfig.lintOnType) return;
      const doc = event.document;
      if (!shouldLintDocument(doc)) return;
      const key = doc.uri.toString();
      const existing = typeDebounce.get(key);
      if (existing) clearTimeout(existing);
      const t = setTimeout(() => {
        typeDebounce.delete(key);
        lintDoc(doc).catch(() => {});
      }, currentConfig.lintOnTypeDelay);
      typeDebounce.set(key, t);
    })
  );

  // --- Commands ---

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.lint", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      await lintDoc(editor.document);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.fix", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      await applyFixToDocument(editor);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.fixAll", async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      await applyFixToDocument(editor);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "promptlint.applyFix",
      async (uri: vscode.Uri, range: vscode.Range, _rule: string) => {
        const doc = await vscode.workspace.openTextDocument(uri);
        const regionText = doc.getText(range);
        const tmpFile = createTempFile(regionText);
        if (!tmpFile) return;
        try {
          const { stdout } = await runCli([
            "-f",
            tmpFile,
            "--fix",
            "--format",
            "json",
          ]);
          const res = JSON.parse(stdout || "{}");
          if (res.optimized_prompt) {
            const wsEdit = new vscode.WorkspaceEdit();
            wsEdit.replace(uri, range, res.optimized_prompt);
            await vscode.workspace.applyEdit(wsEdit);
          }
        } catch {
          // silently ignore
        } finally {
          try {
            fs.unlinkSync(tmpFile);
          } catch {}
        }
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "promptlint.disableRule",
      async (uri: vscode.Uri, line: number, rule: string) => {
        const doc = await vscode.workspace.openTextDocument(uri);
        const editor = await vscode.window.showTextDocument(doc);
        const lineText = doc.lineAt(line).text;
        const marker = lineText.trimStart().startsWith("//") ? "//" : "#";
        const insertPos = new vscode.Position(line, lineText.length);
        await editor.edit((ed) => {
          ed.insert(insertPos, `  ${marker} promptlint-disable ${rule}`);
        });
      }
    )
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.dashboard", async () => {
      const editor = vscode.window.activeTextEditor;
      const out = vscode.window.createOutputChannel("PromptLint Dashboard");
      out.show(true);
      if (!editor) {
        out.appendLine("Open a prompt file and run lint first.");
        return;
      }
      const tmpFile = createTempFile(editor.document.getText());
      if (!tmpFile) return;
      try {
        const { stdout } = await runCli([
          "-f",
          tmpFile,
          "--format",
          "json",
          "--show-dashboard",
        ]);
        const res = JSON.parse(stdout || "{}");
        const d = res.dashboard;
        if (d) {
          out.appendLine(`Current Tokens:     ${d.current_tokens}`);
          out.appendLine(
            `Optimized Tokens:   ${d.optimized_tokens} (${d.reduction_percentage}% reduction)`
          );
          out.appendLine(`Savings per Call:   $${d.savings_per_call}`);
          if (d.monthly_savings !== undefined) {
            out.appendLine(
              `Monthly Savings:    $${d.monthly_savings} at ${d.calls_per_day} calls/day`
            );
            out.appendLine(`Annual Savings:     $${d.annual_savings}`);
          }
        } else {
          out.appendLine("No dashboard data available.");
        }
      } catch {
        out.appendLine("Failed to run promptlint CLI.");
      } finally {
        try {
          fs.unlinkSync(tmpFile);
        } catch {}
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.explainRule", async () => {
      let rules: string[];
      try {
        const { stdout } = await runCli(["--list-rules"]);
        rules = parseRuleIds(stdout);
      } catch {
        rules = [];
      }
      if (rules.length === 0) {
        rules = [
          "cost",
          "cost-limit",
          "prompt-injection",
          "structure-sections",
          "clarity-vague-terms",
          "specificity-examples",
          "specificity-constraints",
          "politeness-bloat",
          "verbosity-sentence-length",
          "verbosity-redundancy",
          "actionability-weak-verbs",
          "consistency-terminology",
          "completeness-edge-cases",
        ];
      }
      const pick = await vscode.window.showQuickPick(rules, {
        placeHolder: "Select a rule to explain",
      });
      if (!pick) return;
      try {
        const { stdout } = await runCli(["--explain", pick]);
        const out = vscode.window.createOutputChannel("PromptLint Rule");
        out.show(true);
        out.appendLine(stdout);
      } catch {
        vscode.window.showErrorMessage(
          `Failed to explain rule '${pick}'. Is promptlint CLI installed?`
        );
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.init", async () => {
      const root =
        vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath ?? process.cwd();
      try {
        await runCli(["--init"], root);
        vscode.window.showInformationMessage(
          "Created .promptlintrc in workspace root."
        );
      } catch {
        vscode.window.showErrorMessage(
          "promptlint --init failed. Ensure CLI is installed."
        );
      }
    })
  );

  // --- Fix helper ---

  async function fixPromptText(text: string): Promise<string | null> {
    const tmpFile = createTempFile(text);
    if (!tmpFile) return null;
    try {
      const { stdout } = await runCli([
        "-f",
        tmpFile,
        "--fix",
        "--format",
        "json",
      ]);
      const res = JSON.parse(stdout || "{}");
      return res.optimized_prompt ?? null;
    } catch {
      return null;
    } finally {
      try {
        fs.unlinkSync(tmpFile);
      } catch {}
    }
  }

  function reindentFixed(original: string, fixed: string): string {
    const origLines = original.split(/\r?\n/);
    const fixedLines = fixed.split(/\r?\n/);

    const leadingWs = origLines
      .filter((l) => l.trim().length > 0)
      .map((l) => {
        const match = l.match(/^(\s*)/);
        return match ? match[1] : "";
      });
    const baseIndent = leadingWs.length > 0
      ? leadingWs.reduce((a, b) => (a.length <= b.length ? a : b))
      : "";

    return fixedLines
      .map((line) => (line.trim().length > 0 ? baseIndent + line.trimStart() : ""))
      .join("\n");
  }

  async function applyFixToDocument(editor: vscode.TextEditor) {
    const doc = editor.document;
    const fullText = doc.getText();
    const regions = extractRegions(fullText);

    if (regions.length > 0) {
      let applied = 0;
      for (const region of [...regions].reverse()) {
        const stripped = stripCodeWrapper(region.content);
        const fixed = await fixPromptText(stripped.promptText);
        if (fixed && fixed !== stripped.promptText) {
          const reindented = reindentFixed(stripped.promptText, fixed);
          // Reconstruct: keep original wrapper lines, only replace prompt body
          const contentLines = region.content.split(/\r?\n/);
          const header = contentLines.slice(0, stripped.headerLineCount);
          const footer = contentLines.slice(
            contentLines.length - (stripped.footerLineCount || 0)
          );
          const rebuilt = [...header, reindented, ...footer].join("\n");

          const startLine = region.startLine - 1;
          const endLine = region.endLine - 2;
          const range = new vscode.Range(
            startLine,
            0,
            endLine,
            doc.lineAt(endLine).text.length
          );
          await editor.edit((e) => {
            e.replace(range, rebuilt);
          });
          applied++;
        }
      }
      if (applied > 0) {
        vscode.window.showInformationMessage(
          `PromptLint: fixed ${applied} prompt region(s).`
        );
      } else {
        vscode.window.showInformationMessage("No auto-fixes available.");
      }
    } else {
      // Pure prompt file: fix the whole file, preserve indentation
      const fixed = await fixPromptText(fullText);
      if (fixed && fixed !== fullText) {
        const reindented = reindentFixed(fullText, fixed);
        const fullRange = new vscode.Range(
          0,
          0,
          doc.lineCount - 1,
          doc.lineAt(doc.lineCount - 1).text.length
        );
        await editor.edit((e) => {
          e.replace(fullRange, reindented);
        });
        vscode.window.showInformationMessage("PromptLint fixes applied.");
      } else {
        vscode.window.showInformationMessage("No auto-fixes available.");
      }
    }
  }
}

function checkCLI() {
  const pythonPath = currentConfig.pythonPath;
  execFile(pythonPath, ["-m", "promptlint", "--version"], (err) => {
    if (err) {
      vscode.window
        .showInformationMessage(
          "promptlint CLI not found. Install with: pip install promptlint-cli",
          "Install"
        )
        .then((sel) => {
          if (sel === "Install") {
            const term = vscode.window.createTerminal("PromptLint");
            term.show();
            term.sendText(
              `${currentConfig.pythonPath} -m pip install promptlint-cli`
            );
          }
        });
    }
  });
}

function parseRuleIds(listOutput: string): string[] {
  const ids: string[] = [];
  for (const line of listOutput.split("\n")) {
    const trimmed = line.trim();
    if (
      trimmed &&
      !trimmed.startsWith("─") &&
      !trimmed.startsWith("│") &&
      !trimmed.toLowerCase().includes("id") &&
      !trimmed.toLowerCase().includes("promptlint rules")
    ) {
      const match = trimmed.match(/^[\s│]*([a-z][\w-]+)/);
      if (match) ids.push(match[1]);
    }
  }
  return ids;
}

export function deactivate() {}
