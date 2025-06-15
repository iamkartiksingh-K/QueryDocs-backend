# app/services/search_service.py
from sqlalchemy.orm import Session
from app.models.document import Document
from fastapi import HTTPException
from uuid import UUID


def search_user_documents(db: Session, user_id: str, keyword: str):
    try:
        # Convert user_id to UUID object before filtering
        user_uuid = UUID(user_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID format.")

    # Case-insensitive partial match on filename
    results = db.query(Document).filter(
        Document.user_id == user_uuid,
        Document.name.ilike(f"%{keyword}%")
    ).all()

    return results