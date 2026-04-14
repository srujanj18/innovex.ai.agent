# VS Code Extension Setup

## What Was Added

This workspace now includes a VS Code extension scaffold at the repo root.

Key files:

- `package.json`
- `tsconfig.json`
- `src/extension.ts`
- `src/commands/*`
- `src/services/*`
- `src/types/api.ts`

## Commands

After compiling and launching the extension, you will have:

- `Agent: Chat`
- `Agent: Fix Current File`
- `Agent: Generate Tests`
- `Agent: Validate Workspace`

## Install Dependencies

From the repo root:

```powershell
npm install
```

## Compile

```powershell
npm run compile
```

## Run In VS Code

1. Open this folder in VS Code
2. Press `F5`
3. In the Extension Development Host window, open a file
4. Run commands from the Command Palette

## Backend Requirement

Make sure your FastAPI backend is running at:

```text
http://127.0.0.1:8000
```

You can change that in VS Code settings:

```text
agent.backendUrl
```

## Current Integration Notes

- The extension sends structured payloads to `/chat`
- The backend now accepts fields like `task`, `filePath`, `language`, `code`, `selection`, `workspaceRoot`, and `openFiles`
- The first version shows responses in notifications/output instead of applying diffs automatically

## Recommended Next Steps

- Add a sidebar chat webview
- Return structured file edits from the backend
- Add diff preview before applying changes
- Add streaming responses
- Add cancellation support
