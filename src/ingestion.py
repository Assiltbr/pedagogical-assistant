"""Ingestion: PDF/TXT -> pages -> cleaned text -> chunks with metadata."""
import re
import unicodedata
from collections import Counter
from pathlib import Path

import pymupdf
from langchain_text_splitters import RecursiveCharacterTextSplitter

import config

# Separators include Arabic punctuation (، ؛ ؟) so Arabic text splits cleanly.
SEPARATORS = ["\n\n", "\n", ". ", "؟ ", "? ", "! ", "؛ ", "; ", "، ", ", ", " ", ""]


# ---------- 1. Extraction ----------
def extract_pages(path: str) -> list[dict]:
    """Return [{'page': int, 'text': str}, ...]. Supports .pdf and .txt/.md."""
    p = Path(path)
    if p.suffix.lower() == ".pdf":
        with fitz.open(p) as doc:
            return [{"page": i + 1, "text": page.get_text()}
                    for i, page in enumerate(doc)]
    text = p.read_text(encoding="utf-8")
    return [{"page": 1, "text": text}]


def is_scanned(pages: list[dict], min_chars: int = 50) -> bool:
    """A PDF with almost no extractable text is probably scanned images (needs OCR)."""
    if not pages:
        return True
    empty = sum(1 for p in pages if len(p["text"].strip()) < min_chars)
    return empty / len(pages) > 0.8


# ---------- 2. Cleaning ----------
def _find_repeated_lines(pages: list[dict], ratio: float = 0.5) -> set[str]:
    """Short lines appearing on many pages are headers/footers."""
    if len(pages) < 4:
        return set()
    counts = Counter()
    for p in pages:
        lines = {l.strip() for l in p["text"].splitlines() if l.strip()}
        counts.update(l for l in lines if len(l) < 80)
    return {l for l, c in counts.items() if c / len(pages) >= ratio}

# LaTeX/Beamer PDFs store accents as separate spacing characters before the letter
_ACCENT_MAP = {"´": "\u0301", "ˆ": "\u0302", "¨": "\u0308", "¸": "\u0327", "˜": "\u0303"}
_ACCENT_RE = re.compile(r"([´ˆ¨¸˜])([A-Za-z])")
_GRAVE_RE = re.compile(r"`([aeuAEU])")


def fix_latex_accents(text: str) -> str:
    """'Num´erique' -> 'Numérique', 'mˆeme' -> 'même', '¸ca' -> 'ça'."""
    text = _ACCENT_RE.sub(
        lambda m: unicodedata.normalize("NFC", m.group(2) + _ACCENT_MAP[m.group(1)]), text)
    return _GRAVE_RE.sub(
        lambda m: unicodedata.normalize("NFC", m.group(1) + "\u0300"), text)

def clean_text(text: str, repeated: set[str]) -> str:
    text = fix_latex_accents(text)  
    # NFKC fixes Arabic presentation forms and ligatures (e.g. "ﻻ", "ﬁ")
    text = unicodedata.normalize("NFKC", text)
    # Remove repeated headers/footers and bare page numbers
    lines = []
    for line in text.splitlines():
        s = line.strip()
        if s in repeated or re.fullmatch(r"(page\s*)?\d{1,4}(\s*/\s*\d{1,4})?", s, re.I):
            continue
        lines.append(line)
    text = "\n".join(lines)
    # Join words hyphenated across line breaks: "informa-\ntion" -> "information"
    text = re.sub(r"(\w)-\n(?=[a-zà-ÿ])", r"\1", text)
    # Single newlines inside a paragraph -> space; keep blank lines as paragraph breaks
    text = re.sub(r"(?<!\n)\n(?!\n)", " ", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"\s*•\s*", "\n\n• ", text)
    return text.strip()


# ---------- 3. Language hint ----------
def detect_language(text: str) -> str:
    """Cheap heuristic: Arabic if many Arabic letters, else French/English by stopwords."""
    letters = [c for c in text if c.isalpha()]
    if not letters:
        return "unknown"
    arabic = sum(1 for c in letters if "\u0600" <= c <= "\u06FF")
    if arabic / len(letters) > 0.3:
        return "ar"
    words = set(re.findall(r"[a-zà-ÿ]+", text.lower()))
    fr = len(words & {"le", "la", "les", "des", "est", "une", "dans", "pour", "que", "et"})
    en = len(words & {"the", "is", "are", "of", "and", "to", "in", "that", "for", "with"})
    return "fr" if fr > en else "en"


# ---------- 4. Chunking ----------
def _build_units(pages: list[dict], repeated: set[str], chunk_size: int) -> list[tuple[int, str]]:
    """Cleaned paragraphs as (page_number, text). Oversized paragraphs are split."""
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=0, separators=SEPARATORS
    )
    units = []
    for p in pages:
        text = clean_text(p["text"], repeated)
        for para in re.split(r"\n{2,}", text):
            para = para.strip()
            if not para:
                continue
            if len(para) > chunk_size:
                units.extend((p["page"], piece) for piece in splitter.split_text(para))
            else:
                units.append((p["page"], para))
    return units


def chunk_pages(pages: list[dict], doc_name: str,
                chunk_size: int = config.CHUNK_SIZE,
                overlap: int = config.CHUNK_OVERLAP) -> list[dict]:
    """Merge consecutive paragraphs (across pages) into chunks of up to chunk_size
    characters, keeping the page range for citations."""
    repeated = _find_repeated_lines(pages)
    doc_lang = detect_language(" ".join(clean_text(p["text"], repeated) for p in pages))
    units = _build_units(pages, repeated, chunk_size)

    chunks = []

    def emit(group):
        idx = len(chunks)
        page_nums = [u[0] for u in group]
        chunks.append({
            "id": f"{doc_name}-c{idx}",
            "text": "\n\n".join(u[1] for u in group),
            "meta": {"doc": doc_name, "page_start": min(page_nums),
                     "page_end": max(page_nums), "chunk": idx, "lang": doc_lang},
        })

    current, current_len, fresh = [], 0, False
    for page, para in units:
        add = len(para) + 2
        if current and current_len + add > chunk_size:
            emit(current)
            # overlap: carry the last paragraphs (up to `overlap` chars) into the next chunk
            keep, total = [], 0
            for u in reversed(current):
                if total + len(u[1]) > overlap:
                    break
                keep.insert(0, u)
                total += len(u[1])
            current, current_len, fresh = keep, sum(len(u[1]) + 2 for u in keep), False
        current.append((page, para))
        current_len += add
        fresh = True
    if current and fresh:
        emit(current)
    return chunks

# ---------- Public entry point ----------
def ingest(path: str, chunk_size: int = config.CHUNK_SIZE,
           overlap: int = config.CHUNK_OVERLAP) -> list[dict]:
    pages = extract_pages(path)
    if is_scanned(pages):
        raise ValueError(f"'{path}' looks scanned (no extractable text). OCR needed.")
    return chunk_pages(pages, Path(path).name, chunk_size, overlap)