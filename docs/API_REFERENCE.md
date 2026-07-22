# IKIP API Reference

The FastAPI backend runs on `http://localhost:8000` and provides the following RESTful endpoints.

## 1. Documents API (`/api/v1/documents`)

### `POST /upload`
Uploads a new document for processing.
- **Body**: `multipart/form-data` containing `file`
- **Response**: Returns Document metadata and ID. Triggers a background parsing job.

### `GET /`
Retrieves a list of all uploaded documents and their processing status.
- **Response**: `[ { "id": 1, "filename": "pump_manual.pdf", "status": "completed" } ]`

## 2. AI Copilot API (`/api/v1/copilot`)

### `POST /chat`
Sends a query to the LangGraph RAG pipeline.
- **Body**: `{ "query": "What is the maintenance schedule for Pump A?" }`
- **Response**:
```json
{
  "answer": "Pump A should be inspected monthly.",
  "confidence_score": 0.92,
  "sources": [
    {
      "document_name": "pump_manual.pdf",
      "page_number": 12,
      "text_snippet": "Maintenance for Pump A requires..."
    }
  ]
}
```

## 3. Root Cause Analysis API (`/api/v1/rca`)

### `POST /analyze`
Generates a structured Root Cause Analysis for a specific industrial failure.
- **Body**: `{ "equipment": "Centrifugal Pump", "problem": "Excessive vibration during operation" }`
- **Response**:
```json
{
  "likely_causes": ["Misalignment", "Bearing wear"],
  "recommendations": ["Check alignment", "Replace bearings if worn"],
  "confidence": 0.88
}
```

## 4. Knowledge Graph API (`/api/v1/graph`)

### `GET /nodes`
Retrieves a visualizable representation of the Neo4j Knowledge Graph.
- **Response**: Returns React-Flow compatible `nodes` and `edges` arrays representing Equipment, Failures, and their relationships.

## 5. Dashboard API (`/api/v1/dashboard`)

### `GET /stats`
Retrieves system statistics for the homepage.
- **Response**: Returns document count, entity count, and recent activity logs.
