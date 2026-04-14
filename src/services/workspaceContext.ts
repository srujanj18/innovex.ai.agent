import * as path from "path";
import * as vscode from "vscode";

export function getWorkspaceRoot(): string | undefined {
  return vscode.workspace.workspaceFolders?.[0]?.uri.fsPath;
}

export function toBackendWorkspacePath(filePath: string): string {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    return path.basename(filePath);
  }

  const normalizedRoot = path.join(workspaceRoot, "backend", "workspace");
  if (filePath.startsWith(normalizedRoot)) {
    return path.relative(normalizedRoot, filePath);
  }

  const relativeToWorkspace = path.relative(workspaceRoot, filePath);
  if (!relativeToWorkspace.startsWith("..")) {
    return relativeToWorkspace;
  }

  return path.basename(filePath);
}

export function toWorkspaceRelativePath(filePath: string): string | undefined {
  const workspaceRoot = getWorkspaceRoot();
  if (!workspaceRoot) {
    return undefined;
  }

  const relativePath = path.relative(workspaceRoot, filePath);
  return relativePath.startsWith("..") ? undefined : relativePath;
}
