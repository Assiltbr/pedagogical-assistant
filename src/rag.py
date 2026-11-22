"""RAG: retrieve passages, build a cited prompt, generate, handle 'not found'."""
import re
import config
from src.llm import generate
from src.prompts import RAG_SYSTEM, NOT_FOUND_MESSAGES
from src.vectorstore import search


def _pages(meta: dict) -> str:
    a, b = meta["page_start"], meta["page_end"]
    return f"p.{a}" if a == b else f"p.{a}-{b}"


def _question_lang(q: str) -> str:
    letters = [c for c in q if c.isalpha()]
    if letters and sum("\u0600" <= c <= "\u06FF" for c in letters) / len(letters) > 0.3:
        return "ar"
    fr_words = {"le", "la", "les", "des", "est", "une", "quel", "quelle", "que",
                "qu", "comment", "pourquoi", "dans", "pour", "est-ce"}
    return "fr" if set(re.findall(r"[a-zà-ÿ'-]+", q.lower())) & fr_words else "en"


def answer(question: str, k: int = config.TOP_K, doc: str | None = None,
           backend: str | None = None) -> dict:
    hits = search(question, k=k, doc=doc)
    passages = "\n\n".join(
        f"[{i}] ({h['meta']['doc']}, {_pages(h['meta'])})\n{h['text']}"
        for i, h in enumerate(hits, 1)
    )
    prompt = f"Passages:\n{passages}\n\nQuestion: {question}"
    text = generate(prompt, system=RAG_SYSTEM, temperature=0.1, backend=backend).strip()

    if "NOT_FOUND" in text:
        return {"answer": NOT_FOUND_MESSAGES[_question_lang(question)],
                "sources": [], "found": False}

    cited = {int(n) for n in re.findall(r"\[(\d+)\]", text)}
    sources = [{"n": i, "doc": h["meta"]["doc"], "pages": _pages(h["meta"]),
                "score": round(h["score"], 3), "text": h["text"]}
               for i, h in enumerate(hits, 1) if i in cited]
    return {"answer": text, "sources": sources, "found": True}