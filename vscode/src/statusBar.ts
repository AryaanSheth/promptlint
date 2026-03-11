import * as vscode from "vscode";

export class StatusBarManager {
  private item: vscode.StatusBarItem;
  constructor() {
    this.item = vscode.window.createStatusBarItem(vscode.StatusBarAlignment.Left);
    this.item.text = "PLint: - tokens";
    this.item.tooltip = "Click to show PromptLint Dashboard";
    this.item.command = "promptlint.dashboard";
    this.item.show();
  }
  updateFromDashboard(dashboard: any) {
    if (!dashboard) return;
    const tokens = dashboard.current_tokens ?? 0;
    const perCall = dashboard.savings_per_call ?? 0;
    this.item.text = `PLint: ${tokens} tokens ($${perCall}/call)`;
  }
  dispose() {
    this.item.dispose();
  }
}
