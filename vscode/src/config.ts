import * as vscode from "vscode";

export interface PromptLintConfig {
  pythonPath: string;
  lintOnSave: boolean;
  lintOnType: boolean;
  lintOnTypeDelay: number;
  languages: string[];
  configPath: string;
  failLevel: "none" | "warn" | "critical";
  showStatusBar: boolean;
}

export function getConfig(): PromptLintConfig {
  const cfg = vscode.workspace.getConfiguration("promptlint");
  const pythonPath = cfg.get<string>("pythonPath", "python");
  const lintOnSave = cfg.get<boolean>("lintOnSave", true);
  const lintOnType = cfg.get<boolean>("lintOnType", false);
  const lintOnTypeDelay = cfg.get<number>("lintOnTypeDelay", 500);
  const languages = cfg.get<string[]>("languages", ["plaintext", "markdown", "python", "javascript", "typescript", "json", "yaml", "toml"]);
  const configPath = cfg.get<string>("configPath", "");
  const failLevel = cfg.get<"none"|"warn"|"critical">("failLevel", "critical");
  const showStatusBar = cfg.get<boolean>("showStatusBar", true);
  return {
    pythonPath,
    lintOnSave,
    lintOnType,
    lintOnTypeDelay,
    languages,
    configPath,
    failLevel,
    showStatusBar
  };
}
