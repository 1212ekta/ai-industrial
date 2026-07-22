# Industrial Knowledge Intelligence Platform (IKIP)

An AI-powered Enterprise SaaS platform for parsing, extracting, and chatting with industrial documents using Large Language Models (LLMs), Vector Stores (Qdrant), and Knowledge Graphs (Neo4j).

## Features

- **Document Ingestion**: Upload PDF, DOCX, TXT, and Excel files.
- **Automated Processing**: Extract text, chunk data, generate embeddings.
- **Entity Extraction**: Identify Equipment, Failures, and Maintenance concepts.
- **Knowledge Graph**: Visualize relationships using Neo4j and React Flow.
- **AI Copilot (RAG)**: Chat with your industrial data using OpenAI and LangGraph.
- **Root Cause Analysis (RCA)**: Generate likely causes and recommendations.
- **Dashboard**: Track system metrics and recent uploads.

## Architecture

- **Frontend**: Next.js 15 (App Router), React 19, TypeScript, Tailwind CSS, shadcn/ui.
- **Backend**: FastAPI, Python 3.12, SQLAlchemy, SQLite, LangGraph.
- **Databases**:
  - **SQLite**: Relational metadata and tracking.
  - **Qdrant**: Vector database for RAG context retrieval.
  - **Neo4j**: Graph database for entity relationships.

## Screenshots

![Dashboard Placeholder](/screenshots/dashboard.png)
*(Placeholder for Dashboard)*

![Copilot Placeholder](/screenshots/copilot.png)
*(Placeholder for AI Copilot)*

## Prerequisites

- Docker and Docker Compose
- Node.js 20+ (if running frontend locally)
- Python 3.12+ (if running backend locally)
- OpenAI API Key

## Environment Variables

Create a `.env` file in the root directory (you can copy `.env.example`):

```env
OPENAI_API_KEY=your_openai_api_key
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password
QDRANT_URL=http://localhost:6333
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

The easiest way to run the full stack is using Docker Compose.

```bash
docker-compose up --build
```

This will start:
- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:8000
- **Neo4j Browser**: http://localhost:7474
- **Qdrant**: http://localhost:6333

### Running Locally (Development)

**Backend:**
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload
```

**Frontend:**
```bash
cd frontend
npm install
npm run dev
```

## License
MIT
