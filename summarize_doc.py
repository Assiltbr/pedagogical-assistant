import sys
from src.summarizer import summarize

doc = sys.argv[1]
lang = sys.argv[2] if len(sys.argv) > 2 else None
with open("summary.txt", "w", encoding="utf-8") as f:
    for level in ("short", "medium", "detailed"):
        s = summarize(doc, level, lang)
        print(f"{level}: {len(s.split())} words")
        f.write(f"===== {level.upper()} ({len(s.split())} words) =====\n{s}\n\n")