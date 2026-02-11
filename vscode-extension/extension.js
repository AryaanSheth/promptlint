const vscode = require('vscode');
const { exec } = require('child_process');
const path = require('path');
const os = require('os');

let statusBarItem;
let outputChannel;

/**
 * @param {vscode.ExtensionContext} context
 */
function activate(context) {
    console.log('PromptLint extension activated');

    // Create output channel for logs
    outputChannel = vscode.window.createOutputChannel('PromptLint');
    
    // Create status bar item
    statusBarItem = vscode.window.createStatusBarItem(
        vscode.StatusBarAlignment.Right,
        100
    );
    statusBarItem.command = 'promptlint.analyzeSelection';
    context.subscriptions.push(statusBarItem);
    
    // Update status bar on text selection
    context.subscriptions.push(
        vscode.window.onDidChangeTextEditorSelection(updateStatusBar)
    );
    
    // Register commands
    context.subscriptions.push(
        vscode.commands.registerCommand('promptlint.analyzeSelection', analyzeSelection)
    );
    
    context.subscriptions.push(
        vscode.commands.registerCommand('promptlint.analyzeAndReplace', analyzeAndReplace)
    );
    
    context.subscriptions.push(
        vscode.commands.registerCommand('promptlint.showDiff', showDiff)
    );
    
    context.subscriptions.push(
        vscode.commands.registerCommand('promptlint.toggleStatusBar', toggleStatusBar)
    );
    
    // Show welcome message
    vscode.window.showInformationMessage(
        '✅ PromptLint is ready! Press Cmd+Option+L to analyze your prompts.',
        'Learn More'
    ).then(selection => {
        if (selection === 'Learn More') {
            vscode.env.openExternal(vscode.Uri.parse('https://github.com/yourusername/promptlint'));
        }
    });
    
    updateStatusBar();
}

function updateStatusBar() {
    const config = vscode.workspace.getConfiguration('promptlint');
    if (!config.get('enabled') || !config.get('showTokenCount')) {
        statusBarItem.hide();
        return;
    }
    
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        statusBarItem.hide();
        return;
    }
    
    const selection = editor.selection;
    const text = editor.document.getText(selection.isEmpty ? undefined : selection);
    
    if (text.length === 0) {
        statusBarItem.hide();
        return;
    }
    
    // Rough token estimate: ~1.3 tokens per word
    const words = text.split(/\s+/).length;
    const tokens = Math.round(words * 1.3);
    
    statusBarItem.text = `$(pulse) ${tokens} tokens`;
    statusBarItem.tooltip = 'Click to analyze with PromptLint';
    statusBarItem.show();
}

async function analyzeSelection() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }
    
    const selection = editor.selection;
    const text = editor.document.getText(selection.isEmpty ? undefined : selection);
    
    if (text.trim().length === 0) {
        vscode.window.showWarningMessage('No text selected. Select text or place cursor in prompt to analyze.');
        return;
    }
    
    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Analyzing prompt with PromptLint...',
        cancellable: false
    }, async (progress) => {
        try {
            const result = await runPromptLint(text);
            
            if (result.error) {
                vscode.window.showErrorMessage(`PromptLint error: ${result.error}`);
                outputChannel.appendLine(`Error: ${result.error}`);
                return;
            }
            
            showAnalysisResults(result, text, editor, selection);
            
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to run PromptLint: ${error.message}`);
            outputChannel.appendLine(`Exception: ${error.message}`);
        }
    });
}

async function analyzeAndReplace() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage('No active editor');
        return;
    }
    
    const selection = editor.selection;
    const text = editor.document.getText(selection.isEmpty ? undefined : selection);
    
    if (text.trim().length === 0) {
        vscode.window.showWarningMessage('No text selected');
        return;
    }
    
    vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: 'Optimizing prompt...',
        cancellable: false
    }, async (progress) => {
        try {
            const result = await runPromptLint(text);
            
            if (result.error) {
                vscode.window.showErrorMessage(`PromptLint error: ${result.error}`);
                return;
            }
            
            const optimized = result.optimized_prompt;
            
            if (optimized === text) {
                vscode.window.showInformationMessage('✅ Prompt is already optimized!');
                return;
            }
            
            // Show summary
            const tokensSaved = result.tokens_saved || 0;
            const issueCount = result.findings ? result.findings.length : 0;
            
            const action = await vscode.window.showInformationMessage(
                `Found ${issueCount} issues. Saved ${tokensSaved} tokens (${result.savings_percent || 0}%). Replace text?`,
                'Replace',
                'Show Diff',
                'Cancel'
            );
            
            if (action === 'Replace') {
                await editor.edit(editBuilder => {
                    if (selection.isEmpty) {
                        const fullRange = new vscode.Range(
                            editor.document.positionAt(0),
                            editor.document.positionAt(editor.document.getText().length)
                        );
                        editBuilder.replace(fullRange, optimized);
                    } else {
                        editBuilder.replace(selection, optimized);
                    }
                });
                vscode.window.showInformationMessage('✅ Text replaced with optimized version!');
            } else if (action === 'Show Diff') {
                showDiffView(text, optimized, result);
            }
            
        } catch (error) {
            vscode.window.showErrorMessage(`Failed to optimize: ${error.message}`);
        }
    });
}

async function showDiff() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        return;
    }
    
    const selection = editor.selection;
    const text = editor.document.getText(selection.isEmpty ? undefined : selection);
    
    if (text.trim().length === 0) {
        vscode.window.showWarningMessage('No text selected');
        return;
    }
    
    try {
        const result = await runPromptLint(text);
        
        if (result.error) {
            vscode.window.showErrorMessage(`PromptLint error: ${result.error}`);
            return;
        }
        
        showDiffView(text, result.optimized_prompt, result);
        
    } catch (error) {
        vscode.window.showErrorMessage(`Failed to show diff: ${error.message}`);
    }
}

async function showDiffView(original, optimized, result) {
    // Create temporary files for diff
    const originalUri = vscode.Uri.parse(`promptlint:original.txt`);
    const optimizedUri = vscode.Uri.parse(`promptlint:optimized.txt`);
    
    // Register text document content provider
    const provider = new class {
        provideTextDocumentContent(uri) {
            if (uri.path === 'original.txt') {
                return original;
            } else if (uri.path === 'optimized.txt') {
                return optimized;
            }
            return '';
        }
    };
    
    vscode.workspace.registerTextDocumentContentProvider('promptlint', provider);
    
    // Open diff view
    await vscode.commands.executeCommand(
        'vscode.diff',
        originalUri,
        optimizedUri,
        `PromptLint: Original ↔ Optimized (${result.tokens_saved || 0} tokens saved)`
    );
}

function showAnalysisResults(result, originalText, editor, selection) {
    const findings = result.findings || [];
    const critical = findings.filter(f => f.level === 'CRITICAL').length;
    const warnings = findings.filter(f => f.level === 'WARN').length;
    const info = findings.filter(f => f.level === 'INFO').length;
    
    const tokensSaved = result.tokens_saved || 0;
    const savingsPercent = result.savings_percent || 0;
    
    // Build message
    let message = `📊 Found ${findings.length} issues: `;
    if (critical > 0) message += `🔴 ${critical} critical `;
    if (warnings > 0) message += `⚠️ ${warnings} warnings `;
    if (info > 0) message += `ℹ️ ${info} info`;
    
    if (tokensSaved > 0) {
        message += `\n💰 Can save ${tokensSaved} tokens (${savingsPercent}%)`;
    }
    
    // Show findings in output channel
    outputChannel.clear();
    outputChannel.appendLine('═══════════════════════════════════════════');
    outputChannel.appendLine('   PromptLint Analysis Results');
    outputChannel.appendLine('═══════════════════════════════════════════\n');
    
    findings.forEach((finding, i) => {
        const icon = finding.level === 'CRITICAL' ? '🔴' :
                     finding.level === 'WARN' ? '⚠️' : 'ℹ️';
        outputChannel.appendLine(`${icon} [${finding.level}] ${finding.rule}`);
        outputChannel.appendLine(`   ${finding.message}`);
        if (finding.context) {
            outputChannel.appendLine(`   Context: ${finding.context.substring(0, 100)}...`);
        }
        outputChannel.appendLine('');
    });
    
    if (result.optimized_prompt && result.optimized_prompt !== originalText) {
        outputChannel.appendLine('───────────────────────────────────────────');
        outputChannel.appendLine('   Optimized Version:');
        outputChannel.appendLine('───────────────────────────────────────────');
        outputChannel.appendLine(result.optimized_prompt);
        outputChannel.appendLine('');
    }
    
    outputChannel.show(true);
    
    // Show action buttons
    const actions = ['Replace with Optimized', 'Show Diff', 'Copy Optimized'];
    
    vscode.window.showInformationMessage(
        message,
        ...actions
    ).then(async (action) => {
        if (action === 'Replace with Optimized') {
            await editor.edit(editBuilder => {
                if (selection.isEmpty) {
                    const fullRange = new vscode.Range(
                        editor.document.positionAt(0),
                        editor.document.positionAt(editor.document.getText().length)
                    );
                    editBuilder.replace(fullRange, result.optimized_prompt);
                } else {
                    editBuilder.replace(selection, result.optimized_prompt);
                }
            });
            vscode.window.showInformationMessage('✅ Replaced with optimized version!');
        } else if (action === 'Show Diff') {
            showDiffView(originalText, result.optimized_prompt, result);
        } else if (action === 'Copy Optimized') {
            await vscode.env.clipboard.writeText(result.optimized_prompt);
            vscode.window.showInformationMessage('✅ Copied to clipboard!');
        }
    });
}

function runPromptLint(text) {
    return new Promise((resolve, reject) => {
        const config = vscode.workspace.getConfiguration('promptlint');
        const pythonPath = config.get('pythonPath', 'python3');
        let promptlintPath = config.get('promptlintPath', '');
        
        // Auto-detect promptlint path if not set
        if (!promptlintPath) {
            // Try to find promptlint in workspace
            const workspaceFolders = vscode.workspace.workspaceFolders;
            if (workspaceFolders && workspaceFolders.length > 0) {
                const workspaceRoot = workspaceFolders[0].uri.fsPath;
                const possiblePath = path.join(workspaceRoot, 'promptlint');
                promptlintPath = possiblePath;
            }
        }
        
        // Escape text for command line
        const escapedText = text.replace(/\\/g, '\\\\').replace(/"/g, '\\"').replace(/\n/g, ' ');
        
        const cwd = promptlintPath || process.cwd();
        const cmd = `${pythonPath} -m promptlint.cli --text "${escapedText}" --format json --fix`;
        
        outputChannel.appendLine(`Running: ${cmd}`);
        outputChannel.appendLine(`CWD: ${cwd}`);
        
        exec(cmd, { cwd, maxBuffer: 1024 * 1024 * 10 }, (error, stdout, stderr) => {
            if (error && !stdout) {
                outputChannel.appendLine(`Error: ${error.message}`);
                outputChannel.appendLine(`Stderr: ${stderr}`);
                reject(new Error(`PromptLint failed: ${error.message}`));
                return;
            }
            
            try {
                const result = JSON.parse(stdout);
                
                // Calculate additional metrics
                if (result.findings) {
                    const originalTokens = Math.round(text.split(/\s+/).length * 1.3);
                    const optimizedTokens = Math.round((result.optimized_prompt || text).split(/\s+/).length * 1.3);
                    result.tokens_saved = Math.max(0, originalTokens - optimizedTokens);
                    result.savings_percent = originalTokens > 0 ? 
                        Math.round((result.tokens_saved / originalTokens) * 100) : 0;
                }
                
                resolve(result);
            } catch (parseError) {
                outputChannel.appendLine(`Parse error: ${parseError.message}`);
                outputChannel.appendLine(`Output: ${stdout}`);
                reject(new Error('Failed to parse PromptLint output'));
            }
        });
    });
}

function toggleStatusBar() {
    const config = vscode.workspace.getConfiguration('promptlint');
    const currentValue = config.get('showTokenCount', true);
    config.update('showTokenCount', !currentValue, vscode.ConfigurationTarget.Global);
    vscode.window.showInformationMessage(
        `PromptLint status bar ${!currentValue ? 'enabled' : 'disabled'}`
    );
}

function deactivate() {
    if (statusBarItem) {
        statusBarItem.dispose();
    }
    if (outputChannel) {
        outputChannel.dispose();
    }
}

module.exports = {
    activate,
    deactivate
};
