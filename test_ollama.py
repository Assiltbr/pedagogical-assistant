import time
from src.llm import generate

prompts = {
    "fr": "Explique en trois phrases ce qu'est le RAG.",
    "ar": "اشرح في ثلاث جمل ما هو RAG.",
}
with open("ollama_test.txt", "w", encoding="utf-8") as f:
    for lang, p in prompts.items():
        start = time.time()
        out = generate(p, backend="ollama")
        line = f"[{lang}] {time.time() - start:.1f}s, {len(out.split())} words\n{out}\n"
        print(line)
        f.write(line + "\n")