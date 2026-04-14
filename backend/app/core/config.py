from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
HF_API_KEY = os.getenv("HF_API_KEY")
HF_TEXT_MODEL = os.getenv("HF_TEXT_MODEL", "deepseek-ai/deepseek-coder-6.7b")
HF_IMAGE_MODEL = os.getenv("HF_IMAGE_MODEL", "stabilityai/stable-diffusion-xl-base-1.0")
HF_API_BASE = os.getenv("HF_API_BASE", "https://api-inference.huggingface.co/models")
HF_IMAGE_API_URL = os.getenv("HF_IMAGE_API_URL")

if not GEMINI_API_KEY:
    print("GEMINI_API_KEY missing")

if not GROQ_API_KEY:
    print("GROQ_API_KEY missing")

if not HF_API_KEY:
    print("HF_API_KEY missing (optional)")

if HF_IMAGE_API_URL:
    print("HF image endpoint configured")
