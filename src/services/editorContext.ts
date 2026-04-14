import * as vscode from "vscode";

import { ChatRequestPayload } from "../types/api";
import { toWorkspaceRelativePath } from "./workspaceContext";

export function getOpenFilePaths(): string[] {
  return vscode.workspace.textDocuments
    .filter((doc) => doc.uri.scheme === "file")
    .map((doc) => doc.fileName);
}

async function getWorkspaceFiles(limit = 200): Promise<string[]> {
  const files = await vscode.workspace.findFiles(
    "**/*",
    "**/{node_modules,dist,.git,backend/workspace,gemini_env}/**",
    limit
  );

  return files
    .map((file) => {
      const folder = vscode.workspace.getWorkspaceFolder(file);
      if (!folder) {
        return undefined;
      }

      return vscode.workspace.asRelativePath(file, false);
    })
    .filter((filePath): filePath is string => Boolean(filePath))
    .sort((left, right) => left.localeCompare(right));
}

export async function buildEditorPayload(
  task: string,
  message: string,
  options?: { runValidation?: boolean; generateTests?: boolean; autonomousMode?: boolean; intelligenceLevel?: string }
): Promise<ChatRequestPayload> {
  const editor = vscode.window.activeTextEditor;
  const workspaceFolder = editor ? vscode.workspace.getWorkspaceFolder(editor.document.uri) : vscode.workspace.workspaceFolders?.[0];
  const workspaceFiles = await getWorkspaceFiles();

  if (!editor) {
    return {
      task,
      message,
      workspaceRoot: workspaceFolder?.uri.fsPath,
      openFiles: getOpenFilePaths(),
      workspaceFiles,
      runValidation: options?.runValidation ?? false,
      generateTests: options?.generateTests ?? false,
      autonomousMode: options?.autonomousMode ?? true,
      intelligenceLevel: options?.intelligenceLevel ?? "high"
    };
  }

  const selection = editor.selection.isEmpty ? "" : editor.document.getText(editor.selection);

  return {
    task,
    message,
    filePath: editor.document.fileName,
    relativeFilePath: toWorkspaceRelativePath(editor.document.fileName),
    language: editor.document.languageId,
    code: editor.document.getText(),
    selection,
    workspaceRoot: workspaceFolder?.uri.fsPath,
    openFiles: getOpenFilePaths(),
    workspaceFiles,
    runValidation: options?.runValidation ?? false,
    generateTests: options?.generateTests ?? false,
    autonomousMode: options?.autonomousMode ?? true,
    intelligenceLevel: options?.intelligenceLevel ?? "high"
  };
}
