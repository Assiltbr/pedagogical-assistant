import sys
from src.quiz import generate_quiz

doc = sys.argv[1]
difficulty = sys.argv[2] if len(sys.argv) > 2 else "medium"
n = int(sys.argv[3]) if len(sys.argv) > 3 else 3
lang = sys.argv[4] if len(sys.argv) > 4 else None

quiz = generate_quiz(doc, n=n, difficulty=difficulty, lang=lang)
with open("quiz.txt", "w", encoding="utf-8") as f:
    f.write(f"Requested {n} {difficulty} questions, got {len(quiz)} valid\n\n")
    for i, q in enumerate(quiz, 1):
        f.write(f"Q{i}. {q.question}\n")
        for letter, opt in zip("ABCD", q.options):
            f.write(f"   {letter}) {opt}\n")
        f.write(f"   Answer: {'ABCD'[q.answer_index]}  ({q.source_pages})\n")
        f.write(f"   Why: {q.explanation}\n\n")
print(open("quiz.txt", encoding="utf-8").read())