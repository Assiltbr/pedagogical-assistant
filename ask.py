import sys
import config
from src.rag import answer

q = sys.argv[1]
doc = sys.argv[2] if len(sys.argv) > 2 else None
k = int(sys.argv[3]) if len(sys.argv) > 3 else config.TOP_K
r = answer(q, k=k, doc=doc)
with open("answer.txt", "w", encoding="utf-8") as f:
    f.write(f"Q: {q}\n\nA: {r['answer']}\n\n")
    for s in r["sources"]:
        f.write(f"[{s['n']}] {s['doc']} {s['pages']} (score {s['score']})\n")
print(open("answer.txt", encoding="utf-8").read())