import * as vscode from "vscode";

import { sendChatRequest } from "../services/api";
import { applyUpdatedFiles } from "../services/diffManager";
import { buildEditorPayload } from "../services/editorContext";

export async function runAgentTask(): Promise<void> {
  const message = await vscode.window.showInputBox({
    prompt: "Describe the coding task you want the agent to complete",
    placeHolder: "Create a website in a new folder, implement a feature, fix errors, add tests..."
  });

  if (!message) {
    return;
  }

  const payload = await buildEditorPayload("run_task", message, {
    runValidation: true,
    generateTests: false
  });

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "Agent is completing the task",
      cancellable: false
    },
    async () => {
      const result = await sendChatRequest(payload);
      await applyUpdatedFiles(result);

      const output = vscode.window.createOutputChannel("Gemini Codex Agent");
      output.appendLine(`> ${message}`);
      output.appendLine(result.response);
      output.show(true);

      vscode.window.showInformationMessage("Agent task finished. Review the output channel for details.");
    }
  );
}
