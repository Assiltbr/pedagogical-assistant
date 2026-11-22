"""Unified LLM interface: the rest of the app only calls generate()."""
import re

import httpx
from openai import OpenAI

import config

OLLAMA_NUM_CTX = 8192


def get_client(backend: str | None = None):
    name = backend or config.LLM_BACKEND
    cfg = config.BACKENDS[name]
    if name != "ollama" and not cfg["api_key"]:
        raise ValueError(f"Missing API key for backend '{name}' in .env")
    return OpenAI(base_url=cfg["base_url"], api_key=cfg["api_key"]), cfg["model"]


def _generate_ollama(messages: list[dict], temperature: float) -> str:
    """Ollama native API: lets us disable 'thinking' and set the context size."""
    cfg = config.BACKENDS["ollama"]
    host = cfg["base_url"].removesuffix("/v1")
    try:
        r = httpx.post(f"{host}/api/chat", timeout=1200, json={
            "model": cfg["model"],
            "messages": messages,
            "stream": False,
            "think": False,
            "options": {"temperature": temperature, "num_ctx": OLLAMA_NUM_CTX},
        })
        r.raise_for_status()
    except httpx.ConnectError as e:
        raise RuntimeError("Ollama is not running. Start it, then try again.") from e
    data = r.json()
    with open("ollama_timings.log", "a", encoding="utf-8") as log:
        log.write(
            f"prompt_tokens={data.get('prompt_eval_count')} "
            f"prompt_s={data.get('prompt_eval_duration', 0) / 1e9:.1f} "
            f"gen_tokens={data.get('eval_count')} "
            f"gen_s={data.get('eval_duration', 0) / 1e9:.1f} "
            f"load_s={data.get('load_duration', 0) / 1e9:.1f} "
            f"total_s={data.get('total_duration', 0) / 1e9:.1f}\n")
    text = data["message"]["content"]
    return re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()

>>>>>>> feature/ui
def generate(prompt: str, system: str | None = None,
             temperature: float = 0.2, backend: str | None = None) -> str:
    name = backend or config.LLM_BACKEND
    messages = []
    if system:
        messages.append({"role": "system", "content": system})
    messages.append({"role": "user", "content": prompt})

    if name == "ollama":
        return _generate_ollama(messages, temperature)

    client, model = get_client(name)
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature
    )
    return response.choices[0].message.content