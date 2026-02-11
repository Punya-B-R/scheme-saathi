# Scheme Saathi Backend

AI-powered government scheme discovery chatbot for Indian citizens.

## Features

- 🤖 Conversational AI using Google Gemini
- 🔍 Semantic search with ChromaDB (RAG)
- 📊 4000+ government schemes from MyScheme.gov.in
- 🌐 Multi-language support (English, Hindi)
- ⚡ Fast, accurate scheme matching

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure environment

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Get your Gemini API key from: https://makersuite.google.com/app/apikey

Add it to `.env`:

```
GEMINI_API_KEY=your_actual_key_here
```

### 3. Run the server

From the `backend/` directory:

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Or from project root:

```bash
cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

API docs: http://localhost:8000/docs

## Project structure

```
backend/
├── app/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Configuration & env
│   ├── models.py         # Pydantic request/response schemas
│   ├── services/
│   │   ├── gemini_service.py   # Gemini AI
│   │   ├── rag_service.py      # ChromaDB + RAG
│   │   └── scheme_matcher.py   # Filtering & matching
│   └── utils/
│       └── data_loader.py      # Load all_schemes.json
├── data_f/
│   └── all_schemes.json
├── chroma_db/            # Auto-created by ChromaDB
├── requirements.txt
├── .env
├── .env.example
└── README.md
```

## API endpoints

| Method | Endpoint        | Description                    |
|--------|-----------------|--------------------------------|
| GET    | /health         | Health check                  |
| POST   | /chat           | Chat with AI (returns reply + suggested schemes) |
| POST   | /search         | Semantic scheme search        |
| GET    | /schemes/categories | List all categories      |

## Data

Scheme data is loaded from `data_f/all_schemes.json` at startup. ChromaDB indexes are stored in `chroma_db/` (created automatically on first run).
