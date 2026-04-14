export interface ChatRequestPayload {
  task: string;
  message: string;
  filePath?: string;
  relativeFilePath?: string;
  language?: string;
  code?: string;
  selection?: string;
  workspaceRoot?: string;
  openFiles?: string[];
  workspaceFiles?: string[];
  runValidation?: boolean;
  generateTests?: boolean;
  autonomousMode?: boolean;
  intelligenceLevel?: "medium" | "high" | "very_high" | string;
}

export interface ChatResponsePayload {
  response: string;
  task?: string;
  filePath?: string;
  runValidation?: boolean;
  generateTests?: boolean;
  autonomousMode?: boolean;
  intelligenceLevel?: string;
  updatedFiles?: Array<{
    path: string;
    content: string;
  }>;
}
