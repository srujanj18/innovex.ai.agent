from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import GEMINI_API_KEY, GROQ_API_KEY
from app.routes.chat import router as chat_router

print("GEMINI:", "Loaded" if GEMINI_API_KEY else "Missing")
print("GROQ:", "Loaded" if GROQ_API_KEY else "Missing")

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(chat_router)


@app.get("/")
def home():
    return {"message": "AI Agent Backend Running"}
