from langchain_openai import OpenAIEmbeddings
from qdrant_client.models import PointStruct
from app.db.qdrant import get_qdrant
from app.core.config import settings
import uuid

embeddings_model = OpenAIEmbeddings(openai_api_key=settings.OPENAI_API_KEY)
qdrant_client = get_qdrant()
collection_name = "ikip_chunks"

def embed_and_store_chunks(document_id: int, filename: str, chunks: list):
    points = []
    texts = [chunk["text"] for chunk in chunks]
    
    if not texts:
        return
        
    embeddings = embeddings_model.embed_documents(texts)
    
    for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "document_id": document_id,
                    "filename": filename,
                    "page_number": chunk["page_number"],
                    "chunk_index": i,
                    "text": chunk["text"]
                }
            )
        )
    
    qdrant_client.upsert(
        collection_name=collection_name,
        points=points
    )

def search_chunks(query: str, limit: int = 5):
    query_vector = embeddings_model.embed_query(query)
    results = qdrant_client.search(
        collection_name=collection_name,
        query_vector=query_vector,
        limit=limit
    )
    return results
