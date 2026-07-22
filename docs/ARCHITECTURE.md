# IKIP Architecture

The Industrial Knowledge Intelligence Platform (IKIP) is designed as a modern, decoupled microservices architecture utilizing cutting-edge AI technologies for RAG and Knowledge Graph generation.

## High-Level Architecture

The system is composed of two primary layers:
1. **Frontend Presentation Layer**: Built with Next.js 15 (App Router).
2. **Backend AI & API Layer**: Built with FastAPI and LangGraph.

## Flow of Data (Ingestion Pipeline)
When a user uploads a document (PDF, DOCX, TXT):
1. **Parser**: The FastAPI background task reads the file using PyMuPDF/python-docx and chunks the text.
2. **Vectorization**: Chunks are embedded using OpenAI's `text-embedding-3-small` and stored in **Qdrant** for semantic retrieval.
3. **Graph Generation**: Chunks are sent to GPT-3.5/4 with structured JSON schemas to extract industrial entities (Equipment, Vendors, Failures).
4. **Graph Persistence**: Extracted entities are mapped to nodes and edges in **Neo4j** using Cypher queries.

## Flow of Data (AI Copilot / RAG)
When a user asks a question in the Copilot:
1. **Planner**: LangGraph analyzes the query to extract vector search terms and graph node entities.
2. **Retriever**:
   - Fetches semantically similar chunks from Qdrant.
   - Fetches structural relationships for the mentioned equipment from Neo4j.
3. **Generator**: GPT synthesizes the contexts into a deterministic answer.
4. **Response**: Returns the answer, confidence score, and exact document citations to the user interface.

## Tech Stack
- **Frontend**: Next.js 15, React 19, TailwindCSS, shadcn/ui, Framer Motion, React Flow.
- **Backend**: FastAPI, Python 3.12, SQLAlchemy, LangGraph.
- **Databases**: SQLite (Relational), Qdrant (Vector), Neo4j (Graph).
- **Orchestration**: Docker Compose.
