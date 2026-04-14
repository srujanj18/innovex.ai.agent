from google import genai

from app.core.config import GEMINI_API_KEY

client = genai.Client(api_key=GEMINI_API_KEY)


class GeminiModel:
    def __init__(self, model_name="gemini-2.5-pro"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
            )

            if hasattr(response, "text") and response.text:
                return response.text

            candidates = getattr(response, "candidates", None) or []
            for candidate in candidates:
                content = getattr(candidate, "content", None)
                if not content:
                    continue

                parts = getattr(content, "parts", None) or []
                texts = [getattr(part, "text", "") for part in parts if getattr(part, "text", "")]
                if texts:
                    return "\n".join(texts).strip()

            return ""

        except Exception as e:
            raise Exception(f"Gemini Error ({self.model_name}): {e}")

    def generate_with_tools(self, prompt, tools):
        try:
            response = client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                tools=tools,
            )

            if hasattr(response, "text") and response.text:
                return response.text

            return str(response)

        except Exception as e:
            raise Exception(f"Gemini Tool Error ({self.model_name}): {e}")
