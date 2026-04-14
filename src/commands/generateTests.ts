import * as vscode from "vscode";

import { sendChatRequest } from "../services/api";
import { applyUpdatedFiles } from "../services/diffManager";
import { buildEditorPayload } from "../services/editorContext";
import { toBackendWorkspacePath } from "../services/workspaceContext";

export async function generateTests(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  if (!editor) {
    vscode.window.showErrorMessage("Open a file first.");
    return;
  }

  const backendPath = toBackendWorkspacePath(editor.document.fileName);
  const payload = await buildEditorPayload(
    "generate_tests",
    `Generate tests for ${backendPath} and validate them`,
    { runValidation: true, generateTests: true }
  );

  await vscode.window.withProgress(
    {
      location: vscode.ProgressLocation.Notification,
      title: "Agent is generating tests",
      cancellable: false
    },
    async () => {
      const result = await sendChatRequest(payload);
      await applyUpdatedFiles(result);
      vscode.window.showInformationMessage(result.response);
    }
  );
}
