import * as vscode from "vscode";
import * as fs from "fs";
import * as path from "path";
import { getConfig, PromptLintConfig } from "./config";
import { lintDocument, lintText, fixText, extractRegions, stripCodeWrapper } from "./linter";
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

/** Resolve the effective .promptlintrc path for a given document. */
function resolveConfigPath(configPath: string, docFsPath: string): string | undefined {
  if (configPath) return configPath;
  const workspaceRoot = vscode.workspace.getWorkspaceFolder(
    vscode.Uri.file(docFsPath)
  )?.uri?.fsPath;
  if (workspaceRoot) {
    for (const name of [".promptlintrc", ".promptlintrc.yml", ".promptlintrc.yaml"]) {
      const p = path.join(workspaceRoot, name);
      if (fs.existsSync(p)) return p;
    }
  }
  return undefined;
}

const RULE_DOCS: Record<string, string> = {
  "cost": "Reports token count and estimated cost per call for your prompt.",
  "cost-limit": "Warns when your prompt exceeds the configured token limit.",
  "prompt-injection": "Detects prompt injection patterns that could override your instructions.",
  "structure-sections": "Checks for required structural tags (e.g. <task>, <context>).",
  "clarity-vague-terms": "Flags vague language that reduces precision (e.g. 'something', 'somehow').",
  "specificity-examples": "Suggests adding examples when none are present in longer prompts.",
  "specificity-constraints": "Checks for explicit output constraints (format, length, etc.).",
  "politeness-bloat": "Identifies politeness words (please, kindly) that add tokens without semantic value.",
  "verbosity-sentence-length": "Flags overly long sentences that could be split for clarity.",
  "verbosity-redundancy": "Detects wordy phrases replaceable with concise alternatives.",
  "actionability-weak-verbs": "Flags weak verbs (consider, try, look into) that reduce prompt directiveness.",
  "consistency-terminology": "Detects inconsistent terminology used for the same concept.",
  "completeness-edge-cases": "Checks whether the prompt addresses edge cases and unexpected inputs.",
};

const STARTER_CONFIG = `model: gpt-4o
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

fix:
  enabled: true
  prompt_injection: true
  politeness_bloat: true
  verbosity_redundancy: true
  structure_scaffold: true
`;

export function activate(context: vscode.ExtensionContext) {
  currentConfig = getConfig();

  const diagCollection =
    vscode.languages.createDiagnosticCollection("promptlint");
  context.subscriptions.push(diagCollection);

  const statusBar = currentConfig.showStatusBar ? new StatusBarManager() : null;
  if (statusBar) context.subscriptions.push(statusBar);

  context.subscriptions.push(
    vscode.workspace.onDidChangeConfiguration((e) => {
      if (e.affectsConfiguration("promptlint")) {
        refreshConfig();
      }
    })
  );

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

  // --- Lint helpers ---

  async function lintDoc(doc: vscode.TextDocument) {
    const cfgPath = resolveConfigPath(currentConfig.configPath, doc.uri.fsPath);
    const { diagnostics, dashboard } = await lintDocument(doc, cfgPath);
    diagCollection.set(doc.uri, diagnostics);
    if (dashboard && statusBar) {
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
      const docs = vscode.workspace.textDocuments.filter(shouldLintDocument);
      if (docs.length === 0) {
        vscode.window.showInformationMessage("No prompt files open to fix.");
        return;
      }
      let total = 0;
      for (const doc of docs) {
        const editor = await vscode.window.showTextDocument(doc, { preview: false });
        const before = doc.getText();
        await applyFixToDocument(editor);
        if (doc.getText() !== before) total++;
      }
      vscode.window.showInformationMessage(`PromptLint: fixed ${total} file(s).`);
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand(
      "promptlint.applyFix",
      async (uri: vscode.Uri, range: vscode.Range, _rule: string) => {
        const doc = await vscode.workspace.openTextDocument(uri);
        const regionText = doc.getText(range);
        const cfgPath = resolveConfigPath(currentConfig.configPath, uri.fsPath);
        try {
          const fixed = fixText(regionText, cfgPath);
          if (fixed && fixed !== regionText) {
            const wsEdit = new vscode.WorkspaceEdit();
            wsEdit.replace(uri, range, fixed);
            await vscode.workspace.applyEdit(wsEdit);
          }
        } catch {
          // silently ignore
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
      try {
        const cfgPath = resolveConfigPath(
          currentConfig.configPath,
          editor.document.uri.fsPath
        );
        const res = lintText(editor.document.getText(), cfgPath);
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
      } catch (e) {
        const msg = e instanceof Error ? e.message : "unknown error";
        out.appendLine(`Failed to run promptlint: ${msg}`);
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.explainRule", async () => {
      const rules = Object.keys(RULE_DOCS);
      const pick = await vscode.window.showQuickPick(rules, {
        placeHolder: "Select a rule to explain",
      });
      if (!pick) return;
      const out = vscode.window.createOutputChannel("PromptLint Rule");
      out.show(true);
      out.appendLine(`Rule: ${pick}\n`);
      out.appendLine(RULE_DOCS[pick] ?? "No documentation available.");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("promptlint.init", async () => {
      const root =
        vscode.workspace.workspaceFolders?.[0]?.uri?.fsPath ?? process.cwd();
      const configFile = path.join(root, ".promptlintrc");
      try {
        if (fs.existsSync(configFile)) {
          vscode.window.showInformationMessage(
            ".promptlintrc already exists in workspace root."
          );
          return;
        }
        fs.writeFileSync(configFile, STARTER_CONFIG, { encoding: "utf8" });
        vscode.window.showInformationMessage(
          "Created .promptlintrc in workspace root."
        );
      } catch {
        vscode.window.showErrorMessage("Failed to create .promptlintrc.");
      }
    })
  );

  // --- Fix helper ---

  function fixPromptText(text: string, docFsPath: string): string | null {
    const cfgPath = resolveConfigPath(currentConfig.configPath, docFsPath);
    try {
      const fixed = fixText(text, cfgPath);
      return fixed !== text ? fixed : null;
    } catch {
      return null;
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
    const baseIndent =
      leadingWs.length > 0
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
        const fixed = fixPromptText(stripped.promptText, doc.uri.fsPath);
        if (fixed && fixed !== stripped.promptText) {
          const reindented = reindentFixed(stripped.promptText, fixed);
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
      const fixed = fixPromptText(fullText, doc.uri.fsPath);
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

export function deactivate() {}
