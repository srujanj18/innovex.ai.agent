"use strict";
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
exports.getOpenFilePaths = getOpenFilePaths;
exports.buildEditorPayload = buildEditorPayload;
const vscode = __importStar(require("vscode"));
const workspaceContext_1 = require("./workspaceContext");
function getOpenFilePaths() {
    return vscode.workspace.textDocuments
        .filter((doc) => doc.uri.scheme === "file")
        .map((doc) => doc.fileName);
}
async function getWorkspaceFiles(limit = 200) {
    const files = await vscode.workspace.findFiles("**/*", "**/{node_modules,dist,.git,backend/workspace,gemini_env}/**", limit);
    return files
        .map((file) => {
        const folder = vscode.workspace.getWorkspaceFolder(file);
        if (!folder) {
            return undefined;
        }
        return vscode.workspace.asRelativePath(file, false);
    })
        .filter((filePath) => Boolean(filePath))
        .sort((left, right) => left.localeCompare(right));
}
async function buildEditorPayload(task, message, options) {
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
        relativeFilePath: (0, workspaceContext_1.toWorkspaceRelativePath)(editor.document.fileName),
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
//# sourceMappingURL=editorContext.js.map