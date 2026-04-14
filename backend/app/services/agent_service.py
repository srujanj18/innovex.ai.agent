import json
import os
import re
import ast
from typing import Any

from app.memory.vector_store import VectorStore
from app.models.huggingface import HFModel
from app.services.model_router import ModelRouter
from app.tools.tool_manager import ToolManager
from app.tools.path_utils import get_workspace_root, resolve_workspace_path

router = ModelRouter()
memory = VectorStore()
hf_image_model = HFModel()

VALID_TOOLS = ["write_file", "read_file", "run_command"]

TOOL_ALIASES = {
    "code_editor": "write_file",
    "file_creator": "write_file",
    "create_file": "write_file",
    "edit_file": "write_file",
}

PLACEHOLDER_PATTERNS = [
    "corrected_code",
    "your_code_here",
    "fixed_code",
    "<fix>",
    "# your fix here",
    "from your_app import",
]


def clean_text(text: str) -> str:
    return re.sub(r"```json|```python|```", "", text).strip()


def extract_all_json(text: str) -> list:
    text = clean_text(text)
    blocks, stack, start = [], 0, None

    for i, ch in enumerate(text):
        if ch == "{":
            if stack == 0:
                start = i
            stack += 1
        elif ch == "}":
            stack -= 1
            if stack == 0 and start is not None:
                blocks.append(text[start : i + 1])

    return blocks


def normalize_path(path: str) -> str:
    if not path:
        return path

    root = get_workspace_root()
    normalized = path.replace("/", "\\").strip().strip("\"'")

    restored = normalized
    drive, _ = os.path.splitdrive(root)
    if drive and not os.path.splitdrive(restored)[0]:
        trimmed = restored.lstrip("\\")
        if trimmed.startswith("Users\\") or trimmed.startswith("Program Files\\"):
            restored = f"{drive}\\{trimmed}"

    if os.path.isabs(restored):
        absolute = os.path.abspath(restored)
        try:
            if os.path.commonpath([root, absolute]) == root:
                return os.path.relpath(absolute, root).replace("/", "\\")
        except ValueError:
            pass
        return os.path.basename(absolute)

    lowered = restored.lower()
    if lowered.startswith("workspace\\"):
        trimmed = restored.lstrip("\\")
        return f"backend\\{trimmed}"

    return restored.lstrip("\\")


def clean_command(cmd) -> str:
    if not cmd:
        return cmd
    if isinstance(cmd, list):
        cmd = " ".join(cmd)
    return cmd


def is_question(text: str) -> bool:
    return any(q in text.lower() for q in ["what", "which", "who", "where", "when"])


def extract_task_name(text: str) -> str:
    match = re.search(r"^Task:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip().lower() if match else ""


def extract_user_request(text: str) -> str:
    if not text:
        return text

    split_markers = ["\n\nTask:", "\nTask:", "\n\nFile path:", "\nFile path:"]
    for marker in split_markers:
        if marker in text:
            return text.split(marker, 1)[0].strip()

    return text.strip()


def looks_like_generation_request(text: str) -> bool:
    lowered = text.lower()
    triggers = [
        "generate",
        "create",
        "write code",
        "build",
        "make a python",
        "make python",
        "python code",
    ]
    return any(trigger in lowered for trigger in triggers)


def looks_like_website_request(text: str) -> bool:
    lowered = text.lower()
    website_terms = [
        "website",
        "landing page",
        "web page",
        "web app",
        "frontend",
        "html",
        "css",
        "javascript",
    ]
    return any(term in lowered for term in website_terms)


def looks_like_python(path: str) -> bool:
    return bool(path) and path.lower().endswith(".py")


def extract_file_paths(text: str) -> list[str]:
    if not text:
        return []

    matches = re.findall(r"[\w./\\-]+\.\w+", text)
    unique_paths = []

    for match in matches:
        normalized = normalize_path(match.strip("\"'"))
        if normalized not in unique_paths:
            unique_paths.append(normalized)

    return unique_paths


def extract_folder_name(text: str) -> str:
    patterns = [
        r"(?:new\s+folder|folder)\s+(?:named|called)\s+['\"]?([\w./\\-]+)['\"]?",
        r"(?:inside|in)\s+(?:a\s+new\s+folder\s+)?['\"]?([\w./\\-]+)['\"]?\s*(?:folder)?",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            candidate = match.group(1).strip().strip("\"'")
            candidate = candidate.rstrip(".,)")
            if candidate and "." not in os.path.basename(candidate):
                return normalize_path(candidate)

    return "website"


def build_run_command(path: str) -> str:
    ext = os.path.splitext(path)[1].lower()
    if ext == ".py":
        return f"python {path}"
    return ""


def build_test_command(file_path: str) -> str:
    test_path = derive_test_path(file_path)
    module_name = test_path.replace("\\", ".").replace("/", ".")
    if module_name.lower().endswith(".py"):
        module_name = module_name[:-3]
    return f"python -m unittest {module_name} -v"


def derive_test_path(file_path: str) -> str:
    base_name = os.path.splitext(os.path.basename(file_path))[0]
    return f"tests\\test_{base_name}.py"


def extract_python_functions(code: str) -> list[str]:
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return []

    function_names = []
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            function_names.append(node.name)
    return function_names


def safe_encode(text: str) -> str:
    if isinstance(text, bytes):
        text = text.decode("utf-8", errors="replace")
    return text.encode("utf-8", errors="replace").decode("utf-8")


def is_tool_error_result(text: str) -> bool:
    lowered = (text or "").lower()
    error_markers = [
        "error",
        "not found",
        "unknown tool",
        "parameter mismatch",
        "timed out",
        "traceback",
        "syntaxerror",
        "nameerror",
        "typeerror",
        "valueerror",
        "modulenotfounderror",
    ]
    return any(marker in lowered for marker in error_markers)


def is_text_web_file(path: str) -> bool:
    allowed_extensions = {".html", ".css", ".js", ".json", ".md", ".txt", ".svg"}
    return os.path.splitext(path)[1].lower() in allowed_extensions


def contains_placeholder_site_copy(text: str) -> bool:
    lowered = (text or "").lower()
    markers = [
        "lorem ipsum",
        "your brand here",
        "coming soon",
    ]
    return any(marker in lowered for marker in markers)


def looks_like_ecommerce_request(text: str) -> bool:
    lowered = text.lower()
    return any(term in lowered for term in ["ecommerce", "e-commerce", "shop", "store", "product"])


def safe_parse(ai_response: str) -> dict:
    blocks = extract_all_json(ai_response)

    if not blocks:
        raise Exception("No JSON found")

    for block in blocks:
        try:
            data = json.loads(block)
            tool = data.get("tool") or data.get("function")

            if "files" in data and isinstance(data["files"], dict):
                file_name = list(data["files"].keys())[0]
                content = data["files"][file_name]
                return {
                    "tool": "write_file",
                    "args": {"path": file_name, "content": content},
                }

            if "input" in data and isinstance(data["input"], dict):
                args = data["input"]
            elif "result" in data and isinstance(data["result"], dict):
                result_block = data["result"]
                args = {}
                for key in ("file_name", "filename", "file_path", "path", "file"):
                    if key in result_block:
                        args["path"] = result_block[key]
                        break
                if "content" in result_block:
                    args["content"] = result_block["content"]
            else:
                args = data.get("args") or data.get("params") or {}

            if isinstance(args, dict):
                for old_key in ("file_path", "filename", "file"):
                    if old_key in args:
                        args["path"] = args.pop(old_key)

                if "text" in args and "content" not in args:
                    args["content"] = args.pop("text")

            if "command" in data and tool == "run_command":
                if not isinstance(args, dict):
                    args = {}
                args["command"] = data["command"]

            if isinstance(args, list):
                if tool == "write_file":
                    args = {"path": args[0], "content": args[1] if len(args) > 1 else ""}
                elif tool == "read_file":
                    args = {"path": args[0]}
                elif tool == "run_command":
                    args = {"command": " ".join(args)}

            if isinstance(args, dict) and "args" in args:
                extra = args.pop("args")
                if isinstance(extra, list):
                    extra = " ".join(extra)
                args["command"] = f"{args.get('command', '')} {extra}".strip()

            if tool in VALID_TOOLS:
                return {"tool": tool, "args": args}

        except Exception:
            continue

    raise Exception("No valid tool JSON found")


class AgentService:
    def __init__(self, workspace_root: str | None = None):
        self.workspace_root = get_workspace_root(workspace_root)
        self.tools = ToolManager(self.workspace_root)

    def plan(self, user_input: str, intelligence_level: str = "high") -> dict[str, Any]:
        planning_depth = "deep" if intelligence_level.lower() in {"high", "very_high"} else "balanced"
        prompt = f"""
You are planning an autonomous coding task executor.

Task: {user_input}
Planning depth: {planning_depth}
Available tools: write_file, read_file, run_command

Return JSON only using this schema:
{{
  "objective": "one sentence mission",
  "success_criteria": ["criterion 1", "criterion 2"],
  "max_iterations": 12,
  "steps": ["step 1", "step 2", "step 3"]
}}

Rules:
- steps are plain-English actions, not code
- keep steps concrete and execution-ready
- max_iterations must be between 4 and 20
"""
        default_plan = {
            "objective": extract_user_request(user_input),
            "success_criteria": ["Requested task completed without tool errors."],
            "max_iterations": 12,
            "steps": [extract_user_request(user_input)],
        }
        try:
            res = router.generate(prompt, task_type="complex")
            parsed = json.loads(extract_all_json(res)[0])
            steps = parsed.get("steps") if isinstance(parsed.get("steps"), list) else []
            success_criteria = (
                parsed.get("success_criteria") if isinstance(parsed.get("success_criteria"), list) else default_plan["success_criteria"]
            )
            max_iterations = parsed.get("max_iterations", 12)
            if not isinstance(max_iterations, int):
                max_iterations = 12
            max_iterations = max(4, min(20, max_iterations))

            return {
                "objective": (parsed.get("objective") or default_plan["objective"]).strip(),
                "success_criteria": [str(item).strip() for item in success_criteria if str(item).strip()] or default_plan["success_criteria"],
                "max_iterations": max_iterations,
                "steps": [str(step).strip() for step in steps if str(step).strip()] or default_plan["steps"],
            }
        except Exception:
            return default_plan

    def _normalize_tool_request(self, data: dict) -> tuple[str, dict] | tuple[None, None]:
        tool = TOOL_ALIASES.get(data.get("tool"), data.get("tool"))
        args = data.get("args", {})

        if tool not in VALID_TOOLS or not isinstance(args, dict):
            return None, None

        if "path" in args:
            args["path"] = normalize_path(args["path"])
        if "command" in args:
            args["command"] = clean_command(args["command"])

        if tool == "write_file":
            raw_content = args.get("content", "")
            if not isinstance(raw_content, str):
                return None, None
            content = raw_content.strip().lower()
            if content in {"corrected_code", "your_code_here", "fixed_code", ""}:
                return None, None

        return tool, args

    def _decide_next_action(
        self,
        user_request: str,
        plan_bundle: dict[str, Any],
        history: list[dict[str, Any]],
        iteration: int,
    ) -> dict[str, Any]:
        steps = plan_bundle.get("steps", [user_request])
        step_index = min(iteration, max(0, len(steps) - 1))
        current_step = steps[step_index] if steps else user_request
        recent_history = history[-6:]

        prompt = f"""
You are an autonomous coding agent controller.
Choose exactly ONE action.

Objective: {plan_bundle.get("objective", user_request)}
Success criteria: {plan_bundle.get("success_criteria", [])}
Current step: {current_step}
User request: {user_request}
Iteration: {iteration + 1}
Recent history (JSON): {json.dumps(recent_history)}

Return JSON only in one of these forms:
1) Tool action:
{{
  "action": "tool",
  "tool": "read_file|write_file|run_command",
  "args": {{}}
}}
2) Finish:
{{
  "action": "finish",
  "message": "short final response"
}}

Rules:
- If not complete, choose tool action.
- Prefer reading before editing unknown files.
- write_file content must be full final file content.
- No markdown, no explanations.
"""
        raw = router.generate(prompt, task_type="agent")
        blocks = extract_all_json(raw)
        if not blocks:
            return {"action": "tool", "tool": "read_file", "args": {"path": self._extract_primary_target(user_request)}}

        try:
            action_data = json.loads(blocks[0])
        except Exception:
            return {"action": "tool", "tool": "read_file", "args": {"path": self._extract_primary_target(user_request)}}

        action = str(action_data.get("action", "")).strip().lower()
        if action == "finish":
            message = action_data.get("message", "")
            if isinstance(message, str) and message.strip():
                return {"action": "finish", "message": message.strip()}
            return {"action": "finish", "message": "Task completed."}

        return {
            "action": "tool",
            "tool": action_data.get("tool"),
            "args": action_data.get("args", {}),
        }

    def _evaluate_completion(
        self,
        user_request: str,
        plan_bundle: dict[str, Any],
        history: list[dict[str, Any]],
    ) -> dict[str, Any]:
        if not history:
            return {"done": False, "summary": "", "next_focus": ""}

        recent_history = history[-8:]
        prompt = f"""
Decide if the task is complete.

User request: {user_request}
Objective: {plan_bundle.get("objective", user_request)}
Success criteria: {plan_bundle.get("success_criteria", [])}
Recent execution history (JSON): {json.dumps(recent_history)}

Return JSON only:
{{
  "done": true or false,
  "summary": "short user-facing summary",
  "next_focus": "what to do next if not done"
}}
"""
        try:
            raw = router.generate(prompt, task_type="complex")
            evaluation = json.loads(extract_all_json(raw)[0])
            return {
                "done": bool(evaluation.get("done")),
                "summary": str(evaluation.get("summary", "")).strip(),
                "next_focus": str(evaluation.get("next_focus", "")).strip(),
            }
        except Exception:
            last_result = str(history[-1].get("result", ""))
            done = not is_tool_error_result(last_result)
            return {
                "done": done,
                "summary": "Task completed." if done else "",
                "next_focus": "" if done else "Address the latest tool error.",
            }

    def _run_autonomous_loop(self, user_input: str, intelligence_level: str = "high") -> str:
        user_request = extract_user_request(user_input)
        plan_bundle = self.plan(user_request, intelligence_level=intelligence_level)
        print("AUTO PLAN:", plan_bundle)

        max_iterations = plan_bundle.get("max_iterations", 12)
        history: list[dict[str, Any]] = []
        last_result = "No result produced."

        for iteration in range(max_iterations):
            decision = self._decide_next_action(user_request, plan_bundle, history, iteration)
            print("AUTO DECISION:", decision)

            if decision.get("action") == "finish":
                return decision.get("message", "Task completed.")

            tool, args = self._normalize_tool_request(decision)
            if not tool:
                last_result = "Error: Agent produced an invalid tool action."
                continue

            result = self.tools.execute(tool, args)
            print("AUTO RESULT:", result)
            last_result = result

            memory.add(
                doc_id=f"auto_{tool}_{len(history)}",
                content=f"{args} -> {result[:120]}",
            )
            history.append({"tool": tool, "args": args, "result": result})

            if is_tool_error_result(result):
                file_path = args.get("path", self._extract_primary_target(user_request))
                repaired = self._debug_and_fix(result, file_path, history)
                history.append({"tool": "auto_repair", "args": {"path": file_path}, "result": repaired})
                last_result = repaired

            if tool == "write_file" and looks_like_python(args.get("path", "")):
                validation_result = self._validate_python_file(args["path"], history)
                if validation_result:
                    history.append({"tool": "validate_python", "args": {"path": args["path"]}, "result": validation_result})
                    last_result = validation_result if is_tool_error_result(validation_result) else f"{result}\n\n{validation_result}".strip()

            evaluation = self._evaluate_completion(user_request, plan_bundle, history)
            print("AUTO EVAL:", evaluation)
            if evaluation.get("done"):
                summary = evaluation.get("summary", "").strip()
                return summary or safe_encode(last_result)

        return safe_encode(last_result)

    def answer(self, user_input: str, context: str) -> str:
        return router.generate(
            f"""
Answer the question using the memory context below. Be concise and factual.

Context:
{context}

Question: {user_input}
"""
        )

    def _is_placeholder(self, text: str) -> bool:
        lowered = (text or "").lower()
        return any(pattern in lowered for pattern in PLACEHOLDER_PATTERNS)

    def _extract_primary_target(self, user_input: str) -> str:
        targets = extract_file_paths(user_input)
        return targets[0] if targets else "app.py"

    def _fallback_website_files(self, folder_path: str, user_input: str) -> dict[str, str]:
        folder_name = os.path.basename(folder_path.rstrip("\\/")) or "website"
        title = folder_name.replace("-", " ").replace("_", " ").title()
        description = clean_text(user_input).replace("\n", " ")
        hero_image = "https://images.unsplash.com/photo-1523275335684-37898b6baf30?auto=format&fit=crop&w=1400&q=80"
        card_image_one = "https://images.unsplash.com/photo-1483985988355-763728e1935b?auto=format&fit=crop&w=900&q=80"
        card_image_two = "https://images.unsplash.com/photo-1512436991641-6745cdb1723f?auto=format&fit=crop&w=900&q=80"
        card_image_three = "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?auto=format&fit=crop&w=900&q=80"

        if not looks_like_ecommerce_request(user_input):
            hero_image = "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1400&q=80"
            card_image_one = "https://images.unsplash.com/photo-1516321318423-f06f85e504b3?auto=format&fit=crop&w=900&q=80"
            card_image_two = "https://images.unsplash.com/photo-1498050108023-c5249f4df085?auto=format&fit=crop&w=900&q=80"
            card_image_three = "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?auto=format&fit=crop&w=900&q=80"

        return {
            f"{folder_path}\\index.html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <main class="page">
    <section class="hero">
      <div class="hero-copy">
        <p class="eyebrow">Generated Site</p>
        <h1>{title}</h1>
        <p class="lede">{description}</p>
        <div class="actions">
          <a class="button primary" href="#features">Shop Highlights</a>
          <a class="button secondary" href="#contact">Get in Touch</a>
        </div>
      </div>
      <div class="hero-media">
        <img data-image-key="hero-image.jpg" src="{hero_image}" alt="{title} featured product collection" />
      </div>
    </section>
    <section id="features" class="card-grid">
      <article class="card">
        <img data-image-key="product-1.jpg" src="{card_image_one}" alt="Featured collection one" />
        <h2>Featured Drop</h2>
        <p>Discover standout products with modern presentation and clear calls to action.</p>
      </article>
      <article class="card">
        <img data-image-key="product-2.jpg" src="{card_image_two}" alt="Featured collection two" />
        <h2>Responsive Storefront</h2>
        <p>Built to adapt across desktop and mobile screens without losing visual impact.</p>
      </article>
      <article class="card">
        <img data-image-key="product-3.jpg" src="{card_image_three}" alt="Featured collection three" />
        <h2>Easy Editing</h2>
        <p>Simple HTML, CSS, and JavaScript files that are easy to customize for your brand.</p>
      </article>
    </section>
    <section id="contact" class="cta">
      <h2>Ready to customize?</h2>
      <p>Edit the content, colors, and interactions to match your project.</p>
      <button id="demo-button" class="button primary" type="button">Try Interaction</button>
      <p id="demo-output" class="demo-output" aria-live="polite"></p>
    </section>
  </main>
  <script src="script.js"></script>
</body>
</html>
""",
            f"{folder_path}\\styles.css": """:root {
  --bg: #f7f1e8;
  --surface: rgba(255, 252, 248, 0.82);
  --text: #171515;
  --muted: #635a52;
  --accent: #d25f2d;
  --accent-dark: #8e3d1b;
  --border: rgba(23, 21, 21, 0.08);
  --shadow: 0 20px 60px rgba(77, 45, 20, 0.14);
}

* {
  box-sizing: border-box;
}

body {
  margin: 0;
  font-family: Georgia, "Times New Roman", serif;
  color: var(--text);
  background:
    radial-gradient(circle at top, rgba(255, 255, 255, 0.9), transparent 35%),
    linear-gradient(135deg, #f7d7b8, #f6efe5 55%, #eadfd2);
  min-height: 100vh;
}

.page {
  width: min(1100px, calc(100% - 32px));
  margin: 0 auto;
  padding: 48px 0 64px;
}

.hero,
.card,
.cta {
  backdrop-filter: blur(14px);
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: 24px;
  box-shadow: var(--shadow);
}

.hero {
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  gap: 28px;
  align-items: center;
  padding: 56px;
}

.hero-copy {
  text-align: left;
}

.hero-media img,
.card img {
  width: 100%;
  display: block;
  object-fit: cover;
}

.hero-media img {
  min-height: 420px;
  border-radius: 24px;
}

.card img {
  height: 220px;
  border-radius: 18px;
  margin-bottom: 18px;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  color: var(--accent-dark);
  font-size: 0.8rem;
}

h1,
h2,
p {
  margin-top: 0;
}

h1 {
  font-size: clamp(2.8rem, 8vw, 5.5rem);
  margin-bottom: 16px;
}

.lede {
  width: min(720px, 100%);
  margin: 0 auto 28px;
  color: var(--muted);
  font-size: 1.1rem;
  line-height: 1.7;
}

.actions {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 999px;
  padding: 14px 22px;
  text-decoration: none;
  border: none;
  cursor: pointer;
  font: inherit;
  transition: transform 160ms ease, opacity 160ms ease, background 160ms ease;
}

.button:hover {
  transform: translateY(-2px);
}

.button.primary {
  background: var(--accent);
  color: white;
}

.button.secondary {
  background: transparent;
  color: var(--text);
  border: 1px solid var(--border);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 20px;
  margin: 28px 0;
}

.card,
.cta {
  padding: 28px;
}

.card p,
.cta p,
.demo-output {
  color: var(--muted);
  line-height: 1.6;
}

@media (max-width: 800px) {
  .hero {
    grid-template-columns: 1fr;
    padding: 32px 20px;
  }

  .hero-copy {
    text-align: center;
  }

  .actions {
    justify-content: center;
  }

  .card-grid {
    grid-template-columns: 1fr;
  }
}
""",
            f"{folder_path}\\script.js": """const button = document.getElementById("demo-button");
const output = document.getElementById("demo-output");

if (button && output) {
  button.addEventListener("click", () => {
    output.textContent = "Interaction works. This site is ready for the next round of customization.";
  });
}

fetch("image-sources.json")
  .then((response) => response.ok ? response.json() : {})
  .then((sources) => {
    document.querySelectorAll("[data-image-key]").forEach((image) => {
      const key = image.getAttribute("data-image-key");
      const source = key ? sources[key] : "";
      if (source) {
        image.setAttribute("src", source);
      }
    });
  })
  .catch(() => {
    console.log("Using default image sources");
  });
""",
            f"{folder_path}\\image-sources.json": json.dumps(
                {
                    "hero-image.jpg": hero_image,
                    "product-1.jpg": card_image_one,
                    "product-2.jpg": card_image_two,
                    "product-3.jpg": card_image_three,
                },
                indent=2,
            ),
        }

    def _write_binary_file(self, path: str, content: bytes) -> str:
        try:
            full_path = resolve_workspace_path(path, self.workspace_root)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as file_handle:
                file_handle.write(content)
            self.tools.changed_files.add(normalize_path(path))
            return f"File written: {full_path}"
        except Exception as error:
            return f"Error writing binary file: {error}"

    def _generate_website_images(self, folder_path: str, user_input: str) -> dict[str, str]:
        prompts = {
            f"{folder_path}\\hero-image.jpg": f"High-end hero image for website: {user_input}. Clean studio lighting, premium product photography, ecommerce banner composition.",
            f"{folder_path}\\product-1.jpg": f"Product showcase image for website: {user_input}. Premium ecommerce catalog photography.",
            f"{folder_path}\\product-2.jpg": f"Lifestyle product image for website: {user_input}. Modern editorial ecommerce photography.",
            f"{folder_path}\\product-3.jpg": f"Close-up feature image for website: {user_input}. Detailed product photography, premium brand style.",
        }
        fallback_sources = json.loads(self._fallback_website_files(folder_path, user_input)[f"{folder_path}\\image-sources.json"])

        for path, prompt in prompts.items():
            try:
                image_bytes = hf_image_model.generate_image(prompt)
                result = self._write_binary_file(path, image_bytes)
                if is_tool_error_result(result):
                    fallback_sources[os.path.basename(path)] = fallback_sources.get(os.path.basename(path), "")
            except Exception:
                continue

        return fallback_sources

    def _website_files_are_usable(self, folder_path: str, files: dict[str, str] | None) -> bool:
        if not files:
            return False

        normalized_folder = normalize_path(folder_path).rstrip("\\/")
        required_paths = {
            f"{normalized_folder}\\index.html",
            f"{normalized_folder}\\styles.css",
            f"{normalized_folder}\\script.js",
        }

        normalized_files = {normalize_path(path): content for path, content in files.items()}
        if not required_paths.issubset(set(normalized_files.keys())):
            return False

        for path, content in normalized_files.items():
            if not path.startswith(f"{normalized_folder}\\"):
                return False
            if not is_text_web_file(path):
                return False
            if not isinstance(content, str) or not content.strip():
                return False

        html = normalized_files.get(f"{normalized_folder}\\index.html", "")
        css = normalized_files.get(f"{normalized_folder}\\styles.css", "")
        js = normalized_files.get(f"{normalized_folder}\\script.js", "")

        if "<html" not in html.lower() or "<body" not in html.lower():
            return False
        if "script.js" not in html or "styles.css" not in html:
            return False
        if contains_placeholder_site_copy(html):
            return False
        if len(css.strip()) < 200 or len(js.strip()) < 40:
            return False

        return True

    def _generate_website(self, user_input: str) -> str:
        folder_path = extract_folder_name(user_input)
        prompt = f"""
You are generating a complete small static website.

USER REQUEST:
{user_input}

TARGET FOLDER:
{folder_path}

Return JSON only in this exact shape:
{{
  "files": {{
    "{folder_path}/index.html": "<full html>",
    "{folder_path}/styles.css": "<full css>",
    "{folder_path}/script.js": "<full javascript>"
  }}
}}

Rules:
- Create a complete frontend website, not a Python backend
- Always include at least index.html, styles.css, and script.js
- All files must live inside the target folder
- Only return text-based web files like html, css, js, json, md, txt, or svg
- Do NOT create binary or image placeholder files like jpg, jpeg, png, webp, or gif
- Use plain HTML, CSS, and JavaScript
- Make the page responsive and visually polished
- Avoid filler copy like Lorem ipsum
- Do not include markdown fences or explanations
"""
        files: dict[str, str] | None = None

        try:
            response = router.generate(prompt, task_type="agent")
            for block in extract_all_json(response):
                data = json.loads(block)
                candidate = data.get("files")
                if isinstance(candidate, dict) and candidate:
                    files = {
                        normalize_path(path): content
                        for path, content in candidate.items()
                        if isinstance(path, str) and isinstance(content, str)
                    }
                    break
        except Exception:
            files = None

        if not self._website_files_are_usable(folder_path, files):
            files = self._fallback_website_files(folder_path, user_input)

        written_files: list[str] = []
        for path, content in files.items():
            result = self.tools.execute("write_file", {"path": path, "content": content})
            if is_tool_error_result(result):
                return result
            written_files.append(path)

        image_sources = self._generate_website_images(folder_path, user_input)
        if image_sources:
            image_map_path = f"{folder_path}\\image-sources.json"
            image_map_result = self.tools.execute(
                "write_file",
                {"path": image_map_path, "content": json.dumps(image_sources, indent=2)},
            )
            if not is_tool_error_result(image_map_result) and image_map_path not in written_files:
                written_files.append(image_map_path)

        return f"Generated website in {folder_path} with files: {', '.join(written_files)}"

    def _generate_code_for_file(self, file_path: str, user_input: str) -> str:
        existing_code = self.tools.execute("read_file", {"path": file_path})
        if is_tool_error_result(existing_code):
            existing_code = ""

        prompt = f"""
You are generating code for a coding agent.

TARGET FILE: {file_path}
USER REQUEST:
{user_input}

CURRENT FILE CONTENTS:
{existing_code}

Rules:
- Return ONLY the full final source code for the target file
- Do NOT include markdown fences or explanations
- If the user asks for new code, replace the file with a clean implementation
- Prefer a simple, correct solution
"""
        generated_code = clean_text(router.generate(prompt, task_type="agent"))

        if not generated_code or self._is_placeholder(generated_code):
            return "Error: Could not generate valid code."

        write_result = self.tools.execute("write_file", {"path": file_path, "content": generated_code})
        if is_tool_error_result(write_result):
            return write_result

        validation_result = self._validate_python_file(file_path, [])
        if validation_result and not is_tool_error_result(validation_result):
            return f"Generated code for {file_path}\n\n{validation_result}".strip()
        if validation_result:
            return validation_result

        return f"Generated code for {file_path}"

    def _needs_fixing(self, user_input: str) -> bool:
        lowered = user_input.lower()
        triggers = ["fix", "error", "bug", "debug", "repair", "correct"]
        return any(trigger in lowered for trigger in triggers) and bool(extract_file_paths(user_input))

    def _fix_file_with_model(self, file_path: str, code: str, error: str = "") -> str:
        prompt = f"""
You are fixing a source file for a coding agent.

FILE: {file_path}
ERROR:
{error or "The user asked to fix this file and ensure it runs correctly."}

CURRENT CODE:
{code}

Rules:
- Return ONLY the full corrected source code
- Do NOT include markdown fences, JSON, or explanations
- Do NOT return placeholder names like corrected_code
- Preserve the original intent unless a change is needed to make the code valid and runnable
"""
        fixed_code = clean_text(router.generate(prompt, task_type="agent"))

        if self._is_placeholder(fixed_code) or not fixed_code.strip():
            return ""

        return fixed_code

    def _generate_tests_with_model(self, file_path: str, code: str) -> str:
        test_path = derive_test_path(file_path)
        module_name = os.path.splitext(os.path.basename(file_path))[0]
        function_names = extract_python_functions(code)
        prompt = f"""
You are generating automated validation tests for a Python file.

TARGET FILE: {file_path}
TARGET MODULE: {module_name}
TEST FILE TO WRITE: {test_path}
TOP-LEVEL FUNCTIONS: {function_names}

SOURCE CODE:
{code}

Rules:
- Return ONLY the full Python test file
- Use the standard library only
- Use unittest, not pytest
- The tests must validate real behavior of the target file
- Prefer robust tests that can run in CI
- Import the real target module name: {module_name}
- Never use placeholder imports like your_app
- If direct imports are awkward, use importlib.util to load the file by path
- If the file is a script, it is acceptable to test it via subprocess
- Do NOT include markdown fences or explanations
"""
        test_code = clean_text(router.generate(prompt, task_type="agent"))

        if self._is_placeholder(test_code) or not test_code.strip():
            return ""

        return test_code

    def _build_fallback_test(self, file_path: str, code: str) -> str:
        normalized_path = file_path.replace("\\", "/")
        file_name = os.path.basename(file_path)
        module_name = os.path.splitext(file_name)[0]
        function_names = extract_python_functions(code)
        function_assertions = "\n".join(
            f'        self.assertTrue(hasattr(module, "{name}"), "Expected function {name} to exist")'
            for name in function_names
        )
        if not function_assertions:
            function_assertions = "        self.assertTrue(hasattr(module, '__name__'))"
        return f"""import pathlib
import importlib.util
import subprocess
import sys
import unittest


WORKSPACE_ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGET_FILE = WORKSPACE_ROOT / "{normalized_path}"
MODULE_NAME = "{module_name}"


def load_target_module():
    spec = importlib.util.spec_from_file_location(MODULE_NAME, TARGET_FILE)
    module = importlib.util.module_from_spec(spec)
    assert spec is not None and spec.loader is not None
    spec.loader.exec_module(module)
    return module


class GeneratedSmokeTest(unittest.TestCase):
    def test_target_file_exists(self):
        self.assertTrue(TARGET_FILE.exists(), f"Missing target file: {{TARGET_FILE}}")

    def test_python_compiles(self):
        source = TARGET_FILE.read_text(encoding="utf-8")
        compile(source, "{file_name}", "exec")

    def test_module_imports(self):
        module = load_target_module()
{function_assertions}

    def test_cli_invocation_finishes(self):
        result = subprocess.run(
            [sys.executable, str(TARGET_FILE)],
            cwd=WORKSPACE_ROOT,
            capture_output=True,
            text=True,
            timeout=5,
        )
        self.assertEqual(result.returncode, 0, msg=result.stderr or result.stdout)

if __name__ == "__main__":
    unittest.main()
"""

    def _test_code_is_usable(self, test_code: str, file_path: str) -> bool:
        lowered = (test_code or "").lower()
        module_name = os.path.splitext(os.path.basename(file_path))[0].lower()
        bad_markers = [
            "your_app",
            "import pytest",
            "from pytest",
        ]
        if any(marker in lowered for marker in bad_markers):
            return False
        return module_name in lowered or "importlib.util" in lowered

    def _write_generated_tests(self, file_path: str) -> tuple[str, str]:
        source_code = self.tools.execute("read_file", {"path": file_path})
        if not source_code or is_tool_error_result(source_code):
            return "", source_code or "Error: Could not read source file for test generation."

        test_path = derive_test_path(file_path)
        test_code = self._generate_tests_with_model(file_path, source_code)
        if not test_code or not self._test_code_is_usable(test_code, file_path):
            test_code = self._build_fallback_test(file_path, source_code)

        write_result = self.tools.execute("write_file", {"path": test_path, "content": test_code})
        return test_path, write_result

    def _validation_points_to_bad_tests(self, validation_result: str) -> bool:
        lowered = (validation_result or "").lower()
        markers = [
            "_failedtest",
            "failedtest",
            "no module named 'your_app'",
            "from your_app import",
            "syntaxerror",
            "importerror",
            "modulenotfounderror",
            "nameerror: name 'your_app'",
        ]
        return any(marker in lowered for marker in markers)

    def _validate_python_file(self, file_path: str, history: list, max_attempts: int = 1) -> str:
        if not looks_like_python(file_path):
            return ""

        validation_command = build_test_command(file_path)
        last_result = ""

        for attempt in range(max_attempts):
            test_path, test_write_result = self._write_generated_tests(file_path)
            print("Generated tests:", test_path, test_write_result)

            if test_write_result and is_tool_error_result(test_write_result):
                return test_write_result

            validation_result = self.tools.execute("run_command", {"command": validation_command})
            print("Validation result:", validation_result)
            last_result = validation_result

            memory.add(
                doc_id=f"validation_{len(history)}_{attempt}",
                content=f"Validated {file_path} with {test_path}: {validation_result[:120]}",
            )

            if validation_result and not is_tool_error_result(validation_result):
                return f"Validation passed for {file_path}\n{validation_result}".strip()

            if self._validation_points_to_bad_tests(validation_result):
                source_code = self.tools.execute("read_file", {"path": file_path})
                fallback_test = self._build_fallback_test(file_path, source_code)
                test_path = derive_test_path(file_path)
                fallback_write = self.tools.execute("write_file", {"path": test_path, "content": fallback_test})
                print("Fallback test write:", fallback_write)
                validation_result = self.tools.execute("run_command", {"command": validation_command})
                print("Fallback validation result:", validation_result)
                last_result = validation_result
                if validation_result and not is_tool_error_result(validation_result):
                    return f"Validation passed for {file_path}\n{validation_result}".strip()

            source_code = self.tools.execute("read_file", {"path": file_path})
            test_code = self.tools.execute("read_file", {"path": test_path}) if test_path else ""
            repair_prompt = f"""
You are fixing a Python source file after automated validation failed.

TARGET FILE: {file_path}
TEST FILE: {test_path}

VALIDATION FAILURE:
{validation_result}

SOURCE CODE:
{source_code}

GENERATED TESTS:
{test_code}

Rules:
- Return ONLY the full corrected source code for {file_path}
- Do NOT modify the tests in your response
- Do NOT include markdown fences or explanations
- Keep the intended behavior, but make the code pass the validation
"""
            fixed_code = clean_text(router.generate(repair_prompt, task_type="agent"))

            if not fixed_code or self._is_placeholder(fixed_code) or fixed_code.strip() == source_code.strip():
                break

            write_result = self.tools.execute("write_file", {"path": file_path, "content": fixed_code})
            print("Validation repair write:", write_result)

        return last_result

    def _run_and_capture(self, file_path: str) -> str:
        command = build_run_command(file_path)
        if not command:
            return ""
        return self.tools.execute("run_command", {"command": command})

    def _repair_target_file(self, file_path: str, history: list) -> str:
        file_path = normalize_path(file_path)
        code = self.tools.execute("read_file", {"path": file_path})
        print("CODE:", code)

        if not code or is_tool_error_result(code):
            return code or "Error: Could not read file."

        execution_result = self._run_and_capture(file_path) if looks_like_python(file_path) else ""
        if execution_result and not is_tool_error_result(execution_result):
            validation_result = self._validate_python_file(file_path, history)
            if validation_result and is_tool_error_result(validation_result):
                return validation_result
            if validation_result:
                return f"Code already works: {file_path}\n{execution_result}\n\n{validation_result}".strip()
            return f"Code already works: {file_path}\n{execution_result}".strip()

        error_context = execution_result if execution_result else "The file content appears incorrect and should be fixed."
        fixed_code = self._fix_file_with_model(file_path, code, error_context)

        if not fixed_code or fixed_code.strip() == code.strip():
            return execution_result or f"Error: Could not produce a valid fix for {file_path}"

        write_result = self.tools.execute("write_file", {"path": file_path, "content": fixed_code})
        print("Fixed code written:", write_result)

        rerun_result = self._run_and_capture(file_path) if looks_like_python(file_path) else write_result

        memory.add(
            doc_id=f"fix_{len(history)}",
            content=f"Fixed {file_path}: {rerun_result[:120]}",
        )

        if rerun_result and not is_tool_error_result(rerun_result):
            validation_result = self._validate_python_file(file_path, history)
            if validation_result and is_tool_error_result(validation_result):
                return validation_result
            if validation_result:
                return f"Fixed {file_path}\n{rerun_result}\n\n{validation_result}".strip()
            return f"Fixed {file_path}\n{rerun_result}".strip()

        return rerun_result or write_result

    def _debug_and_fix(self, error: str, file_path: str, history: list) -> str:
        print("DEBUG MODE ACTIVATED")
        return self._repair_target_file(file_path, history)

    def process(self, user_input: str, autonomous_mode: bool = True, intelligence_level: str = "high") -> str:
        user_request = extract_user_request(user_input)
        task_name = extract_task_name(user_input)
        should_use_memory = task_name in {"chat", ""} and is_question(user_input)
        context = memory.search(user_input) if should_use_memory else []
        print("MEMORY:", context)

        if is_question(user_input):
            return safe_encode(self.answer(user_input, context))

        if task_name == "fix_file":
            target = self._extract_primary_target(user_input)
            return safe_encode(self._repair_target_file(target, []))

        if looks_like_website_request(user_request) and looks_like_generation_request(user_request):
            return safe_encode(self._generate_website(user_request))

        if task_name == "chat" and looks_like_generation_request(user_request) and extract_file_paths(user_request):
            target = self._extract_primary_target(user_request)
            return safe_encode(self._generate_code_for_file(target, user_request))

        if task_name == "generate_tests":
            target = self._extract_primary_target(user_input)
            test_path, write_result = self._write_generated_tests(target)
            if write_result and is_tool_error_result(write_result):
                return safe_encode(write_result)
            validation_result = self._validate_python_file(target, [])
            return safe_encode(f"Generated tests for {target} at {test_path}\n{validation_result}".strip())

        if task_name == "validate_workspace":
            target = self._extract_primary_target(user_input)
            validation_result = self._validate_python_file(target, [])
            return safe_encode(validation_result or f"No validation was run for {target}")

        if self._needs_fixing(user_input):
            target = extract_file_paths(user_input)[0]
            return safe_encode(self._repair_target_file(target, []))

        if autonomous_mode:
            return safe_encode(self._run_autonomous_loop(user_input, intelligence_level=intelligence_level))

        return safe_encode(self._run_autonomous_loop(user_input, intelligence_level="medium"))

    def get_changed_files(self) -> list[str]:
        return sorted(self.tools.changed_files)

    def read_changed_file(self, relative_path: str) -> str | None:
        try:
            full_path = resolve_workspace_path(relative_path, self.workspace_root)
        except Exception:
            return None

        if not os.path.exists(full_path):
            return None

        with open(full_path, "r", encoding="utf-8") as file_handle:
            return file_handle.read()
