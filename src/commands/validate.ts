import * as vscode from "vscode";

import { sendChatRequest } from "../services/api";
import { applyUpdatedFiles } from "../services/diffManager";
import { buildEditorPayload } from "../services/editorContext";
import { toBackendWorkspacePath } from "../services/workspaceContext";

export async function validateWorkspace(): Promise<void> {
  const editor = vscode.window.activeTextEditor;
  const backendPath = editor ? toBackendWorkspacePath(editor.document.fileName) : "the current workspace";
  const payload = await buildEditorPayload(
    "validate_workspace",
    `Validate ${backendPath} with generated tests if needed`,
    { runValidation: true, generateTests: true }
  );

  const result = await sendChatRequest(payload);
  await applyUpdatedFiles(result);
  vscode.window.showInformationMessage(result.response);
}
