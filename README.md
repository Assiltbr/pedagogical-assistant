# Studyroom - pedagogical assistant

Studyroom helps students work with their course documents. Upload a PDF, TXT, or
Markdown file to create grounded summaries, multiple-choice quizzes, and a
question-and-answer chat with course citations.
Choose a study mode inside each room, add more course files without leaving the
room, select a configured model for chat, and switch between light and dark
appearance with the sun and moon controls. The interface can also switch between
English and French, and courses can be removed from the library.

## Run locally

From the project directory on Windows:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
streamlit run app.py
```

Configure a supported model provider in `.env` before using the study tools.
Uploaded files are stored under `data/uploads/`; the document index and generated
notes use the existing `chroma_db/` and `cache/` folders.

