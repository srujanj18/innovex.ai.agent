import * as vscode from "vscode";

import { chatWithAgent } from "./commands/chat";
import { fixCurrentFile } from "./commands/fixFile";
import { generateTests } from "./commands/generateTests";
import { runAgentTask } from "./commands/runTask";
import { validateWorkspace } from "./commands/validate";

export function activate(context: vscode.ExtensionContext): void {
  context.subscriptions.push(
    vscode.commands.registerCommand("agent.chat", chatWithAgent),
    vscode.commands.registerCommand("agent.runTask", runAgentTask),
    vscode.commands.registerCommand("agent.fixCurrentFile", fixCurrentFile),
    vscode.commands.registerCommand("agent.generateTests", generateTests),
    vscode.commands.registerCommand("agent.validateWorkspace", validateWorkspace)
  );
}

export function deactivate(): void {}
