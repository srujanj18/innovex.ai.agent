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
exports.applyUpdatedFiles = applyUpdatedFiles;
const vscode = __importStar(require("vscode"));
async function replaceDocumentContent(document, content) {
    const editor = await vscode.window.showTextDocument(document, { preview: false, preserveFocus: true });
    const entireRange = new vscode.Range(document.positionAt(0), document.positionAt(document.getText().length));
    await editor.edit((editBuilder) => {
        editBuilder.replace(entireRange, content);
    });
    await document.save();
}
async function applyUpdatedFiles(response) {
    const config = vscode.workspace.getConfiguration("agent");
    if (!config.get("autoApplyChanges", true)) {
        return;
    }
    for (const updatedFile of response.updatedFiles ?? []) {
        const uri = vscode.Uri.file(updatedFile.path);
        try {
            const openDocument = vscode.workspace.textDocuments.find((document) => document.uri.fsPath === updatedFile.path);
            if (openDocument) {
                await replaceDocumentContent(openDocument, updatedFile.content);
                continue;
            }
            await vscode.workspace.fs.writeFile(uri, Buffer.from(updatedFile.content, "utf8"));
        }
        catch (error) {
            const message = error instanceof Error ? error.message : String(error);
            vscode.window.showWarningMessage(`Could not apply update for ${updatedFile.path}: ${message}`);
        }
    }
}
//# sourceMappingURL=diffManager.js.map