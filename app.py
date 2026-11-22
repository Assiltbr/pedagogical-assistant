"""Student-facing study app for course documents."""
import hashlib
from pathlib import Path

import streamlit as st

import config
from src.ingestion import ingest
from src.quiz import generate_quiz
from src.rag import answer
from src.summarizer import summarize
from src.vectorstore import add_chunks, delete_doc, get_doc_chunks, list_docs

UPLOAD_DIR = Path("data/uploads")
CACHE_DIR = Path("cache")
ALLOWED_EXTENSIONS = {".pdf", ".txt", ".md"}
TRANSLATIONS = {
    "A calmer way to learn": "Une façon plus sereine d'apprendre",
    "Upload a course to unlock your study tools.": "Ajoutez un cours pour utiliser vos outils d'étude.",
    "Home": "Accueil",
    "Study room": "Espace d'étude",
    "My library": "Ma bibliothèque",
    "YOUR COURSE COMPANION": "VOTRE COMPAGNON D'ÉTUDE",
    "Make your next study session count.": "Faites de votre prochaine séance un vrai moment d'étude.",
    "Bring a course document. Get focused notes, practice questions, and thoughtful answers grounded in what you are learning.": "Ajoutez un support de cours pour obtenir des notes claires, des questions d'entraînement et des réponses fondées sur son contenu.",
    "Start with a course document": "Commencez avec un support de cours",
    "PDF, TXT, or Markdown | Your documents stay in your local project": "PDF, TXT ou Markdown | Vos documents restent dans votre projet local",
    "Drop a course file here, or browse to upload": "Déposez un cours ici ou parcourez vos fichiers",
    "Ask your course": "Posez une question au cours",
    "Get clear answers with citations back to the material.": "Obtenez des réponses claires avec leurs références.",
    "Make useful notes": "Créez des fiches utiles",
    "Choose quick, medium, or detailed course summaries.": "Choisissez un résumé court, moyen ou détaillé.",
    "Practise what you learned": "Entraînez-vous",
    "Try verified multiple-choice questions at your level.": "Testez vos connaissances avec des QCM adaptés.",
    "Continue studying": "Continuer à étudier",
    "Pick up where you left off:": "Reprenez là où vous en étiez :",
    "YOUR LIBRARY": "VOTRE BIBLIOTHÈQUE",
    "Your course files": "Vos supports de cours",
    "Your library is empty. Upload a course document from Home to begin.": "Votre bibliothèque est vide. Ajoutez un support de cours depuis l'accueil.",
    "Course document | Chat, notes, and quiz": "Support de cours | Chat, fiches et quiz",
    "Open": "Ouvrir",
    "Remove": "Supprimer",
    "Cancel": "Annuler",
    "Remove course?": "Supprimer ce cours ?",
    "Are you sure you want to remove this course?": "Voulez-vous vraiment supprimer ce cours ?",
    "This removes the indexed course and any uploaded copy.": "Le cours indexé et sa copie importée seront supprimés.",
    "Confirm removal": "Confirmer la suppression",
    "course ready to study": "cours prêt à étudier",
    "courses ready to study": "cours prêts à étudier",
    "Ready to study {name} | {count} new sections indexed.": "{name} est prêt à étudier | {count} nouvelles sections indexées.",
    "STUDY ROOM": "ESPACE D'ÉTUDE",
    "Choose a course to get started": "Choisissez un cours pour commencer",
    "Your courses": "Vos cours",
    "Upload a PDF or text course from Home to open your study room.": "Ajoutez un cours PDF ou texte depuis l'accueil pour ouvrir votre espace d'étude.",
    "Course document": "Support de cours",
    "Add another course": "Ajouter un autre cours",
    "Choose a study mode": "Choisissez un mode d'étude",
    "Ask": "Discuter",
    "Summarize": "Résumer",
    "Quiz": "Quiz",
    "Question": "Question",
    "Your quiz": "Votre quiz",
    "Close quiz": "Fermer le quiz",
    "Close quiz": "Fermer le quiz",
    "Your answer:": "Votre réponse :",
    "Correct answer:": "Bonne réponse :",
    "Your score: {score} / {total}": "Votre score : {score} / {total}",
    "Open quiz": "Ouvrir le quiz",
    "Book companion for your course": "Support de cours ouvert et prêt à étudier",
    "Choose model": "Modèle",
    "Ask anything about this course...": "Posez une question sur ce cours...",
    "Choose the configured model provider for your chat.": "Choisissez le fournisseur de modèle pour vos échanges.",
    "How much detail?": "Quel niveau de détail ?",
    "Quick notes": "Fiche express",
    "Study summary": "Résumé de révision",
    "Detailed notes": "Fiche détaillée",
    "Create summary": "Créer le résumé",
    "Download notes": "Télécharger les fiches",
    "Choose a length to create clear, course-grounded notes.": "Choisissez un format pour créer des fiches claires basées sur le cours.",
    "Difficulty": "Difficulté",
    "Easy": "Facile",
    "Medium": "Moyen",
    "Hard": "Difficile",
    "Questions": "Questions",
    "Make a quiz": "Créer un quiz",
    "Choose a difficulty and question count to practise.": "Choisissez la difficulté et le nombre de questions.",
    "Check my answers": "Vérifier mes réponses",
    "Answers checked": "Réponses vérifiées",
    "Try another quiz": "Recommencer un quiz",
    "No verified questions could be made from this course. Try again.": "Aucune question vérifiée n'a pu être créée à partir de ce cours. Réessayez.",
    "Your course supported {count} verified questions.": "Votre cours a permis de créer {count} questions vérifiées.",
    "Choose one answer": "Choisissez une réponse",
    "no answer selected.": "aucune réponse choisie.",
    "correct.": "bonne réponse.",
    "not quite.": "ce n'est pas tout à fait ça.",
    "Your score": "Votre score",
    "View course sources": "Voir les sources du cours",
    "Section": "Section",
    "Section text": "Texte de la section",
    "Course text": "Texte du cours",
    "Course source": "Source du cours",
    "The original PDF is unavailable. Add the file again to preview it here.": "Le PDF original est introuvable. Ajoutez à nouveau le fichier pour l'afficher ici.",
    "Extracted course text": "Texte extrait du cours",
    "Your study room": "Votre espace d'étude",
    "Switch to light mode": "Passer en mode clair",
    "Switch to dark mode": "Passer en mode sombre",
    "Looking through your course...": "Recherche dans votre cours...",
    "Building notes from your course...": "Création des fiches à partir de votre cours...",
    "Writing questions from your course...": "Création des questions à partir de votre cours...",
}


def _t(text: str) -> str:
    if st.session_state.get("language", "en") == "fr":
        return TRANSLATIONS.get(text, text)
    return text

st.set_page_config(
    page_title="Studyroom | Course companion",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    :root {
        --ink: #1d2b45;
        --muted: #718096;
        --paper: #f7f6f2;
        --card: #ffffff;
        --line: #e8e8e2;
        --blue: #5478a8;
        --green: #648d79;
        --orange: #d98654;
    }
    [data-testid="stAppViewContainer"] { background: var(--paper); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] {
        background: #f0efe9;
        border-right: 1px solid var(--line);
    }
    [data-testid="stSidebar"] > div:first-child { padding-top: 0; }
    [data-testid="stSidebarUserContent"] { padding-top: 0; }
    [data-testid="stSidebarCollapseButton"],
    [data-testid="stSidebarCollapseButton"] * {
        visibility: visible !important;
        opacity: 1 !important;
        color: #1d2b45 !important;
        fill: #1d2b45 !important;
    }
    .block-container { max-width: 1440px; padding-top: 0; padding-bottom: 4rem; }
    h1, h2, h3 { color: #1d2b45 !important; letter-spacing: -0.035em; }
    h1 {
        font-family: "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive !important;
        font-weight: 500;
        letter-spacing: -0.02em;
    }
    p, label, li { color: #43516a; }
    [data-testid="stCaptionContainer"] { color: #718096 !important; }
    [data-testid="stFileUploader"] section {
        background: #fff;
        border: 1px dashed #aab9c8;
        border-radius: 18px;
    }
    [data-testid="stFileUploader"] section:hover { border-color: var(--blue); }
    [data-testid="stBaseButton-primary"] {
        background: var(--ink);
        border-color: var(--ink);
        border-radius: 10px;
        color: #ffffff !important;
    }
    [data-testid="stBaseButton-primary"] p { color: #ffffff !important; }
    [data-testid="stBaseButton-secondary"] {
        background: #ffffff;
        border-color: #e1e4e8;
        border-radius: 10px;
        color: var(--ink) !important;
    }
    [data-testid="stBaseButton-secondary"] p { color: var(--ink) !important; }
    [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
        background: transparent;
        border-color: transparent;
    }
    [data-testid="stTabs"] button { color: #59677e; }
    [data-testid="stTabs"] button[aria-selected="true"] {
        color: #1d2b45;
        border-color: var(--blue);
    }
    .brand-mark {
        position: relative;
        top: -60px;
        z-index: 20;
        color: #1d2b45;
        font-size: 1.1rem;
        font-weight: 750;
        letter-spacing: -0.03em;
        min-height: 38px;
        margin: 0 0 -40px;
        pointer-events: none;
    }
    .eyebrow {
        margin-bottom: 0.55rem;
        color: #bd6b39;
        font-size: 0.72rem;
        font-weight: 750;
        letter-spacing: 0.13em;
        text-transform: uppercase;
    }
    .hero-copy {
        max-width: 650px;
        margin: 0.4rem 0 1.8rem;
        color: var(--muted);
        font-size: 1.05rem;
        line-height: 1.7;
    }
    .book-art {
        display: block;
        width: min(100%, 290px);
        margin: 0 auto;
        filter: drop-shadow(0 18px 22px rgba(29, 43, 69, 0.12));
    }
    .feature-card {
        min-height: 178px;
        padding: 1.25rem;
        border: 1px solid var(--line);
        border-top: 3px solid var(--orange);
        border-radius: 18px;
        background-color: var(--card);
        background-image:
            linear-gradient(to right, transparent 1.1rem, rgba(217, 134, 84, 0.18) 1.1rem, rgba(217, 134, 84, 0.18) 1.17rem, transparent 1.17rem),
            repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(84, 120, 168, 0.15) 32px);
        box-shadow: 0 8px 26px rgba(29, 43, 69, 0.045);
    }
    .feature-card h3 {
        margin: 0 0 0.55rem;
        font-size: 1.02rem;
        letter-spacing: -0.02em;
        font-family: "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive;
        font-weight: 600;
        line-height: 1.75;
    }
    .feature-card p {
        margin: 0;
        color: #718096;
        font-size: 0.9rem;
        line-height: 2;
        font-family: "Segoe Print", "Bradley Hand", "Comic Sans MS", cursive;
    }
    .surface {
        padding: 1rem 1.15rem;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: var(--card);
    }
    .st-key-chat-workspace {
        border-top: 3px solid var(--orange) !important;
        border-radius: 20px !important;
        background: var(--card);
        box-shadow: 0 12px 32px rgba(29, 43, 69, 0.07);
    }
    [data-testid="stChatMessage"] {
        padding: 0.8rem 1rem;
        border: 1px solid var(--line);
        border-radius: 16px;
        background: var(--card);
    }
    [data-testid="stChatInput"] {
        border: 1px solid #d5dce5;
        border-radius: 16px;
        background: #ffffff;
    }
    [data-testid="stChatInput"] textarea {
        background: #ffffff !important;
        color: #1d2b45 !important;
        caret-color: #1d2b45;
    }
    [data-testid="stChatInput"] textarea::placeholder {
        color: #718096 !important;
        opacity: 1;
    }
    .st-key-theme_toggle button,
    .st-key-language_toggle button {
        min-width: 42px;
        height: 42px;
        border-radius: 14px;
    }
    [data-testid="stFileUploader"] section { border-color: #d98654; }
    [data-testid="stBaseButton-primary"] {
        background: #bd6b39;
        border-color: #bd6b39;
    }
    [data-testid="stBaseButton-primary"] p { color: #ffffff !important; }
    </style>
    """,
    unsafe_allow_html=True,
)

if st.session_state.get("dark_mode", False):
    st.markdown(
        """
        <style>
        [data-testid="stAppViewContainer"] { background: #121a27 !important; color: #e8edf5 !important; }
        [data-testid="stSidebar"] { background: #182235 !important; border-color: #2b3950 !important; }
        [data-testid="stSidebarCollapseButton"],
        [data-testid="stSidebarCollapseButton"] * {
            color: #f3f5f8 !important;
            fill: #f3f5f8 !important;
            opacity: 1 !important;
            visibility: visible !important;
        }
        h1, h2, h3, h4 { color: #e8edf5 !important; }
        p, label, li, [data-testid="stCaptionContainer"] { color: #b7c2d2 !important; }
        .brand-mark, .feature-card h3 { color: #e8edf5 !important; }
        .feature-card, .surface, [data-testid="stFileUploader"] section {
            background: #1b273a !important;
            border-color: #34445c !important;
        }
        .feature-card {
            background-image:
                linear-gradient(to right, transparent 1.1rem, rgba(217, 134, 84, 0.25) 1.1rem, rgba(217, 134, 84, 0.25) 1.17rem, transparent 1.17rem),
                repeating-linear-gradient(to bottom, transparent 0, transparent 31px, rgba(169, 197, 232, 0.14) 32px) !important;
        }
        .feature-card p { color: #b7c2d2 !important; }
        .book-art { filter: drop-shadow(0 18px 24px rgba(0, 0, 0, 0.3)); }
        [data-testid="stTextArea"] textarea,
        [data-testid="stChatInput"] textarea,
        [data-testid="stSelectbox"] [data-baseweb="select"] > div,
        [data-testid="stNumberInput"] input {
            background: #202d41 !important;
            border-color: #3a4b64 !important;
            color: #e8edf5 !important;
        }
        [data-testid="stChatInput"] {
            background: #202d41 !important;
            border-color: #4a5d79 !important;
        }
        [data-testid="stChatInput"] textarea {
            background: #202d41 !important;
            color: #f3f5f8 !important;
            caret-color: #f3f5f8 !important;
        }
        [data-testid="stChatInput"] textarea::placeholder {
            color: #b7c2d2 !important;
            opacity: 1;
        }
        [data-testid="stBaseButton-secondary"] {
            background: #202d41 !important;
            border-color: #3a4b64 !important;
            color: #e8edf5 !important;
        }
        [data-testid="stBaseButton-primary"] {
            background: #5478a8 !important;
            border-color: #5478a8 !important;
        }
        [data-testid="stBaseButton-secondary"] p { color: #e8edf5 !important; }
        [data-testid="stChatMessage"], .st-key-chat-workspace {
            background: #1b273a !important;
            border-color: #34445c !important;
        }
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] {
            background: transparent !important;
            border-color: transparent !important;
        }
        [data-testid="stSidebar"] [data-testid="stBaseButton-secondary"] p {
            color: #d3dbea !important;
        }
        .st-key-theme_toggle button,
        .st-key-language_toggle button {
            background: #202d41 !important;
            border-color: #3a4b64 !important;
            color: #e8edf5 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

def _navigate(page: str) -> None:
    st.session_state["page"] = page


def _set_theme(dark_mode: bool) -> None:
    st.session_state["dark_mode"] = dark_mode


def _open_document(doc_name: str) -> None:
    st.session_state["selected_doc"] = doc_name
    st.session_state["page"] = "Study room"


def _request_remove_document(doc_name: str) -> None:
    st.session_state["confirm_remove_doc"] = doc_name


def _cancel_remove_document() -> None:
    st.session_state.pop("confirm_remove_doc", None)


def _remove_document(doc_name: str) -> None:
    delete_doc(doc_name)

    upload_path = UPLOAD_DIR / Path(doc_name).name
    if upload_path.is_file():
        upload_path.unlink()

    cache_prefix = hashlib.md5(doc_name.encode("utf-8")).hexdigest()
    if CACHE_DIR.is_dir():
        for cache_file in CACHE_DIR.glob(f"{cache_prefix}_*.json"):
            cache_file.unlink()

    st.session_state.get("chat_histories", {}).pop(doc_name, None)
    summaries = st.session_state.get("summaries", {})
    for key in list(summaries):
        if isinstance(key, tuple) and key[0] == doc_name:
            del summaries[key]
    st.session_state.get("quizzes", {}).pop(doc_name, None)
    st.session_state.get("submitted_quizzes", set()).discard(doc_name)
    st.session_state.get("generated_quizzes", set()).discard(doc_name)
    for key in list(st.session_state):
        if key.startswith(f"quiz_answer_{doc_name}_"):
            del st.session_state[key]
    if st.session_state.get("selected_doc") == doc_name:
        st.session_state.pop("selected_doc", None)
    _cancel_remove_document()


def _new_document_name(filename: str, existing: set[str]) -> str:
    safe_name = Path(filename).name
    suffix = Path(safe_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise ValueError("Please upload a PDF, TXT, or Markdown course file.")

    stem = Path(safe_name).stem
    candidate = safe_name
    number = 2
    while candidate in existing or (UPLOAD_DIR / candidate).exists():
        candidate = f"{stem} ({number}){suffix}"
        number += 1
    return candidate


def _index_upload(uploaded_file, existing: set[str]) -> tuple[str, int] | None:
    content = uploaded_file.getvalue()
    digest = hashlib.sha256(content).hexdigest()
    upload_token = f"{uploaded_file.name}:{digest}"
    if st.session_state.get("last_upload_token") == upload_token:
        return None

    doc_name = _new_document_name(uploaded_file.name, existing)
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    path = UPLOAD_DIR / doc_name
    path.write_bytes(content)

    try:
        chunks = ingest(str(path))
    except ValueError as error:
        path.unlink(missing_ok=True)
        st.error(str(error))
        return None

    for chunk in chunks:
        chunk["id"] = f"{doc_name}-c{chunk['meta']['chunk']}"
        chunk["meta"]["doc"] = doc_name
    added = add_chunks(chunks)

    st.session_state["last_upload_token"] = upload_token
    st.session_state["selected_doc"] = doc_name
    st.session_state["page"] = "Study room"
    return doc_name, added


def _render_sources(sources: list[dict]) -> None:
    if not sources:
        return
    with st.expander(_t("View course sources")):
        for source in sources:
            st.markdown(f"**{source['doc']} | {source['pages']}**")
            st.caption(source["text"])


def _document_path(doc_name: str) -> Path | None:
    safe_name = Path(doc_name).name
    for folder in (UPLOAD_DIR, Path("data/sample_courses")):
        path = folder / safe_name
        if path.is_file():
            return path
    return None


def _render_document(doc_name: str) -> None:
    st.markdown(f"**{doc_name}**")
    path = _document_path(doc_name)
    if Path(doc_name).suffix.lower() == ".pdf":
        if path is None:
            st.warning(_t("The original PDF is unavailable. Add the file again to preview it here."))
            return
        st.pdf(path.read_bytes(), height=780, key=f"document_{doc_name}")
        return
    if path is not None:
        st.text_area(
            _t("Course text"),
            path.read_text(encoding="utf-8"),
            height=700,
            disabled=True,
            label_visibility="collapsed",
        )
        return

    chunks = get_doc_chunks(doc_name)
    if not chunks:
        st.info("The original file is not available in this session.")
        return
    st.caption(_t("Extracted course text"))
    section = st.selectbox(
        _t("Section"),
        range(len(chunks)),
        format_func=lambda index: f"{_t('Section')} {index + 1}",
        key=f"section_{doc_name}",
    )
    st.text_area(
        _t("Section text"),
        chunks[section]["text"],
        height=650,
        disabled=True,
        label_visibility="collapsed",
    )


def _render_chat(doc_name: str) -> None:
    backends = list(config.BACKENDS)
    default_backend = config.LLM_BACKEND if config.LLM_BACKEND in backends else backends[0]
    with st.container(border=True, key="chat-workspace"):
        header, model_column = st.columns([5, 1.25], gap="medium", vertical_alignment="center")
        with header:
            st.subheader(_t("Ask your course"))
        with model_column:
            backend = st.selectbox(
                _t("Choose model"),
                backends,
                index=backends.index(default_backend),
                format_func=lambda name: name.title(),
                key="chat_backend",
                label_visibility="collapsed",
                help=_t("Choose the configured model provider for your chat."),
            )

        histories = st.session_state.setdefault("chat_histories", {})
        history = histories.setdefault(doc_name, [])
        with st.container():
            for message in history:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])
                    _render_sources(message.get("sources", []))

        prompt = st.chat_input(
            _t("Ask anything about this course..."),
            key=f"chat_input_{doc_name}",
        )
        if prompt:
            history.append({"role": "user", "content": prompt})
            with st.spinner(_t("Looking through your course...")):
                result = answer(prompt, doc=doc_name, backend=backend)
            history.append({
                "role": "assistant",
                "content": result["answer"],
                "sources": result["sources"],
            })
            st.rerun()


def _render_summary(doc_name: str) -> None:
    levels = {
        _t("Quick notes"): "short",
        _t("Study summary"): "medium",
        _t("Detailed notes"): "detailed",
    }
    choice = st.selectbox(
        _t("How much detail?"),
        list(levels),
        key=f"summary_level_{doc_name}",
    )
    summaries = st.session_state.setdefault("summaries", {})
    summary_key = (doc_name, levels[choice])
    if st.button(_t("Create summary"), type="primary", key=f"summarize_{doc_name}"):
        with st.spinner(_t("Building notes from your course...")):
            summaries[summary_key] = summarize(doc_name, level=levels[choice])

    if summary_key in summaries:
        with st.container(border=True):
            st.markdown(summaries[summary_key])
        st.download_button(
            _t("Download notes"),
            summaries[summary_key],
            file_name=f"{Path(doc_name).stem}-{levels[choice]}-notes.txt",
            mime="text/plain",
            key=f"download_summary_{doc_name}_{levels[choice]}",
        )
    else:
        st.caption(_t("Choose a length to create clear, course-grounded notes."))


@st.dialog("Your quiz", width="large")
def _show_quiz_dialog(doc_name: str) -> None:
    questions = st.session_state["quizzes"][doc_name]
    submitted = doc_name in st.session_state["submitted_quizzes"]
    answers = st.session_state.setdefault("quiz_answers", {})

    if not submitted:
        with st.form(f"quiz_form_{doc_name}"):
            for index, question in enumerate(questions):
                with st.container(border=True):
                    st.markdown(f"**{_t('Question')} {index + 1}**")
                    st.markdown(question.question)
                    st.radio(
                        _t("Choose one answer"),
                        range(len(question.options)),
                        format_func=lambda choice, options=question.options: options[choice],
                        index=None,
                        key=f"quiz_answer_{doc_name}_{index}",
                        label_visibility="collapsed",
                    )
            checked = st.form_submit_button(_t("Check my answers"), type="primary")
        if checked:
            st.session_state["submitted_quizzes"].add(doc_name)
            st.rerun()
        return

    correct_count = 0
    for index, question in enumerate(questions):
        selected = st.session_state.get(f"quiz_answer_{doc_name}_{index}")
        correct_count += int(selected == question.answer_index)
        with st.container(border=True):
            st.markdown(f"**{_t('Question')} {index + 1}**")
            st.markdown(question.question)
            if selected is not None:
                st.markdown(f"**{_t('Your answer:')}** {question.options[selected]}")
            st.markdown(
                f"**{_t('Correct answer:')}** {question.options[question.answer_index]}"
            )
            st.caption(f"{question.explanation} | {question.source_pages or _t('Course source')}")
    st.success(
        _t("Your score: {score} / {total}").format(
            score=correct_count, total=len(questions)
        )
    )
    if st.button(_t("Close quiz"), key=f"close_quiz_{doc_name}"):
        st.session_state.pop("quiz_dialog_doc", None)
        st.rerun()


def _render_quiz(doc_name: str) -> None:
    difficulty_labels = {_t("Easy"): "easy", _t("Medium"): "medium", _t("Hard"): "hard"}
    controls = st.columns(2)
    with controls[0]:
        difficulty_label = st.selectbox(
            _t("Difficulty"),
            list(difficulty_labels),
            key=f"quiz_difficulty_{doc_name}",
        )
    with controls[1]:
        question_count = st.selectbox(
            _t("Questions"),
            [3, 5, 8],
            key=f"quiz_count_{doc_name}",
        )

    quizzes = st.session_state.setdefault("quizzes", {})
    st.session_state.setdefault("submitted_quizzes", set())
    generated_quizzes = st.session_state.setdefault("generated_quizzes", set())
    if st.button(_t("Make a quiz"), type="primary", key=f"generate_quiz_{doc_name}"):
        with st.spinner(_t("Writing questions from your course...")):
            questions = generate_quiz(
                doc_name,
                n=question_count,
                difficulty=difficulty_labels[difficulty_label],
            )
        quizzes[doc_name] = questions
        st.session_state["submitted_quizzes"].discard(doc_name)
        generated_quizzes.add(doc_name)
        st.session_state.pop("quiz_dialog_doc", None)
        if questions:
            st.session_state["quiz_dialog_doc"] = doc_name
        for index in range(8):
            st.session_state.pop(f"quiz_answer_{doc_name}_{index}", None)

    questions = quizzes.get(doc_name, [])
    if not questions:
        if doc_name in generated_quizzes:
            st.warning(_t("No verified questions could be made from this course. Try again."))
        else:
            st.caption(_t("Choose a difficulty and question count to practise."))
        return

    if st.session_state.get("quiz_dialog_doc") == doc_name:
        _show_quiz_dialog(doc_name)
    else:
        if st.button(_t("Open quiz"), key=f"open_quiz_{doc_name}"):
            st.session_state["quiz_dialog_doc"] = doc_name
            st.rerun()
        if doc_name in st.session_state["submitted_quizzes"]:
            if st.button(_t("Try another quiz"), key=f"reset_quiz_{doc_name}"):
                quizzes.pop(doc_name, None)
                st.session_state["submitted_quizzes"].discard(doc_name)
                generated_quizzes.discard(doc_name)
                st.session_state.pop("quiz_dialog_doc", None)
                for index in range(8):
                    st.session_state.pop(f"quiz_answer_{doc_name}_{index}", None)
                st.rerun()


def _home_page(documents: list[str]) -> None:
    st.markdown(
        f'<div class="eyebrow">{_t("YOUR COURSE COMPANION")}</div>',
        unsafe_allow_html=True,
    )
    hero_copy, hero_art = st.columns([1.5, 0.7], vertical_alignment="center")
    with hero_copy:
        st.title(_t("Make your next study session count."))
        st.markdown(
            f'<p class="hero-copy">{_t("Bring a course document. Get focused notes, practice questions, and thoughtful answers grounded in what you are learning.")}</p>',
            unsafe_allow_html=True,
        )
    with hero_art:
        st.markdown(
            """
            <svg class="book-art" viewBox="0 0 280 220" role="img"
                 aria-label="Book companion for your course">
              <circle cx="142" cy="111" r="95" fill="#F2EDE4"/>
              <path d="M37 67c37-11 65-5 91 14v104c-27-19-55-24-91-12V67Z"
                    fill="#fffdf8" stroke="#304563" stroke-width="4" stroke-linejoin="round"/>
              <path d="M220 67c-37-11-65-5-92 14v104c28-19 56-24 92-12V67Z"
                    fill="#f3f6fa" stroke="#304563" stroke-width="4" stroke-linejoin="round"/>
              <path d="M128 81v104" fill="none" stroke="#d98654" stroke-width="4"/>
              <path d="M56 93c22-5 39-2 57 7M56 113c22-5 39-2 57 7M56 133c22-5 39-2 57 7"
                    fill="none" stroke="#9eafbf" stroke-width="3" stroke-linecap="round"/>
              <path d="M145 99c18-8 35-10 57-6M145 119c18-8 35-10 57-6M145 139c18-8 35-10 57-6"
                    fill="none" stroke="#9eafbf" stroke-width="3" stroke-linecap="round"/>
              <path d="m213 34 5 12 12 5-12 5-5 12-5-12-12-5 12-5 5-12Z"
                    fill="#d98654"/>
              <circle cx="65" cy="46" r="5" fill="#648d79"/>
            </svg>
            """,
            unsafe_allow_html=True,
        )
    st.subheader(_t("Start with a course document"))
    st.caption(_t("PDF, TXT, or Markdown | Your documents stay in your local project"))
    uploaded_file = st.file_uploader(
        _t("Drop a course file here, or browse to upload"),
        type=["pdf", "txt", "md"],
        label_visibility="collapsed",
        key="course_upload",
    )
    if uploaded_file is not None:
        result = _index_upload(uploaded_file, set(documents))
        if result is not None:
            name, count = result
            st.success(
                _t("Ready to study {name} | {count} new sections indexed.").format(
                    name=f"**{name}**", count=count
                )
            )
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)
    cards = st.columns(3, gap="medium")
    features = [
        ("Ask your course", "Get clear answers with citations back to the material."),
        ("Make useful notes", "Choose quick, medium, or detailed course summaries."),
        ("Practise what you learned", "Try verified multiple-choice questions at your level."),
    ]
    for column, (title, description) in zip(cards, features):
        with column:
            st.markdown(
                f'<div class="feature-card"><h3>{_t(title)}</h3>'
                f"<p>{_t(description)}</p></div>",
                unsafe_allow_html=True,
            )

    selected_doc = st.session_state.get("selected_doc")
    if selected_doc and selected_doc in documents:
        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown(f"**{_t('Pick up where you left off:')}** {selected_doc}")
        st.button(
            _t("Continue studying"),
            type="primary",
            key="continue_studying",
            on_click=_navigate,
            args=("Study room",),
        )


def _library_page(documents: list[str]) -> None:
    st.markdown(f'<div class="eyebrow">{_t("YOUR LIBRARY")}</div>', unsafe_allow_html=True)
    st.title(_t("Your course files"))
    if not documents:
        st.info(_t("Your library is empty. Upload a course document from Home to begin."))
        return

    count_label = _t("course ready to study") if len(documents) == 1 else _t(
        "courses ready to study"
    )
    st.caption(f"{len(documents)} {count_label}")
    for index, doc_name in enumerate(documents):
        with st.container(border=True):
            row = st.columns([5, 1, 1])
            row[0].markdown(f"**{doc_name}**")
            row[0].caption(_t("Course document | Chat, notes, and quiz"))
            row[1].button(
                _t("Open"),
                key=f"open_document_{index}",
                on_click=_open_document,
                args=(doc_name,),
            )
            row[2].button(
                _t("Remove"),
                key=f"remove_document_{index}",
                on_click=_request_remove_document,
                args=(doc_name,),
            )
        if st.session_state.get("confirm_remove_doc") == doc_name:
            st.warning(f"{_t('Are you sure you want to remove this course?')} **{doc_name}**")
            confirm, cancel, _ = st.columns([1.5, 1, 5])
            if confirm.button(_t("Confirm removal"), key=f"confirm_remove_{index}"):
                _remove_document(doc_name)
                st.rerun()
            cancel.button(
                _t("Cancel"),
                key=f"cancel_remove_{index}",
                on_click=_cancel_remove_document,
            )


def _study_page(documents: list[str]) -> None:
    doc_name = st.session_state.get("selected_doc")
    if doc_name not in documents:
        st.markdown(f'<div class="eyebrow">{_t("STUDY ROOM")}</div>', unsafe_allow_html=True)
        st.title(_t("Choose a course to get started"))
        if documents:
            choice = st.selectbox(_t("Your courses"), documents)
            st.session_state["selected_doc"] = choice
            st.rerun()
        else:
            st.info(_t("Upload a PDF or text course from Home to open your study room."))
        return

    st.markdown(f'<div class="eyebrow">{_t("STUDY ROOM")}</div>', unsafe_allow_html=True)
    st.title(_t("Your study room"))
    left, right = st.columns([0.85, 1.3], gap="large")
    with left:
        st.markdown(f"#### {_t('Course document')}")
        additional_file = st.file_uploader(
            _t("Add another course"),
            type=["pdf", "txt", "md"],
            key=f"add_course_{doc_name}",
        )
        if additional_file is not None:
            result = _index_upload(additional_file, set(documents))
            if result is not None:
                st.rerun()
        _render_document(doc_name)
    with right:
        mode_key = f"study_mode_{doc_name}"
        mode = st.session_state.get(mode_key, "Ask")
        mode_columns = st.columns(3, gap="small")
        selected_mode = None
        for column, option, label in zip(
            mode_columns,
            ("Ask", "Summarize", "Quiz"),
            (_t("Ask"), _t("Summarize"), _t("Quiz")),
        ):
            if column.button(
                label,
                type="primary" if mode == option else "secondary",
                use_container_width=True,
                key=f"study_mode_button_{doc_name}_{option}",
            ):
                selected_mode = option
        if selected_mode is not None:
            st.session_state[mode_key] = selected_mode
            mode = selected_mode
            st.rerun()
        if mode == "Ask":
            _render_chat(doc_name)
        elif mode == "Summarize":
            _render_summary(doc_name)
        elif mode == "Quiz":
            _render_quiz(doc_name)


if "page" not in st.session_state:
    st.session_state["page"] = "Home"

with st.sidebar:
    st.markdown('<div class="brand-mark">Studyroom</div>', unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)
    for page in ("Home", "Study room", "My library"):
        st.button(
            _t(page),
            type="primary" if st.session_state["page"] == page else "secondary",
            use_container_width=True,
            key=f"nav_{page}",
            on_click=_navigate,
            args=(page,),
        )

dark_mode = st.session_state.get("dark_mode", False)
language = st.session_state.get("language", "en")
_, theme_column, language_column = st.columns([24, 1, 1])
with theme_column:
    if st.button(
        "☀" if dark_mode else "☾",
        help=_t("Switch to light mode") if dark_mode else _t("Switch to dark mode"),
        type="secondary",
        key="theme_toggle",
        use_container_width=True,
    ):
        _set_theme(not dark_mode)
        st.rerun()
with language_column:
    if st.button(
        "EN" if language == "fr" else "FR",
        help=_t("Switch language to English" if language == "fr" else "Switch language to French"),
        type="secondary",
        key="language_toggle",
        use_container_width=True,
    ):
        st.session_state["language"] = "en" if language == "fr" else "fr"
        st.rerun()

documents = list_docs()
current_page = st.session_state["page"]
if current_page == "My library":
    _library_page(documents)
elif current_page == "Study room":
    _study_page(documents)
else:
    _home_page(documents)