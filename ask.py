import sys
from src.rag import answer

q = sys.argv[1]
doc = sys.argv[2] if len(sys.argv) > 2 else None
r = answer(q, doc=doc)
with open("answer.txt", "w", encoding="utf-8") as f:
    f.write(f"Q: {q}\n\nA: {r['answer']}\n\n")
    for s in r["sources"]:
        f.write(f"[{s['n']}] {s['doc']} {s['pages']} (score {s['score']})\n")
print(open("answer.txt", encoding="utf-8").read())