# Innovex AI Agent

`Innovex AI Agent` is a VS Code extension backed by a local FastAPI service. It lets users chat with an AI coding agent, fix the current file, generate tests, validate a workspace, and apply returned file changes directly inside VS Code.

## What Users Can Do

- Chat with the agent from the Command Palette
- Ask the agent to complete a coding task
- Fix the currently open file
- Generate tests for the current file
- Validate the current workspace or file
- Auto-apply changed files returned by the backend

## Commands

Open the Command Palette and run:

- `Innovex AI: Chat`
- `Innovex AI: Complete Task`
- `Innovex AI: Fix Current File`
- `Innovex AI: Generate Tests`
- `Innovex AI: Validate Workspace`

Some commands also appear in the editor right-click context menu.

## Extension Settings

This extension contributes these settings:

- `agent.backendUrl`
  - Default: `http://127.0.0.1:8000`
  - Points VS Code to the local FastAPI backend
- `agent.autoApplyChanges`
  - Default: `true`
  - Automatically writes backend-returned file edits into the workspace

## Local Development Setup

### 1. Start the backend

From the repository root:

```powershell
start_backend.bat
```

This starts the FastAPI app on:

```text
http://127.0.0.1:8000
```

### 2. Compile the extension

From the repository root:

```powershell
npm install
npm run compile
```

### 3. Run the extension in VS Code

Open this repo in VS Code and press `F5`.

That launches an Extension Development Host where you can test the extension locally.

## Build A Local Installable VSIX

To create a local extension package:

```powershell
npm install
npm run package:vsix
```

That produces a `.vsix` file in the project root.

To install it locally:

```powershell
code --install-extension .\innovex-ai-agent-0.1.0.vsix
```

Or in VS Code:

1. Open Extensions
2. Select the `...` menu
3. Choose `Install from VSIX...`
4. Pick the generated `.vsix` file

## Can Users Search For It In The Extensions Tab?

Yes, but only after you publish it to the Visual Studio Marketplace.

Right now this repository can be packaged and installed locally as a `.vsix`, but it will not appear in the public Extensions search until you:

1. Create a real publisher account in Azure DevOps / Visual Studio Marketplace
2. Replace `"publisher": "local"` in `package.json` with your real publisher ID
3. Publish the extension with `vsce publish`

After that, users can:

1. Open the VS Code Extensions panel
2. Search for `Innovex AI Agent`
3. Click `Install`
4. Start using it on their local machine

## Publish To Marketplace

Typical publish flow:

```powershell
npm install
npm run compile
npx @vscode/vsce login <your-publisher-id>
npx @vscode/vsce publish
```

Before publishing, make sure:

- the backend setup instructions are correct
- your publisher name is real
- your extension metadata is finalized
- you add a license if you intend to distribute it publicly
- you test the `.vsix` locally first

## Project Structure

```text
vscodeex/
|-- src/
|   |-- commands/
|   |-- services/
|   |-- extension.ts
|-- dist/
|-- backend/
|   |-- app/
|   |-- workspace/
|-- package.json
|-- tsconfig.json
|-- start_backend.bat
```

## Notes

- The extension depends on the local backend being available
- If the backend is not running, commands will fail when they call `/chat`
- The extension currently targets local development and local-agent workflows

## Current Status

This repository is now set up to behave like a real VS Code extension project:

- extension manifest present
- commands contributed
- activation events configured
- local `.vsix` packaging script added
- local install flow documented

Marketplace search and one-click public install still require a real publisher and an actual publish step.
