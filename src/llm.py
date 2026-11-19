"""Unified LLM interface: the rest of the app only calls generate()."""
from openai import OpenAI
import config


def get_client(backend: str | None = None):
    name = backend or config.LLM_BACKEND
    cfg = config.BACKENDS[name]
    if name != "ollama" and not cfg["api_key"]:
        raise ValueError(f"Missing API key for backend '{name}' in .env")
    return OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"]), cfg["model"]


def generate(prompt: str, system: str | None = None,
             temperature: float = 0.2, backend: str | None = None) -> str:
    client, model = get_client(backend)
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature
    )
    return response.choices[0].message.content