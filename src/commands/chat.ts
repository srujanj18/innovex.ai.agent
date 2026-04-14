import * as vscode from "vscode";

import { sendChatRequest } from "../services/api";
import { buildEditorPayload } from "../services/editorContext";

export async function chatWithAgent(): Promise<void> {
  const message = await vscode.window.showInputBox({
    prompt: "Ask the coding agent",
    placeHolder: "Create a website in a new folder, refactor this file, explain the selection..."
  });

  if (!message) {
    return;
  }

  const payload = await buildEditorPayload("chat", message, { runValidation: false, generateTests: false });
  const result = await sendChatRequest(payload);

  const output = vscode.window.createOutputChannel("Gemini Codex Agent");
  output.appendLine(`> ${message}`);
  output.appendLine(result.response);
  output.show(true);
}
