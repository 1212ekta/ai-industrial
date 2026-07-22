import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import Base, engine
from app.services.graph_service import init_graph_schema

# Create storage directories
os.makedirs("storage/uploads", exist_ok=True)
os.makedirs("storage/db", exist_ok=True)

# Create sqlite tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Industrial Knowledge Intelligence Platform (IKIP)",
    description="API for IKIP MVP",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    # Initialize Neo4j constraints
    init_graph_schema()

@app.get("/")
def read_root():
    return {"message": "Welcome to IKIP API"}

from app.api.endpoints import documents, search, copilot, rca, dashboard, graph

app.include_router(documents.router, prefix="/documents", tags=["documents"])
app.include_router(search.router, prefix="/search", tags=["search"])
app.include_router(copilot.router, prefix="/copilot", tags=["copilot"])
app.include_router(rca.router, prefix="/rca", tags=["rca"])
app.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
app.include_router(graph.router, prefix="/graph", tags=["graph"])
