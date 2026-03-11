import * as vscode from "vscode";

export class PromptLintCodeActionProvider implements vscode.CodeActionProvider {
  static readonly fixableRules = ["politeness-bloat", "verbosity-redundancy", "structure-sections", "prompt-injection"];

  provideCodeActions(
    document: vscode.TextDocument,
    range: vscode.Range,
    context: vscode.CodeActionContext,
    token: vscode.CancellationToken
  ): vscode.ProviderResult<vscode.CodeAction[]> {
    const actions: vscode.CodeAction[] = [];
    for (const diag of context.diagnostics ?? []) {
      if (diag.source === "promptlint" && diag.code) {
        const code = String(diag.code);
        if (PromptLintCodeActionProvider.fixableRules.includes(code)) {
          const fix = new vscode.CodeAction(`Fix: ${code}`, vscode.CodeActionKind.QuickFix);
          fix.command = { command: "promptlint.applyFix", title: "PromptLint: Apply Fix", arguments: [document.uri, range, code] } as vscode.Command;
          actions.push(fix);
        }
        // Disable for this line
        const disable = new vscode.CodeAction(`Disable ${code} for this line`, vscode.CodeActionKind.QuickFix);
        disable.command = { command: "promptlint.disableRule", title: "Disable rule", arguments: [document.uri, range.start.line, code] } as vscode.Command;
        actions.push(disable);
      }
    }
    return actions;
  }
}
