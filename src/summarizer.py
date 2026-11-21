"""Map-reduce summarization with 3 detail levels and on-disk caching."""
import hashlib
import json
import time
from pathlib import Path
import re

from src.llm import generate
from src.prompts import MAP_SYSTEM, REDUCE_SYSTEM, LEVELS, LANG_NAMES
from src.vectorstore import get_doc_chunks

CACHE_DIR = Path("cache")
BATCH_CHARS = 6000       # text sent per map call
REDUCE_LIMIT = 12000     # max chars of notes sent to one reduce call


def _llm(prompt: str, system: str) -> str:
    """generate() with retries for rate limits (429) and empty replies."""
    for attempt in range(4):
        try:
            out = generate(prompt, system=system, temperature=0.2).strip()
            if out:
                return out
        except Exception as e:
            if "429" in str(e) and attempt < 3:
                time.sleep(20 * (attempt + 1))
                continue
            raise
    raise RuntimeError("The LLM returned an empty answer 4 times in a row.")


def _batches(chunks: list[dict]) -> list[str]:
    batches, current, size = [], [], 0
    for c in chunks:
        if current and size + len(c["text"]) > BATCH_CHARS:
            batches.append("\n\n".join(current))
            current, size = [], 0
        current.append(c["text"])
        size += len(c["text"])
    if current:
        batches.append("\n\n".join(current))
    return batches


def _cache_path(doc: str, kind: str) -> Path:
    CACHE_DIR.mkdir(exist_ok=True)
    return CACHE_DIR / f"{hashlib.md5(doc.encode('utf-8')).hexdigest()}_{kind}.json"


def _cached(path: Path, compute):
    if path.exists():
        value = json.loads(path.read_text(encoding="utf-8"))
        if value:                      # ignore empty cached values
            return value
    value = compute()
    if value:                          # never cache empty results
        path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")
    return value

def _truncate_words(text: str, limit: int) -> str:
    """Last resort: keep whole sentences until the word limit is reached."""
    out, count = [], 0
    for sentence in re.split(r"(?<=[.!?])\s+", text):
        n = len(sentence.split())
        if out and count + n > limit:
            break
        out.append(sentence)
        count += n
    return " ".join(out)

def _map_notes(doc: str, language: str) -> list[str]:
    chunks = get_doc_chunks(doc)
    if not chunks:
        raise ValueError(f"Document '{doc}' is not indexed.")
    system = MAP_SYSTEM.format(language=language)
    return [_llm(f"Section text:\n\n{b}", system) for b in _batches(chunks)]


def _collapse(notes: list[str], language: str) -> list[str]:
    """If the notes are too long for one call, merge them hierarchically."""
    system = MAP_SYSTEM.format(language=language)
    while sum(len(n) for n in notes) > REDUCE_LIMIT and len(notes) > 1:
        merged, group, size = [], [], 0
        for n in notes:
            if group and size + len(n) > REDUCE_LIMIT // 2:
                merged.append(_llm("Section text:\n\n" + "\n\n".join(group), system))
                group, size = [], 0
            group.append(n)
            size += len(n)
        if group:
            merged.append(_llm("Section text:\n\n" + "\n\n".join(group), system))
        if len(merged) >= len(notes):
            break
        notes = merged
    return notes

WORD_LIMITS = {"short": 120, "medium": 360}   # detailed has no upper limit

def _enforce_length(text: str, level: str, language: str) -> str:
    limit = WORD_LIMITS.get(level)
    if not limit:
        return text
    for _ in range(2):                 # ask the model to shorten, up to twice
        if len(text.split()) <= limit:
            return text
        text = _llm(
            f"Shorten this summary to at most {limit - 20} words. Keep the most important "
            f"points and the structure. Add nothing new.\n\n{text}",
            REDUCE_SYSTEM.format(language=language),
        )
    return text if len(text.split()) <= limit else _truncate_words(text, limit)

def summarize(doc: str, level: str = "medium", lang: str | None = None) -> str:
    """level: short | medium | detailed.  lang: en | fr | ar (default: document language)."""
    if level not in LEVELS:
        raise ValueError(f"level must be one of {list(LEVELS)}")
    chunks = get_doc_chunks(doc)
    lang = lang or (chunks[0]["meta"]["lang"] if chunks else "en")
    language = LANG_NAMES.get(lang, "English")

    def compute_summary():
        notes = _cached(_cache_path(doc, f"notes_{lang}"), lambda: _map_notes(doc, language))
        notes = _collapse(notes, language)
        body = "\n\n".join(f"Notes {i}:\n{n}" for i, n in enumerate(notes, 1))
        text = _llm(f"{LEVELS[level]}\n\n{body}", REDUCE_SYSTEM.format(language=language))
        return _enforce_length(text, level, language)
    
    return _cached(_cache_path(doc, f"summary_{level}_{lang}"), compute_summary)