import requests

from app.core.config import HF_API_BASE, HF_API_KEY, HF_IMAGE_API_URL, HF_IMAGE_MODEL, HF_TEXT_MODEL

headers = {
    "Authorization": f"Bearer {HF_API_KEY}"
} if HF_API_KEY else {}


class HFModel:
    def __init__(self, model_name: str = HF_TEXT_MODEL):
        self.model_name = model_name

    @property
    def endpoint(self) -> str:
        return f"{HF_API_BASE}/{self.model_name}"

    def generate(self, prompt: str) -> str:
        try:
            response = requests.post(
                self.endpoint,
                headers=headers,
                json={"inputs": prompt},
                timeout=60,
            )
            response.raise_for_status()

            data = response.json()

            if isinstance(data, list):
                return data[0].get("generated_text", "")

            raise Exception(data)
        except Exception as error:
            raise Exception(f"HuggingFace Error: {error}")

    def generate_image(self, prompt: str) -> bytes:
        try:
            image_endpoint = HF_IMAGE_API_URL or f"{HF_API_BASE}/{HF_IMAGE_MODEL}"
            response = requests.post(
                image_endpoint,
                headers=headers,
                json={"inputs": prompt},
                timeout=120,
            )
            response.raise_for_status()

            content_type = response.headers.get("content-type", "")
            if "image" not in content_type.lower():
                raise Exception(response.text[:500])

            return response.content
        except Exception as error:
            raise Exception(f"HuggingFace Image Error: {error}")
