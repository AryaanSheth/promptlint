import * as core from "@actions/core";
import * as glob from "@actions/glob";
import * as fs from "fs";
import * as path from "path";
import { analyze, computeScore, loadConfig } from "promptlint-cli";
import type { Finding } from "promptlint-cli";

interface FileFinding extends Finding {
  filePath: string;
}

async function run(): Promise<void> {
  const pattern = core.getInput("path") || ".";
  const failLevel = core.getInput("fail-level") || "critical";
  const configInput = core.getInput("config");
  const showScore = core.getInput("show-score") === "true";
  const sarifOutput = core.getInput("sarif-output");
  const emitAnnotations = core.getInput("annotations") !== "false";

  const workspaceRoot = process.env.GITHUB_WORKSPACE || process.cwd();

  // ── Resolve files ───────────────────────────────────────────────────────

  const globber = await glob.create(pattern, { followSymbolicLinks: false });
  const matched = await globber.glob();

  const promptFiles = matched.filter((f) => {
    try {
      return fs.statSync(f).isFile();
    } catch {
      return false;
    }
  });

  if (promptFiles.length === 0) {
    core.warning(`PromptLint: no files matched pattern "${pattern}"`);
    core.setOutput("findings-count", 0);
    core.setOutput("critical-count", 0);
    core.setOutput("score", 100);
    core.setOutput("grade", "A");
    return;
  }

  core.info(`PromptLint: scanning ${promptFiles.length} file(s)...`);

  // ── Load config ─────────────────────────────────────────────────────────

  const config = loadConfig(configInput || undefined);

  // ── Analyze ─────────────────────────────────────────────────────────────

  const allFindings: FileFinding[] = [];
  const MAX_BYTES = 10 * 1024 * 1024;

  for (const filePath of promptFiles) {
    let text: string;
    try {
      const stat = fs.statSync(filePath);
      if (stat.size > MAX_BYTES) {
        core.warning(`Skipping ${filePath}: exceeds 10 MB limit`);
        continue;
      }
      text = fs.readFileSync(filePath, "utf8");
    } catch (err) {
      core.warning(`Could not read ${filePath}: ${err}`);
      continue;
    }

    const findings = analyze(text, config);
    for (const f of findings) {
      allFindings.push({ ...f, filePath });
    }
  }

  // ── GitHub annotations ──────────────────────────────────────────────────

  if (emitAnnotations) {
    for (const f of allFindings) {
      // Skip cost/token INFO findings — too noisy for PR annotations
      if (f.rule === "cost" && f.level === "INFO") continue;

      const relPath = path
        .relative(workspaceRoot, f.filePath)
        .replace(/\\/g, "/");

      const lineNum =
        typeof f.line === "number" ? f.line : undefined;

      const props: core.AnnotationProperties = {
        file: relPath,
        startLine: lineNum,
        title: `PromptLint [${f.rule}]`,
      };

      if (f.level === "CRITICAL") core.error(f.message, props);
      else if (f.level === "WARN") core.warning(f.message, props);
      else core.notice(f.message, props);
    }
  }

  // ── Health score ────────────────────────────────────────────────────────

  const score = computeScore(allFindings);

  if (showScore) {
    core.info("──────────────────────────────────────────");
    core.info(
      `PromptLint Health Score: ${score.overall}/100  (Grade: ${score.grade})`
    );
    core.info(`  Security:     ${score.categories.security}/100`);
    core.info(`  Cost:         ${score.categories.cost}/100`);
    core.info(`  Quality:      ${score.categories.quality}/100`);
    core.info(`  Completeness: ${score.categories.completeness}/100`);
    core.info("──────────────────────────────────────────");
  }

  // ── SARIF output ────────────────────────────────────────────────────────

  if (sarifOutput) {
    const sarif = buildSarif(allFindings, workspaceRoot);
    fs.writeFileSync(sarifOutput, JSON.stringify(sarif, null, 2), "utf8");
    core.info(`PromptLint: SARIF written to ${sarifOutput}`);
  }

  // ── Outputs ─────────────────────────────────────────────────────────────

  const critCount = allFindings.filter((f) => f.level === "CRITICAL").length;
  const warnAndCritCount = allFindings.filter(
    (f) => f.level === "WARN" || f.level === "CRITICAL"
  ).length;

  core.setOutput("findings-count", allFindings.length);
  core.setOutput("critical-count", critCount);
  core.setOutput("score", score.overall);
  core.setOutput("grade", score.grade);

  core.info(
    `PromptLint: ${promptFiles.length} file(s) scanned — ` +
      `${allFindings.length} finding(s), ${critCount} CRITICAL`
  );

  // ── Fail logic ──────────────────────────────────────────────────────────

  if (failLevel === "critical" && critCount > 0) {
    core.setFailed(
      `PromptLint: ${critCount} CRITICAL finding(s) detected. Fix before merging.`
    );
  } else if (failLevel === "warn" && warnAndCritCount > 0) {
    core.setFailed(
      `PromptLint: ${warnAndCritCount} WARN/CRITICAL finding(s) detected.`
    );
  }
}

// ── SARIF v2.1.0 builder ────────────────────────────────────────────────────

function buildSarif(
  findings: FileFinding[],
  workspaceRoot: string
): object {
  // Unique rule IDs
  const ruleIds = [...new Set(findings.map((f) => f.rule))];

  const rules = ruleIds.map((id) => ({
    id,
    name: id
      .split("-")
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(""),
    shortDescription: { text: `PromptLint: ${id}` },
    helpUri: `https://promptlint.dev/rules#${id}`,
    properties: { tags: ["promptlint", "llm", "security"] },
  }));

  const results = findings.map((f) => {
    const relPath = path
      .relative(workspaceRoot, f.filePath)
      .replace(/\\/g, "/");

    const sarifLevel =
      f.level === "CRITICAL" ? "error" :
      f.level === "WARN" ? "warning" : "note";

    return {
      ruleId: f.rule,
      level: sarifLevel,
      message: { text: f.message },
      locations: [
        {
          physicalLocation: {
            artifactLocation: {
              uri: relPath,
              uriBaseId: "%SRCROOT%",
            },
            ...(typeof f.line === "number"
              ? { region: { startLine: f.line } }
              : {}),
          },
        },
      ],
    };
  });

  return {
    $schema:
      "https://schemastore.azurewebsites.net/schemas/json/sarif-2.1.0-rtm.5.json",
    version: "2.1.0",
    runs: [
      {
        tool: {
          driver: {
            name: "PromptLint",
            version: "1.0.0",
            informationUri: "https://promptlint.dev",
            rules,
          },
        },
        results,
        originalUriBaseIds: {
          "%SRCROOT%": { uri: "file:///" },
        },
      },
    ],
  };
}

run().catch(core.setFailed);
