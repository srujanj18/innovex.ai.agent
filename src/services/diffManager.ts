import * as vscode from "vscode";

import { ChatResponsePayload } from "../types/api";

async function replaceDocumentContent(document: vscode.TextDocument, content: string): Promise<void> {
  const editor = await vscode.window.showTextDocument(document, { preview: false, preserveFocus: true });
  const entireRange = new vscode.Range(
    document.positionAt(0),
    document.positionAt(document.getText().length)
  );

  await editor.edit((editBuilder) => {
    editBuilder.replace(entireRange, content);
  });

  await document.save();
}

export async function applyUpdatedFiles(response: ChatResponsePayload): Promise<void> {
  const config = vscode.workspace.getConfiguration("agent");
  if (!config.get<boolean>("autoApplyChanges", true)) {
    return;
  }

  for (const updatedFile of response.updatedFiles ?? []) {
    const uri = vscode.Uri.file(updatedFile.path);

    try {
      const openDocument = vscode.workspace.textDocuments.find(
        (document) => document.uri.fsPath === updatedFile.path
      );

      if (openDocument) {
        await replaceDocumentContent(openDocument, updatedFile.content);
        continue;
      }

      await vscode.workspace.fs.writeFile(uri, Buffer.from(updatedFile.content, "utf8"));
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      vscode.window.showWarningMessage(`Could not apply update for ${updatedFile.path}: ${message}`);
    }
  }
}
