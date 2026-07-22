from fastapi import APIRouter, UploadFile, File, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
import os
import shutil

from app.db.database import get_db
from app.models.domain import Document, Chunk
from app.schemas.domain import DocumentResponse
from app.services.document_parser import parse_document
from app.services.embeddings import embed_and_store_chunks
from app.services.llm_service import extract_entities
from app.services.graph_service import insert_entities

router = APIRouter()

UPLOAD_DIR = "storage/uploads"

def process_document_background(document_id: int, file_path: str, file_type: str, filename: str, db: Session):
    try:
        # Update status to processing
        doc = db.query(Document).filter(Document.id == document_id).first()
        doc.status = "processing"
        db.commit()

        # Parse document
        parsed_chunks = parse_document(file_path, file_type)
        
        # Save chunks to SQLite
        for idx, chunk_data in enumerate(parsed_chunks):
            db_chunk = Chunk(
                document_id=document_id,
                page_number=chunk_data["page_number"],
                text=chunk_data["text"],
                chunk_index=idx
            )
            db.add(db_chunk)
        db.commit()

        # Generate Embeddings and store in Qdrant
        embed_and_store_chunks(document_id, filename, parsed_chunks)

        # Entity Extraction and Knowledge Graph
        # Process up to 10 chunks to avoid extreme token usage for MVP
        chunks_to_process = parsed_chunks[:10]
        for chunk in chunks_to_process:
            entities = extract_entities(chunk["text"])
            if entities:
                insert_entities(document_id, entities)

        # Update status to completed
        doc.status = "completed"
        db.commit()

    except Exception as e:
        print(f"Error processing document {document_id}: {e}")
        doc = db.query(Document).filter(Document.id == document_id).first()
        if doc:
            doc.status = "error"
            db.commit()


@router.post("/upload", response_model=DocumentResponse)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    db_doc = Document(
        filename=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        status="uploaded"
    )
    db.add(db_doc)
    db.commit()
    db.refresh(db_doc)
    
    background_tasks.add_task(
        process_document_background, 
        db_doc.id, 
        file_path, 
        file.content_type, 
        file.filename,
        db
    )
    
    return db_doc

@router.get("/", response_model=List[DocumentResponse])
def get_documents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents

@router.delete("/{document_id}")
def delete_document(document_id: int, db: Session = Depends(get_db)):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    # We should also delete from Qdrant and Neo4j ideally
    db.delete(doc)
    db.commit()
    return {"status": "success"}
