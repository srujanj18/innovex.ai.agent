import * as vscode from "vscode";

import { ChatRequestPayload, ChatResponsePayload } from "../types/api";

export function getBackendUrl(): string {
  const config = vscode.workspace.getConfiguration("agent");
  return config.get<string>("backendUrl", "http://127.0.0.1:8000");
}

export async function sendChatRequest(payload: ChatRequestPayload): Promise<ChatResponsePayload> {
  const response = await fetch(`${getBackendUrl()}/chat`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    const body = await response.text();
    throw new Error(`Backend request failed (${response.status}): ${body}`);
  }

  return (await response.json()) as ChatResponsePayload;
}
