from groq import Groq
from app.core.config import GROQ_API_KEY

client = Groq(api_key=GROQ_API_KEY)

class GroqModel:
    def __init__(self, model_name="llama-3.3-70b-versatile"):
        self.model_name = model_name

    def generate(self, prompt: str) -> str:
        try:
            response = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model_name,
            )
            return response.choices[0].message.content

        except Exception as e:
            raise Exception(f"Groq Error ({self.model_name}): {e}")