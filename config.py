"""Central configuration. Everything tunable lives here."""
import os
from dotenv import load_dotenv

load_dotenv()

# --- LLM backends (all OpenAI-compatible) ---
BACKENDS = {
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "api_key": os.getenv("GROQ_API_KEY", ""),
        "model": os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile"),
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "api_key": os.getenv("GEMINI_API_KEY", ""),
        "model": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    },
    "ollama": {
        "base_url": "http://localhost:11434/v1",
        "api_key": "ollama",  # ignored by Ollama but required by the client
        "model": os.getenv("OLLAMA_MODEL", "qwen2.5:3b"),
    },
}
LLM_BACKEND = os.getenv("LLM_BACKEND", "groq")

# --- Embeddings ---
EMBEDDING_MODEL = "intfloat/multilingual-e5-base"

# --- Chunking ---
CHUNK_SIZE = 1000
CHUNK_OVERLAP = 150

# --- Retrieval ---
TOP_K = 5
SIMILARITY_THRESHOLD = 0.35   # tune later with the test set

# --- Paths ---
CHROMA_DIR = "chroma_db"