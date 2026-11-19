import sys
from collections import Counter
from src.ingestion import ingest

path = sys.argv[1]
for size in (500, 1000, 1500):
    chunks = ingest(path, chunk_size=size, overlap=int(size * 0.15))
    avg = sum(len(c["text"]) for c in chunks) / len(chunks)
    langs = Counter(c["meta"]["lang"] for c in chunks)
    print(f"chunk_size={size}: {len(chunks)} chunks, avg {avg:.0f} chars, langs={dict(langs)}")

chunks = ingest(path)
for c in chunks[:3]:
    print("\n---", c["id"], c["meta"]["lang"], "---")
    print(c["text"][:400])