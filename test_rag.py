from src.rag import answer

questions = [
    "Qu'est-ce que le TALN ?",
    "What is named entity recognition?",
    "ما هو معالجة اللغة الطبيعية؟",
    "Quelle est la recette du couscous ?",
    "Who is the president of France?",
]
for q in questions:
    r = answer(q)
    print(f"\nQ: {q}\nA: {r['answer']}")
    for s in r["sources"]:
        print(f"   [{s['n']}] {s['doc']} {s['pages']} (score {s['score']})")