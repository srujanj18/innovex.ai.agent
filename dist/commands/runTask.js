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
exports.runAgentTask = runAgentTask;
const vscode = __importStar(require("vscode"));
const api_1 = require("../services/api");
const diffManager_1 = require("../services/diffManager");
const editorContext_1 = require("../services/editorContext");
async function runAgentTask() {
    const message = await vscode.window.showInputBox({
        prompt: "Describe the coding task you want the agent to complete",
        placeHolder: "Create a website in a new folder, implement a feature, fix errors, add tests..."
    });
    if (!message) {
        return;
    }
    const payload = await (0, editorContext_1.buildEditorPayload)("run_task", message, {
        runValidation: true,
        generateTests: false
    });
    await vscode.window.withProgress({
        location: vscode.ProgressLocation.Notification,
        title: "Agent is completing the task",
        cancellable: false
    }, async () => {
        const result = await (0, api_1.sendChatRequest)(payload);
        await (0, diffManager_1.applyUpdatedFiles)(result);
        const output = vscode.window.createOutputChannel("Gemini Codex Agent");
        output.appendLine(`> ${message}`);
        output.appendLine(result.response);
        output.show(true);
        vscode.window.showInformationMessage("Agent task finished. Review the output channel for details.");
    });
}
//# sourceMappingURL=runTask.js.map