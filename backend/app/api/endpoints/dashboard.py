from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.models.domain import Document
from app.schemas.domain import DashboardStats
from app.services.graph_service import get_neo4j

router = APIRouter()

@router.get("/", response_model=DashboardStats)
def get_dashboard_stats(db: Session = Depends(get_db)):
    total_docs = db.query(Document).count()
    recent_docs = db.query(Document).order_by(Document.upload_date.desc()).limit(5).all()
    
    conn = get_neo4j()
    
    eq_result = conn.query("MATCH (e:Equipment) RETURN count(e) as c")
    eq_count = eq_result[0]["c"] if eq_result else 0
    
    fail_result = conn.query("MATCH (f:Failure) RETURN count(f) as c")
    fail_count = fail_result[0]["c"] if fail_result else 0
    
    return DashboardStats(
        total_documents=total_docs,
        equipment_count=eq_count,
        failures_count=fail_count,
        recent_uploads=recent_docs
    )
