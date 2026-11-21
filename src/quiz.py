"""Quiz generation: grounded MCQs as validated JSON, with retries and shuffling."""
import json
import random
import re

from pydantic import BaseModel, field_validator

from src.llm import generate
from src.prompts import QUIZ_SYSTEM, DIFFICULTY, LANG_NAMES, VERIFY_SYSTEM
from src.vectorstore import get_doc_chunks, search

SKIP_WORDS = ("références", "references", "bibliograph", "merci de votre attention")


class MCQ(BaseModel):
    question: str
    options: list[str]
    answer_index: int
    explanation: str
    source_pages: str | None = None
    difficulty: str = "medium"

    @field_validator("options")
    @classmethod
    def four_distinct_options(cls, v):
        v = [o.strip() for o in v]
        if len(v) != 4 or len(set(o.lower() for o in v)) != 4 or any(not o for o in v):
            raise ValueError("need exactly 4 distinct, non-empty options")
        return v

    @field_validator("answer_index")
    @classmethod
    def valid_index(cls, v):
        if not 0 <= v <= 3:
            raise ValueError("answer_index must be 0-3")
        return v

    @field_validator("question", "explanation")
    @classmethod
    def not_empty(cls, v):
        if not v.strip():
            raise ValueError("empty text")
        return v.strip()


def _pick_chunks(doc: str, n: int, topic: str | None) -> list[dict]:
    if topic:
        return [{"text": h["text"], "meta": h["meta"]} for h in search(topic, k=max(n, 3), doc=doc)]
    chunks = [c for c in get_doc_chunks(doc)
              if len(c["text"]) > 300 and not any(w in c["text"].lower() for w in SKIP_WORDS)]
    if len(chunks) <= n:
        return chunks
    step = len(chunks) / n
    return [chunks[int(i * step)] for i in range(n)]


def _parse_json(text: str) -> list:
    text = re.sub(r"^```(?:json)?|```$", "", text.strip(), flags=re.M).strip()
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array found")
    return json.loads(text[start:end + 1])


def _shuffle(q: MCQ) -> MCQ:
    correct = q.options[q.answer_index]
    options = q.options[:]
    random.shuffle(options)
    q.options, q.answer_index = options, options.index(correct)
    return q

def _verify(q: MCQ, passage: str) -> bool:
    """Second LLM call: answer the question from the passage; must match the key."""
    options = "\n".join(f"{l}) {o}" for l, o in zip("ABCD", q.options))
    try:
        out = generate(f"Passage:\n{passage}\n\nQuestion: {q.question}\n{options}",
                       system=VERIFY_SYSTEM, temperature=0).strip().upper()
    except Exception:
        return False
    m = re.search(r"\b(NONE|[ABCD])\b", out)
    return bool(m) and m.group(1) == "ABCD"[q.answer_index]

def generate_quiz(doc: str, n: int = 5, difficulty: str = "medium",
                  lang: str | None = None, topic: str | None = None,
                  max_attempts: int = 3) -> list[MCQ]:
    if difficulty not in DIFFICULTY:
        raise ValueError(f"difficulty must be one of {list(DIFFICULTY)}")
    chunks = _pick_chunks(doc, n, topic)
    if not chunks:
        raise ValueError(f"No usable text found for '{doc}'. Is it indexed?")
    lang = lang or chunks[0]["meta"]["lang"]
    system = QUIZ_SYSTEM.format(language=LANG_NAMES.get(lang, "English"))
    passages = "\n\n".join(f"[{i}]\n{c['text']}" for i, c in enumerate(chunks, 1))

    quiz: list[MCQ] = []
    for _ in range(max_attempts):
        missing = n - len(quiz)
        if missing <= 0:
            break
        prompt = (f"{DIFFICULTY[difficulty]}\n\nWrite {missing} questions.\n\n"
                  f"Passages:\n{passages}")
        try:
            items = _parse_json(generate(prompt, system=system, temperature=0.4))
        except Exception:
            continue                                   # invalid JSON: retry

        for item in items:
            try:
                idx = int(item.get("passage", 0))
                if not 1 <= idx <= len(chunks):
                    continue                           # no grounding: drop
                meta = chunks[idx - 1]["meta"]
                pages = (f"p.{meta['page_start']}" if meta["page_start"] == meta["page_end"]
                         else f"p.{meta['page_start']}-{meta['page_end']}")
                q = _shuffle(MCQ(question=item["question"], options=item["options"],
                                 answer_index=item["answer_index"],
                                 explanation=item["explanation"],
                                 source_pages=pages, difficulty=difficulty))
            except Exception:
                continue                               # invalid question: drop it

            if any(q.question.lower() == e.question.lower() for e in quiz):
                continue                               # duplicate: drop
            if _verify(q, chunks[idx - 1]["text"]):    # keep only verified questions
                quiz.append(q)
    return quiz[:n]
    return quiz[:n]