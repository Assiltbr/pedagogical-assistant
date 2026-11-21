import sys
from src.ingestion import ingest

chunks = ingest(sys.argv[1])
print(f"{len(chunks)} chunks, lang={chunks[0]['meta']['lang']}")

with open("arabic_check.txt", "w", encoding="utf-8") as f:
    for c in chunks[:5]:
        f.write(f"--- {c['id']} (pages {c['meta']['page_start']}-{c['meta']['page_end']}) ---\n")
        f.write(c["text"] + "\n\n")