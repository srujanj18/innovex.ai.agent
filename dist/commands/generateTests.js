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
exports.generateTests = generateTests;
const vscode = __importStar(require("vscode"));
const api_1 = require("../services/api");
const diffManager_1 = require("../services/diffManager");
const editorContext_1 = require("../services/editorContext");
const workspaceContext_1 = require("../services/workspaceContext");
async function generateTests() {
    const editor = vscode.window.activeTextEditor;
    if (!editor) {
        vscode.window.showErrorMessage("Open a file first.");
        return;
    }
    const backendPath = (0, workspaceContext_1.toBackendWorkspacePath)(editor.document.fileName);
    const payload = await (0, editorContext_1.buildEditorPayload)("generate_tests", `Generate tests for ${backendPath} and validate them`, { runValidation: true, generateTests: true });
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "Agent is generating tests",
        cancellable: false
    }, async () => {
        const result = await (0, api_1.sendChatRequest)(payload);
        await (0, diffManager_1.applyUpdatedFiles)(result);
        vscode.window.showInformationMessage(result.response);
    });
}
//# sourceMappingURL=generateTests.js.map