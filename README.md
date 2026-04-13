# AI Coding Agent Backend

This project is a FastAPI-based coding agent backend that accepts natural-language requests over HTTP, plans tool-driven steps, edits files inside a local workspace, runs commands, and stores lightweight memory for later context.

The backend is designed around a simple agent loop:

1. Receive a user message through `POST /chat`
2. Search memory for related context
3. Either answer a question or execute a coding workflow
4. Use model output to choose one tool call at a time
5. Read, write, and run code inside `backend/workspace`
6. If a target code file fails, automatically attempt to fix it and verify the fix

## Features

- FastAPI API server with a `/chat` endpoint
- Multi-model routing across Groq, Gemini, and Hugging Face fallback
- Autonomous execution mode with iterative plan -> act -> evaluate loops
- Adjustable intelligence level (`medium`, `high`, `very_high`) for deeper reasoning
- Tool-based agent loop using:
  - `read_file`
  - `write_file`
  - `run_command`
- Automatic code repair flow for prompts like `Fix the code in app.py`
- Automatic test generation and validation for Python files
- ChromaDB-backed memory store for lightweight retrieval
- Local sentence-transformer embeddings with safe fallback when unavailable
- Workspace isolation for generated and edited files

## Project Structure

```text
vscodeex/
├── README.md
├── backend/
│   ├── requirements.txt
│   ├── workspace/
│   │   └── app.py
│   └── app/
│       ├── main.py
│       ├── core/
│       │   └── config.py
│       ├── memory/
│       │   ├── embedder.py
│       │   └── vector_store.py
│       ├── models/
│       │   ├── base_model.py
│       │   ├── gemini.py
│       │   ├── groq.py
│       │   └── huggingface.py
│       ├── routes/
│       │   └── chat.py
│       ├── services/
│       │   ├── agent_service.py
│       │   └── model_router.py
│       └── tools/
│           ├── tool_manager.py
│           ├── file_tools/
│           │   ├── edit_file.py
│           │   ├── read_file.py
│           │   └── write_file.py
│           └── terminal/
│               ├── executor.py
│               └── validator.py
└── gemini_env/
```

## How It Works

### 1. API Layer

The FastAPI app is defined in `backend/app/main.py`.

- `GET /` returns a simple health-style message
- `POST /chat` accepts a JSON body with a single `message` field

Example request body:

```json
{
  "message": "Fix the code in app.py"
}
```

Example response:

```json
{
  "response": "Fixed app.py\nHello, World!"
}
```

### 2. Agent Service

The main orchestration lives in `backend/app/services/agent_service.py`.

It handles:

- memory lookup
- question detection
- task planning
- tool-call parsing
- tool execution
- automatic debugging and file repair

There are two main modes:

- Question mode
  - If the input looks like a question, the agent answers using memory context
- Action mode
  - If the input is a coding task, the agent creates and executes a step-by-step tool workflow

### 3. Automatic Code Fixing

The backend now includes a dedicated repair path for fix-style prompts.

When a user sends something like:

```text
Fix the code in app.py
```

the agent will:

1. Extract the file path from the prompt
2. Read the file from `backend/workspace`
3. Run the file if it is Python
4. Detect whether the execution failed
5. Ask the model for corrected source code
6. Reject placeholder outputs like `corrected_code`
7. Write the repaired code back to disk
8. Re-run the file to verify that it now works
9. Return a result such as:

```text
Fixed app.py
Hello, World!
```

This is the main improvement made to the current codebase: the agent no longer stops after reading broken code or returning a success-looking string. It now performs an actual fix-and-verify workflow.

### 4. Automatic Test Generation and Validation

The agent now performs a lightweight AI CI pass for Python files.

After creating or fixing a Python file, it can:

1. Read the latest source code
2. Generate a `unittest` file under `backend/workspace/tests`
3. Run:

```text
python -m unittest discover -s tests -p "test_*.py" -v
```

4. Inspect the validation result
5. If validation fails, ask the model to repair the source code and retry

This gives the agent a more realistic CI/CD-style behavior:

- generate code
- generate tests
- validate automatically
- repair from validation failures
- return success only after verification

### 5. Tool System

The tool registry lives in `backend/app/tools/tool_manager.py`.

Current tools:

- `read_file`
  - Reads a file from `backend/workspace`
- `write_file`
  - Writes or creates a file inside `backend/workspace`
- `run_command`
  - Executes a shell command with the current working directory set to `backend/workspace`
- `edit_file`
  - Present in the tool layer, but not used by the main agent loop

The tool manager normalizes execution and returns string responses for the agent loop.

### 6. Model Routing

Model selection is handled in `backend/app/services/model_router.py`.

Configured models:

- Gemini
  - `gemini-2.5-pro`
  - `gemini-2.5-flash`
- Groq
  - `llama-3.3-70b-versatile`
  - `llama-3.1-8b-instant`
- Hugging Face fallback
  - `deepseek-ai/deepseek-coder-6.7b`

Routing strategy:

- `complex`
  - prefers stronger reasoning models
- `fast`
  - prefers lower-latency models
- `agent`
  - prioritizes fast agent-loop responses

### 7. Memory

Memory is stored with ChromaDB in `backend/app/memory/vector_store.py`.

Embeddings are generated in `backend/app/memory/embedder.py` using:

- `sentence-transformers/all-MiniLM-L6-v2`

The embedder now lazy-loads the embedding model. If the embedding model is unavailable, the system falls back to a zero vector instead of crashing on import. That keeps the API usable in restricted or partially configured environments.

## Setup

### Prerequisites

- Python 3.10+ recommended
- A virtual environment
- API keys for:
  - Gemini
  - Groq
- Optional:
  - Hugging Face API key

### Install Dependencies

From the `backend` directory:

```powershell
pip install -r requirements.txt
```

Important: the current `requirements.txt` is incomplete for all runtime features used by the codebase. In addition to the listed packages, the project also uses libraries such as:

- `requests`
- `chromadb`
- `sentence-transformers`

If those are not already installed in your environment, you should install them manually.

Example:

```powershell
pip install requests chromadb sentence-transformers
```

### Environment Variables

Create a `.env` file inside `backend/` with:

```env
GEMINI_API_KEY=your_gemini_key
GROQ_API_KEY=your_groq_key
HF_API_KEY=your_huggingface_key
HF_IMAGE_API_URL=https://<endpoint-id>.<region>.endpoints.huggingface.cloud/
```

Notes:

- `HF_API_KEY` is optional in the current code
- `HF_IMAGE_API_URL` is recommended for image generation because a dedicated Inference Endpoint is more reliable than a public model URL
- Gemini and Groq are the primary model providers

## Running the Server

From the `backend` directory:

```powershell
uvicorn app.main:app --reload
```

Default local server:

```text
http://127.0.0.1:8000
```

## Running The Frontend

From the `frontend` directory:

```powershell
python -m http.server 5500
```

Then open:

```text
http://127.0.0.1:5500
```

The frontend supports:
- chat/fix/test/validate requests
- autonomous mode toggle
- intelligence level selection
- updated files viewer

## API Usage

### Health Check

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/" -Method Get
```

### Chat Request

```powershell
Invoke-RestMethod -Uri "http://127.0.0.1:8000/chat" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"message": "Fix the code in app.py", "autonomousMode": true, "intelligenceLevel": "high"}'
```

### Example Prompts

- `Create a Python file named app.py with hello world code`
- `Fix the code in app.py`
- `Create a calculator in calc.py and validate it`
- `Read app.py`
- `Run app.py`

## Workspace Behavior

All file operations are scoped to:

```text
backend/workspace
```

That means:

- `read_file("app.py")` reads `backend/workspace/app.py`
- `write_file("app.py", "...")` writes to `backend/workspace/app.py`
- `run_command("python app.py")` runs from `backend/workspace`

This keeps generated code separate from backend source files.

## Core Files

### `backend/app/main.py`

- Creates the FastAPI app
- Loads the chat router
- Logs whether Gemini and Groq keys are available

### `backend/app/routes/chat.py`

- Defines the `/chat` endpoint
- Accepts a `message`
- Returns the agent response

### `backend/app/services/agent_service.py`

- Main orchestration layer
- Parses model tool output
- Executes file and terminal tools
- Stores memory
- Runs the auto-fix workflow for broken code

### `backend/app/services/model_router.py`

- Chooses which model to call based on task type
- Falls back across providers if one fails

### `backend/app/tools/tool_manager.py`

- Central tool dispatcher
- Standardizes execution and return strings

### `backend/app/tools/terminal/executor.py`

- Executes shell commands inside the workspace
- Captures stdout and stderr

### `backend/app/memory/vector_store.py`

- Stores and retrieves memory snippets using ChromaDB

### `backend/app/memory/embedder.py`

- Generates embeddings
- Uses lazy model loading
- Falls back safely if the embedding model is unavailable

## Current Limitations

- `requirements.txt` does not list every package currently used by the codebase
- `validator.py` exists, but `run_command` does not currently use it
- `edit_file.py` writes directly to the given path and is not workspace-scoped
- `read_file.py` and `write_file.py` still return some legacy error strings with non-ASCII characters
- `GeminiModel` exposes `generate_with_tools`, but the router currently calls `.generate(...)`, so Gemini may need an adapter method to participate fully in all routes
- Memory depends on ChromaDB and sentence-transformers being installed

## Recommended Improvements

- Add all missing runtime packages to `backend/requirements.txt`
- Make all tool responses consistently ASCII-safe
- Integrate `validator.py` into `run_command` for command safety checks
- Align all model classes to a shared interface
- Add tests for:
  - planning
  - tool parsing
  - broken-file repair
  - workspace path normalization
- Add request/response schemas and API docs examples
- Improve file type support beyond Python

## Example End-to-End Flow

If `backend/workspace/app.py` contains:

```python
print('Hello, World!'),.
```

and the user sends:

```text
Fix the code in app.py
```

the backend now performs this sequence:

1. Read `app.py`
2. Execute `python app.py`
3. Capture the syntax error
4. Ask the model for corrected code
5. Write:

```python
print('Hello, World!')
```

6. Generate `tests/test_app.py`
7. Run automated validation with `unittest discover`
8. Re-run `python app.py`
9. Return:

```text
Fixed app.py
Hello, World!

Validation passed for app.py
...
OK
```

## Development Notes

- The backend is currently optimized for local development and experimentation
- The design is intentionally simple: one HTTP endpoint, one main agent service, and a small tool surface
- The memory layer is best-effort and should not block the API from running

## License

No license file is currently present in this repository. Add one if you plan to distribute or open-source the project.
#   i n n o v e x . a i . a g e n t  
 