# Scheme Saathi — Complete Project Report

**Document version:** 1.0  
**Last updated:** February 2025  
**Project:** AI-powered government scheme finder for Indian citizens  

---

## 1. Executive Summary

**Scheme Saathi** is a full-stack application that helps Indian citizens discover government schemes (scholarships, pensions, loans, subsidies, etc.) through an AI chatbot. Users describe their situation (occupation, state, type of help needed, gender, age, caste) in natural language; the system gathers context, searches a vector database of 3,700+ schemes, filters by eligibility, and returns matched schemes with clickable apply links. The app supports **English and Hindi**, **voice input and output**, and a **professional landing page + chat UI** with expandable scheme cards.

**Core value:** One conversational interface to find relevant schemes without browsing multiple government portals.

---

## 2. High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND (React + Vite)                         │
│  Landing (/) │ Chat (/chat, /chat/:chatId) │ Navbar, Sidebar, Voice     │
└─────────────────────────────────────────────────────────────────────────┘
                                      │
                              HTTP (axios, /chat, /search, /schemes, /health)
                                      ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      BACKEND (FastAPI, Python 3.x)                       │
│  main.py: routes, context extraction, eligibility filters                │
│  gemini_service: system prompt, chat (OpenAI GPT 5.2 or Gemini)        │
│  rag_service: ChromaDB search + hard eligibility filter                 │
│  embedding_function: OpenAI text-embedding-3-large                       │
└─────────────────────────────────────────────────────────────────────────┘
         │                              │
         │                              │
         ▼                              ▼
┌─────────────────────┐    ┌─────────────────────────────────────────────┐
│  ChromaDB            │    │  data_f/all_schemes.json                     │
│  (chroma_db/)        │    │  ~3,793 schemes (enriched, structured)       │
│  Vectors from        │    │  source_url, official_website, eligibility,  │
│  OpenAI embeddings   │    │  benefits, required_documents, etc.         │
└─────────────────────┘    └─────────────────────────────────────────────┘
```

- **Frontend:** React 18, Vite 6, React Router 7, Tailwind CSS, Framer Motion, Axios, React Markdown, React Hot Toast, Lucide React.  
- **Backend:** FastAPI, Uvicorn, Pydantic, ChromaDB, OpenAI API (embeddings + chat), optional Google Gemini.  
- **Data:** Single source of truth `backend/data_f/all_schemes.json`; vector index in `backend/chroma_db/`.

---

## 3. Repository Structure

```
Buildathon pt 2/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, all routes, context extraction, filters
│   │   ├── config.py           # Pydantic Settings (env: .env)
│   │   ├── models.py           # ChatMessage, ChatRequest, ChatResponse, HealthResponse, scheme models
│   │   ├── services/
│   │   │   ├── gemini_service.py   # System prompt builder, chat (OpenAI or Gemini), health
│   │   │   ├── rag_service.py      # ChromaDB init, search_schemes, filter_schemes_by_eligibility
│   │   │   └── scheme_matcher.py   # (if used)
│   │   └── utils/
│   │       ├── data_loader.py      # load_schemes_from_json, prepare_scheme_text_for_embedding, resilient JSON parse
│   │       └── embedding_function.py # get_embedding_function() → OpenAI text-embedding-3-large
│   ├── data_f/
│   │   ├── all_schemes.json    # Main scheme dataset (~3,793 schemes)
│   │   └── all_schemes_backup.json
│   ├── chroma_db/              # ChromaDB persistent store (SQLite + segment binaries)
│   ├── pipeline/
│   │   ├── auto_update_pipeline.py  # Scrape → merge → enrich → vectordb, reports
│   │   ├── daemon.py           # 24h loop (disabled by default)
│   │   ├── pipeline_config.json
│   │   ├── README.md
│   │   └── reports/            # latest.json, run_*.json, daemon_status.json
│   ├── build_vectordb.py       # Load all_schemes.json → OpenAI embed → ChromaDB (batch 20, delay 16s)
│   ├── enrich_data.py          # Re-extract state, occupation, benefit_type, gender, caste, age from text
│   ├── run_data_update_pipeline.py
│   ├── run_data_update_daemon.py
│   ├── requirements.txt
│   ├── .env.example
│   └── README.md
├── frontend/
│   ├── src/
│   │   ├── App.jsx             # Router: /, /chat, /chat/:chatId, 404
│   │   ├── main.jsx, index.css
│   │   ├── pages/
│   │   │   ├── HomePage.jsx    # Landing
│   │   │   ├── ChatPage.jsx    # Chat container + layout
│   │   │   └── NotFound.jsx
│   │   ├── components/
│   │   │   ├── chat/           # ChatContainer, ChatInput, ChatMessages, Message, SchemeCard, VoiceButton, etc.
│   │   │   ├── common/         # Button, Badge, Card, LoadingSpinner
│   │   │   ├── landing/        # Hero, Features, HowItWorks, Statistics, CTA, Footer
│   │   │   └── layout/         # Navbar, PageLayout, Footer
│   │   ├── hooks/
│   │   │   └── useVoice.js     # Web Speech API: STT, TTS, silence detection, Hindi/English
│   │   ├── services/
│   │   │   ├── api.js          # sendChatMessage, getHealthStatus, listSchemes, getSchemeById, searchSchemes
│   │   │   └── storage.js      # getAllChats, getChatById, saveMessageToChat, deleteChat, currentChatId
│   │   └── utils/
│   │       ├── constants.js   # API_BASE_URL, FEATURES, SUGGESTIONS (en/hi), etc.
│   │       ├── i18n.js         # useTranslation, UI_TEXT (en/hi)
│   │       └── chatHelpers.js
│   ├── package.json
│   └── tailwind.config.js
├── scraper/                    # Category scrapers (MyScheme / official sources)
│   ├── *_scraper.py            # Per-category scrapers
│   ├── data_cleaner.py, manual_data.py
│   ├── extraction/             # benefits_parser, documents_extractor, eligibility_parser, quality_scorer
│   └── utils/selenium_helper.py
├── data/                       # Scraped outputs by category (from_urls/*.json), URL lists
├── ex-machina/                 # Alternate scraper/run scripts
├── .gitignore
├── README.md
└── PROJECT_REPORT.md           # This file
```

---

## 4. Backend — Detailed Description

### 4.1 Configuration (`app/config.py`)

| Variable | Purpose | Default |
|----------|---------|---------|
| `GEMINI_API_KEY` | Gemini (fallback chat) | `"placeholder"` |
| `OPENAI_API_KEY` | Embeddings + chat when OpenAI used | `""` |
| `OPENAI_EMBEDDING_MODEL` | ChromaDB embedding model | `"text-embedding-3-large"` |
| `OPENAI_CHAT_MODEL` | Chat LLM when using OpenAI | `"gpt-5.2-chat-latest"` |
| `GEMINI_MODEL` | Chat when not using OpenAI | `"gemini-3-pro-preview"` |
| `APP_NAME`, `APP_VERSION` | API identity | Scheme Saathi, 1.0.0 |
| `SCHEMES_DATA_PATH` | Path to schemes JSON | `data_f/all_schemes.json` |
| `CHROMA_DB_PATH` | ChromaDB directory | `chroma_db` |
| `TOP_K_SCHEMES` | Default RAG retrieval size | 10 |
| `SIMILARITY_THRESHOLD` | Min score for RAG hit | 0.3 |
| `ALLOWED_ORIGINS` | CORS | localhost:3000, 5173 |

Chat behaviour: if `OPENAI_CHAT_MODEL` is set and `OPENAI_API_KEY` is set, chat uses **OpenAI** (e.g. GPT 5.2); otherwise **Gemini**.

### 4.2 API Endpoints (`app/main.py`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Root: `{ app, version, status, message, docs_url }` |
| GET | `/health` | Health: status, app_name, version, gemini_status, vector_db_status, total_schemes, timestamp |
| POST | `/chat` | Main chat: body `message`, `conversation_history`, `user_context`, `language` → `message`, `schemes`, `needs_more_info`, `extracted_context` |
| GET | `/schemes` | List schemes; query `category`, `state`, `limit` |
| GET | `/schemes/categories` | List unique categories |
| GET | `/schemes/{scheme_id}` | Single scheme by ID |
| POST | `/search` | Semantic search; body `query`, `state`, `category`, `top_k` → `SchemeSearchResponse` |

All relevant routes are in `main.py`; no separate router files.

### 4.3 Chat Flow (Logic in `main.py`)

1. **Context extraction (no LLM):**  
   `build_cumulative_context(conversation_history, current_message)` runs regex over every user message and the current one to fill:  
   `occupation`, `state`, `help_type`/`specific_need`, `gender`, `age`, `caste_category`, `education_level`, `income`, `bpl`, `disability`, `residence`, `family_status`.  
   Uses patterns for Indian states, occupations, NEED_PATTERNS (scholarship, loan, pension, etc.), caste, gender, age, BPL, disability, etc. Hindi “छात्रवृत्ति” maps to help_type scholarship.

2. **Readiness to recommend:**  
   `is_ready_to_recommend(user_ctx)` requires:  
   - `occupation`, `state`, `help_type`, and  
   - at least one of: `gender`, `age`, `caste_category`.  
   So at least four fields must be present before schemes are shown.

3. **RAG (only when ready):**  
   Builds `search_query` from query + context (occupation, state, gender, caste, education_level, specific_need, disability, bpl) and last 4 user messages.  
   Calls `rag_service.search_schemes(query, user_ctx, top_k=50)`.  
   Then `filter_schemes_for_user(raw, user_ctx)` applies hard filters: state, gender, caste, age, occupation, education (pre/post matric), disability, family status, farmer/senior/child-specific, and `_filter_by_need` (e.g. exclude loans when user asked for scholarship).  
   Up to 20 schemes returned; if filter removes all, fallback is top 20 from RAG.

4. **LLM response:**  
   `gemini_service.chat(user_message, conversation_history, matched_schemes, user_context, missing_fields, language)` builds the system prompt (personality, conversation flow, user profile, scheme list with Website URLs, language rules, no emojis, “include clickable link per scheme”) and calls either **OpenAI** (GPT 5.2) or **Gemini**.  
   Returns a single string; no separate “endpoint changes” for chat — only this one `/chat` flow.

5. **Response:**  
   `ChatResponse(message=reply, schemes=candidates if ready else [], needs_more_info=not ready, extracted_context=user_ctx)`.

### 4.4 RAG Service (`app/services/rag_service.py`)

- **Init:** Loads `all_schemes.json` via `data_loader`, creates or opens ChromaDB persistent client at `chroma_db/`, gets or creates collection `government_schemes` with **OpenAI embedding function** from `app.utils.embedding_function.get_embedding_function()` (text-embedding-3-large).  
- If collection count is 0, calls `_initialize_vector_db()`: for each scheme, `prepare_scheme_text_for_embedding(s)` → document text, then `collection.add(ids, documents, metadatas)` (embedding done by ChromaDB via OpenAI).  
- **search_schemes(query, user_context, top_k):** Builds `enhanced_query` with context, queries ChromaDB with `n_results` up to 50, converts distances to match_score, applies `SIMILARITY_THRESHOLD`, then `filter_schemes_by_eligibility` (state, gender, etc.).  
- Returns list of scheme dicts with `match_score` attached.

### 4.5 Embeddings (`app/utils/embedding_function.py` + ChromaDB)

- **Model:** OpenAI **text-embedding-3-large** (no Sentence Transformers).  
- **Usage:** `build_vectordb.py` and `rag_service` both use `get_embedding_function()` so index and query use the same model.  
- **Requirement:** `OPENAI_API_KEY` must be set; otherwise RAG init fails (or is skipped with empty schemes).

### 4.6 Building the Vector DB (`build_vectordb.py`)

- Reads `data_f/all_schemes.json`, filters by `data_quality_score >= MIN_QUALITY_SCORE` (30).  
- Prepares text per scheme (name, category, brief/detailed description, benefits, eligibility, state, occupation, etc.).  
- Uses **OpenAI embedding function**; creates collection with `embedding_function=...`.  
- **Batch:** 20 documents per batch; **delay 16 s** between batches to stay under OpenAI TPM (e.g. 40k tokens/min).  
- Writes to `chroma_db/`; can run with `fresh=True` to wipe and rebuild.  
- Test search at end uses same embedding function for query.

### 4.7 Data Enrichment (`enrich_data.py`)

- Reads `data_f/all_schemes.json`, backs up to `all_schemes_backup.json`.  
- For each scheme, re-derives from free text:  
  `state`, `occupation`, `benefit_type`, `gender`, `caste_category`, `age_range`  
  using regex and keyword rules so that filters (state, occupation, help_type, etc.) work correctly.  
- Writes back to `all_schemes.json`.  
- Used in pipeline after merge; can be run standalone.

### 4.8 Data Auto-Update Pipeline (`pipeline/`)

- **Config:** `pipeline_config.json`: scraping (category modules, resume, test_mode), merge (min_quality_score, prefer_newer_last_updated), enrichment (run), vectordb (rebuild), scheduler (enabled false, interval_hours 24, stop_file, heartbeat_file).  
- **Stages:** (1) Run category scrapers from `scraper.*`, (2) Merge new data into `data_f/all_schemes.json`, (3) Run `enrich_data.py`, (4) Run `build_vectordb.py`, (5) Write report to `pipeline/reports/`.  
- **Entry:** `run_data_update_pipeline.py` (one-shot), `run_data_update_daemon.py` (loop; only if `scheduler.enabled` true).  
- **Note:** Pipeline is **manual**; no cron or systemd. Daemon is **off** by default.

---

## 5. Frontend — Detailed Description

### 5.1 Stack

- **React** 18, **Vite** 6, **React Router** 7.  
- **Tailwind CSS** 3, **Framer Motion** 12, **Lucide React** icons.  
- **Axios** for API, **React Markdown** for AI messages, **React Hot Toast** for notifications.  
- **API base URL:** `import.meta.env.VITE_API_URL || 'http://localhost:8000'`.

### 5.2 Routes

- `/` → HomePage (landing).  
- `/chat` → ChatPage (new chat).  
- `/chat/:chatId` → ChatPage (existing conversation).  
- `*` → NotFound.

### 5.3 Chat Page & Components

- **ChatContainer:** Manages `messages`, `chats`, `currentChatId`, `isLoading`, `language`, `voiceEnabled`, `isSpeaking`, `voiceRef`. Sends full `conversation_history` (no slice) to `/chat`. On response, builds assistant message with `content: response.message`, `schemes: response.schemes` (array). Persists messages via `storage.saveMessageToChat`.  
- **ChatSidebar:** List of chats (from storage), New Chat, delete, “Back to Home”.  
- **ChatMessages:** Renders list of Message components + WelcomeScreen when no messages; TypingIndicator when loading.  
- **Message:** User bubble (text) or assistant bubble (ReactMarkdown for content; custom `<a>` for links: `target="_blank"`, blue underline). If `message.schemes?.length > 0`, renders “Schemes found for you” and up to 20 **SchemeCard** components. Speak button on assistant messages calls `onSpeak(message.content)`.  
- **SchemeCard:** Expand/collapse card: scheme name, category, benefit type, state, doc count, **Apply** link (and optional domain link) with `source_url` or `official_website`, eligibility preview; expanded: full eligibility, benefits, documents, application process, **View details** link. Uses `scheme.source_url || scheme.official_website` for clickable URL; `onClick` stopPropagation so link opens without toggling card.  
- **ChatInput:** Textarea, send button, **VoiceButton**. Uses `useVoice` for STT (transcript, silence-based auto-send), exposes `speak`/`stopSpeaking` via `onVoiceReady`. When listening: red/emerald ring, countdown pill, “Listening” badge, sound bars, floating overlay pill with transcript.  
- **LanguageToggle:** EN / हि; calls `onLanguageChange`.  
- **SpeakingIndicator:** Shown when TTS is active; Stop button.  
- **WelcomeScreen:** Suggestion chips from `SUGGESTIONS[language]` (en/hi).

### 5.4 Voice (`hooks/useVoice.js`)

- **STT:** `SpeechRecognition` / `webkitSpeechRecognition`, `continuous`, `interimResults`, `lang` en-IN or hi-IN. Transcript updates live; 5 s silence triggers `onFinalTranscript` (auto-send).  
- **TTS:** `SpeechSynthesisUtterance`; chunked for long text; Hindi: prefer `hi-IN` or “hindi” voice; clean markdown/URLs/emojis; `₹` → “रुपये” (hi) or “rupees” (en).  
- **Auto-speak:** When user sends via voice or when voice toggle is on, reply is spoken via `voiceRef.current.speak(response.message)`.

### 5.5 i18n (`utils/i18n.js`)

- `UI_TEXT` for en/hi: navbar, sidebar, chat placeholders, welcome, scheme cards (eligibility, documents, Apply, show more/less), errors, listening, etc.  
- `useTranslation(language)` returns `t` object.  
- Suggestion chips and scheme card labels use these so UI is bilingual.

### 5.6 Storage (`services/storage.js`)

- **Keys:** `scheme_saathi_chats`, `scheme_saathi_current_chat_id`, `scheme_saathi_language`.  
- Chats: array of `{ id, title, messages, createdAt, updatedAt }`.  
- `saveMessageToChat(chatId, message)` appends message (full object including `schemes`).  
- New chat title from first user message (truncated).

---

## 6. Data Model (Scheme)

Schemes in `all_schemes.json` (and API responses) are JSON objects. Main fields:

- **Identity:** `scheme_id`, `scheme_name`, `category`.  
- **Descriptions:** `brief_description`, `detailed_description`.  
- **Eligibility:** `eligibility_criteria` (object): `state`, `occupation`, `gender`, `caste_category`, `age_range`, `income_limit`, `raw_eligibility_text`, etc.  
- **Benefits:** `benefits` (object): `summary`, `financial_benefit`, `benefit_type`, `frequency`, `raw_benefits_text`.  
- **Application:** `required_documents`, `application_process`, `official_website`, `source_url`.  
- **Enrichment/quality:** `data_quality_score`; enriched fields may include normalized `state`, `occupation`, `benefit_type`, etc.

Vector DB stores one document per scheme: concatenation of name, category, descriptions, benefits summary, eligibility text, and key eligibility fields (from `data_loader.prepare_scheme_text_for_embedding`).

---

## 7. Environment & Runbooks

### 7.1 Backend

- **.env** (copy from `.env.example`):  
  `GEMINI_API_KEY`, `OPENAI_API_KEY`, `OPENAI_EMBEDDING_MODEL`, `OPENAI_CHAT_MODEL`, `GEMINI_MODEL`, paths, CORS, `TOP_K_SCHEMES`, `SIMILARITY_THRESHOLD`.  
- **Install:** `pip install -r requirements.txt` (fastapi, uvicorn, pydantic, pydantic-settings, google-generativeai, chromadb, openai, python-dotenv, httpx).  
- **Vector DB (first time or after data change):**  
  `cd backend && python build_vectordb.py` (requires `OPENAI_API_KEY`; uses batch 20, 16 s delay).  
- **Run server:**  
  `cd backend && python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`.  
- **Health:** `GET http://localhost:8000/health`.  
- **Docs:** `http://localhost:8000/docs`.

### 7.2 Frontend

- **Install:** `npm install`.  
- **Dev:** `npm run dev` (e.g. http://localhost:5173).  
- **Build:** `npm run build`; preview with `npm run preview`.  
- **API URL:** Set `VITE_API_URL` if backend is not at `http://localhost:8000`.

### 7.3 Pipeline (Optional)

- **One-shot:** `cd backend && python run_data_update_pipeline.py` (optionally `--dry-run`).  
- **Daemon (disabled by default):** Set `scheduler.enabled` true in `pipeline_config.json`, then `python run_data_update_daemon.py`. Stop with `backend/pipeline/.stop_daemon`.

---

## 8. Features Summary

| Feature | Where | Notes |
|--------|--------|------|
| Conversational scheme discovery | Backend + Frontend | Context from conversation; RAG + filters; up to 20 schemes per reply |
| Multi-language (EN/Hi) | Backend prompt + Frontend i18n | UI_TEXT, SUGGESTIONS, scheme card labels; LLM responds in selected language |
| Voice input | Frontend useVoice + ChatInput | Web Speech STT; live transcript; 5 s silence → auto-send |
| Voice output | Frontend useVoice + ChatContainer | TTS for replies (optional toggle); auto-speak when message was sent by voice |
| Scheme cards | Frontend SchemeCard + Message | Expand/collapse; Apply + domain link; eligibility, benefits, docs, process |
| Clickable scheme links | Backend prompt + SchemeCard | LLM instructed to include [Apply](url); cards use source_url/official_website |
| No emojis in LLM | Backend prompt | “Do not use emojis in your responses.” |
| Eligibility filtering | Backend main.py | State, gender, caste, age, occupation, education, disability, family, farmer/senior/child, help_type |
| RAG + embeddings | Backend rag_service + ChromaDB | OpenAI text-embedding-3-large; query enhanced with user context |
| Chat LLM | Backend gemini_service | OpenAI gpt-5.2-chat-latest when OPENAI_CHAT_MODEL set; else Gemini |
| Landing page | Frontend HomePage | Hero, Features, How It Works, Statistics, CTA, Footer |
| Chat persistence | Frontend storage.js | Chats and messages in localStorage; key scheme_saathi_chats |
| Data enrichment | Backend enrich_data.py | Re-extract structured fields from text for better filtering |
| Data pipeline | Backend pipeline/ | Scrape → merge → enrich → vectordb; manual; optional 24h daemon |

---

## 9. Testing & Scripts

- **Backend:** `check_backend.py`, `quick_smoke_test.py`, `test_api.py`, `test_config.py`, `test_context.py`, `test_data_loader.py`, `test_filters.py`, `test_fixes.py`, `test_gemini.py`, `test_models.py`, `test_rag.py`, `test_response.py`, `diagnose_matching.py`.  
- **Pipeline:** Reports under `backend/pipeline/reports/` (latest.json, run_*.json).

---

## 10. Security & Deployment Notes

- **API keys:** Stored in `.env`; not committed.  
- **CORS:** Backend allows all origins (`allow_origins=["*"]`); for production, restrict to frontend origin(s).  
- **Rate limits:** OpenAI embedding calls throttled in `build_vectordb.py` (batch size and delay); no application-level rate limiting on `/chat`.  
- **Data:** Scheme data is public government info; no PII stored beyond what the user types in chat (kept in browser localStorage only).

---

## 11. Dependencies (Exact Versions in Lockfiles)

**Backend (requirements.txt):**  
fastapi>=0.109.0, uvicorn[standard]>=0.27.0, pydantic>=2.5.0, pydantic-settings>=2.1.0, google-generativeai>=0.3.0, chromadb>=0.4.22, openai>=1.0.0, python-dotenv>=1.0.0, httpx>=0.26.0

**Frontend (package.json):**  
react 18.3.1, react-dom 18.3.1, react-router-dom 7.13.0, axios 1.7, framer-motion 12.34, lucide-react 0.460, react-hot-toast 2.6, react-markdown 9.0.1, vite 6.x, tailwindcss 3.4, @vitejs/plugin-react 4.3

---

## 12. Document History

- **v1.0:** Full project report: architecture, backend (config, endpoints, chat flow, RAG, embeddings, build_vectordb, enrichment, pipeline), frontend (routes, chat components, voice, i18n, storage), data model, env/runbooks, features table, testing, security, dependencies.
