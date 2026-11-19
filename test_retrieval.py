import sys
from src.ingestion import ingest
from src.vectorstore import add_chunks, search

chunks = ingest(sys.argv[1])
print("Indexed:", add_chunks(chunks), "new chunks of", len(chunks))

for q in ["Qu'est-ce que le TALN ?",
          "What is named entity recognition?",
          "ما هو معالجة اللغة الطبيعية؟",
          "Quelle est la recette du couscous ?"]:      # out-of-scope control
    print(f"\nQ: {q}")
    for h in search(q, k=3):
        m = h["meta"]
        print(f"  {h['score']:.3f}  p.{m['page_start']}-{m['page_end']}  {h['text'][:90]!r}")