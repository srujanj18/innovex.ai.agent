import re
import traceback

from app.models.gemini import GeminiModel
from app.models.groq import GroqModel
from app.models.huggingface import HFModel


class ModelRouter:
    def __init__(self):
        self.models = {
            "gemini_2.5_pro": GeminiModel("gemini-2.5-pro"),
            "gemini_2.5_flash": GeminiModel("gemini-2.5-flash"),
            "gemini_2.5_flash_lite": GeminiModel("gemini-2.5-flash-lite"),
            "gemini_2.5_flash_live": GeminiModel("gemini-2.5-flash-live"),
            "gemini_2.5_flash_tts": GeminiModel("gemini-2.5-flash-tts"),
            "gemini_2.5_pro_tts": GeminiModel("gemini-2.5-pro-tts"),
            "gemini_embedding_2": GeminiModel("gemini-embedding-2"),
            "gemini_embedding": GeminiModel("gemini-embedding"),
            "nano_banana_pro": GeminiModel("nano-banana-pro"),
            "nano_banana_2": GeminiModel("nano-banana-2"),
            "nano_banana": GeminiModel("nano-banana"),
            "imagen_4": GeminiModel("imagen-4"),
            "veo_31": GeminiModel("veo-3.1"),
            "veo_31_lite": GeminiModel("veo-3.1-lite"),
            "lyria_3_pro": GeminiModel("lyria-3-pro"),
            "lyria_3_clip": GeminiModel("lyria-3-clip"),
            "lyria_realtime": GeminiModel("lyria-realtime"),
            "computer_use": GeminiModel("computer-use"),
            "gemini_deep_research": GeminiModel("gemini-deep-research"),
            "groq_main": GroqModel("llama-3.3-70b-versatile"),
            "groq_fast": GroqModel("llama-3.1-8b-instant"),
            "hf_deepseek": HFModel(),
        }

        self.task_routes = {
            "advanced_reasoning": ["groq_main", "gemini_2.5_flash", "gemini_2.5_pro", "hf_deepseek"],
            "agentic_coding": ["groq_fast", "groq_main", "gemini_2.5_flash", "gemini_2.5_pro"],
            "structured_backend": ["groq_fast", "groq_main", "gemini_2.5_flash", "gemini_2.5_pro"],
            "fast_text": ["groq_fast", "gemini_2.5_flash", "groq_main", "gemini_2.5_flash_lite"],
            "budget_text": ["groq_fast", "gemini_2.5_flash_lite", "gemini_2.5_flash", "groq_main"],
            "realtime_audio": ["gemini_2.5_flash_live", "gemini_2.5_flash", "groq_fast"],
            "text_to_speech": ["gemini_2.5_flash_tts", "gemini_2.5_pro_tts", "gemini_2.5_flash"],
            "image_generation": ["nano_banana_pro", "nano_banana_2", "nano_banana", "imagen_4"],
            "video_generation": ["veo_31", "veo_31_lite"],
            "music_generation": ["lyria_3_pro", "lyria_3_clip", "lyria_realtime"],
            "computer_use": ["computer_use", "groq_main", "gemini_2.5_flash"],
            "deep_research": ["gemini_deep_research", "groq_main", "gemini_2.5_flash", "gemini_2.5_pro"],
            "embeddings_rag": ["gemini_embedding_2", "gemini_embedding"],
            "general": ["groq_fast", "groq_main", "gemini_2.5_flash", "gemini_2.5_pro"],
        }

    def infer_task_profile(self, prompt: str, task_type="general") -> str:
        lowered = (prompt or "").lower()

        if task_type in {"agent", "complex", "fast"}:
            forced_map = {
                "agent": "agentic_coding",
                "complex": "advanced_reasoning",
                "fast": "fast_text",
            }
            return forced_map[task_type]

        if re.search(r"\b(embed|embedding|rag|vector|semantic search|retrieval)\b", lowered):
            return "embeddings_rag"
        if re.search(r"\b(research|investigate|analyze deeply|deep research)\b", lowered):
            return "deep_research"
        if re.search(r"\b(click|browse|open website|computer use|ui automation)\b", lowered):
            return "computer_use"
        if re.search(r"\b(song|music|melody|background music|composition)\b", lowered):
            return "music_generation"
        if re.search(r"\b(video|reel|cinematic|animation|ad video)\b", lowered):
            return "video_generation"
        if re.search(r"\b(image|logo|poster|banner|illustration|design asset|ui asset)\b", lowered):
            return "image_generation"
        if re.search(r"\b(tts|text to speech|narration|podcast|audiobook)\b", lowered):
            return "text_to_speech"
        if re.search(r"\b(live|realtime|voice assistant|audio streaming|streaming audio)\b", lowered):
            return "realtime_audio"
        if re.search(r"\b(high volume|cheap|low cost|budget|simple automation|bulk)\b", lowered):
            return "budget_text"
        if re.search(r"\b(api|chatbot|real-time app|realtime app|scalable|latency)\b", lowered):
            return "fast_text"
        if re.search(r"\b(backend|workflow|structured|service layer|heavy logic)\b", lowered):
            return "structured_backend"
        if re.search(r"\b(code|python|debug|fix|test|refactor|agent|tool|function|file)\b", lowered):
            return "agentic_coding"
        if re.search(r"\b(reason|analyze|complex|plan|architecture|deep analysis)\b", lowered):
            return "advanced_reasoning"

        return "general"

    def route(self, task_type="general", prompt=""):
        profile = self.infer_task_profile(prompt, task_type)
        return self.task_routes.get(profile, self.task_routes["general"])

    def generate(self, prompt, task_type="general"):
        model_priority = self.route(task_type=task_type, prompt=prompt)

        for model_name in model_priority:
            try:
                print(f"\nTrying model: {model_name}")

                model = self.models.get(model_name)
                if not model:
                    print(f"Model not found: {model_name}")
                    continue

                result = model.generate(prompt)

                if result and str(result).strip():
                    print(f"Success: {model_name}")
                    return result

                print(f"Empty response from: {model_name}")

            except Exception:
                print(f"\n{model_name} failed:")
                traceback.print_exc()

        return "Error: All models failed."

    def generate_parallel(self, prompt, task_type="general"):
        import threading

        results = {}
        model_priority = self.route(task_type=task_type, prompt=prompt)[:2]

        def call_model(name):
            try:
                res = self.models[name].generate(prompt)
                if res:
                    results[name] = res
            except Exception:
                pass

        threads = [threading.Thread(target=call_model, args=(name,)) for name in model_priority]

        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        if results:
            best_model = list(results.keys())[0]
            print(f"Parallel winner: {best_model}")
            return results[best_model]

        return "Error: All models failed (parallel)."
