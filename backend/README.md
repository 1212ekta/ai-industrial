# IKIP Backend

FastAPI backend for the Industrial Knowledge Intelligence Platform: document
ingestion, AI entity extraction, knowledge graph (Neo4j), semantic search
(Qdrant), a RAG Copilot, and a LangGraph-based Root Cause Analysis agent.

## Stack

- Python 3.12, FastAPI, SQLAlchemy (async) + SQLite for MVP metadata
- OpenAI GPT-5.5 (chat) + `text-embedding-3-large` (embeddings)
- Qdrant (vector store), Neo4j (knowledge graph)
- PyMuPDF / pdfplumber / python-docx / pandas / PaddleOCR (parsing + OCR)
- LangGraph (RCA agent workflow)

## Quickstart (local, no Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
# edit .env: set OPENAI_API_KEY, and Qdrant/Neo4j URLs if not running locally

# Start Qdrant + Neo4j (or point at existing instances)
docker run -p 6333:6333 qdrant/qdrant
docker run -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/change-me neo4j:5.26-community

uvicorn app.main:app --reload
```

API docs: http://localhost:8000/docs
Health check: http://localhost:8000/health

## Quickstart (Docker Compose — backend + Qdrant + Neo4j)

```bash
cp .env.example .env   # set OPENAI_API_KEY at minimum
docker compose up --build
```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/documents/upload` | Upload a document (pdf/docx/txt/png/jpg/xlsx); kicks off async processing |
| GET | `/api/v1/documents` | List/filter documents |
| GET | `/api/v1/documents/{id}` | Document metadata + status |
| GET | `/api/v1/documents/{id}/file` | Download/stream original file |
| GET | `/api/v1/documents/{id}/chunks` | Chunk-level content + page numbers |
| DELETE | `/api/v1/documents/{id}` | Delete document + cascade cleanup (Qdrant, Neo4j) |
| GET | `/api/v1/entities?document_id=` | Extracted entities for a document |
| GET | `/api/v1/graph/equipment/{tag}` | Equipment subgraph (failures, maintainers, inspectors, vendors, docs) |
| GET | `/api/v1/graph/stats` | Node/edge counts |
| POST | `/api/v1/search` | Semantic search over chunks |
| POST | `/api/v1/copilot/chat` | RAG Q&A with citations + confidence |
| POST | `/api/v1/rca` | Root Cause Analysis (LangGraph agent) |
| GET | `/api/v1/dashboard/stats` | Summary stats + recent uploads/queries |

## Processing pipeline

Upload → background task: parse (PyMuPDF/pdfplumber/docx/pandas, PaddleOCR
fallback for scanned pages/images) → chunk (page-aware, ~500 tokens, 50 overlap)
→ embed (OpenAI) → upsert to Qdrant → LLM entity/relation extraction per chunk
→ write nodes/relationships to Neo4j → mark `indexed`.

Poll `GET /api/v1/documents/{id}` for `status`: `uploaded → parsing → embedding
→ extracting → indexed` (or `failed`, with `error_message` set).

## Notes on the MVP SQLite choice

`DocumentStatus` enum values are stored as plain strings (`native_enum=False`)
so the schema is portable to Postgres later with zero model changes — swap
`DATABASE_URL` to a `postgresql+asyncpg://...` DSN and rerun.

## Known MVP limitations (by design, for hackathon scope)

- No auth layer yet (all endpoints are open) — add JWT middleware from
  `app/core/config.py`'s `secret_key` before any real deployment.
- Background tasks use FastAPI's in-process `BackgroundTasks`, not a durable
  queue — fine for a demo, swap for Celery/RQ + Redis for production.
- Entity resolution across documents is best-effort (string normalization),
  not a full entity-resolution/dedup pipeline.
