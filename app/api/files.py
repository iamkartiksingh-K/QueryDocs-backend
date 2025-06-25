from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path as pp
import shutil
import os
from datetime import datetime, timezone
from app.models.user import User
from app.schemas.document import DocumentOut
from app.models.document import Document
from app.utils.security import get_current_user
from app.services.cloudinary_service import upload_pdf_to_cloudinary, get_cloudinary_signature, delete_pdf_from_cloudinary
from app.services.ingest import ingest_pdf
from app.services.query import query_with_context
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import Query
from fastapi import Path as fp
from uuid import UUID
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.vector_store.qdrant_store import get_qdrant_client
from app.services.tasks import process_pdf_background

router = APIRouter()

def format_file_size(size_in_bytes) -> str:
    try:
        size_in_bytes = int(size_in_bytes)
    except (ValueError, TypeError):
        return "Unknown size"
    size_kb = size_in_bytes / 1024
    if size_kb >= 1000:
        return f"{size_kb / 1024:.2f} MB"
    return f"{size_kb:.2f} KB"


@router.post("/upload/", response_model=DocumentOut)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    temp_dir = pp("./temp").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename

    # 🔽 Save file locally
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    file_size = os.path.getsize(temp_path)

    # 🔽 Upload to Cloudinary
    try:
        cloud_url = upload_pdf_to_cloudinary(str(temp_path))
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # 🔽 Save metadata to DB
    new_doc = Document(
        name=file.filename,
        url=cloud_url,
        user_id=current_user.id,
        size=file_size,
        created=datetime.now(timezone.utc).strftime("%d %B %Y")
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # ✅ Send to Celery in background
    try:
        process_pdf_background.delay(str(temp_path), str(current_user.id), str(new_doc.document_id))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to trigger background processing: {str(e)}")

    return new_doc

@router.get("/ask/")
def ask_question(
    query: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = query_with_context(query, str(current_user.id))
    return result

@router.get("/get-signature")
def get_signature():
    return get_cloudinary_signature()

@router.get("/search")
def search_user_documents_route(
    keyword: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    from app.services.search_service import search_user_documents
    results = search_user_documents(db, str(current_user.id), keyword)
    return {
        "results": [
            {
                "document_id": str(doc.document_id),
                "name": doc.name,
                "url": doc.url,
                "size": format_file_size(doc.size),
                "created": doc.created
            } for doc in results
        ]
    }

@router.get("/load-documents")
def get_user_documents(
    page: int = Query(1, ge=1),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    page_size = 10
    offset = (page - 1) * page_size

    documents = (
        db.query(Document)
        .filter(Document.user_id == current_user.id)
        .order_by(Document.created.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "page": page,
        "page_size": page_size,
        "results": [
            {
                "document_id": str(doc.document_id),
                "name": doc.name,
                "url": doc.url,
                "size": format_file_size(doc.size),
                "created": doc.created
            }
            for doc in documents
        ]
    }

@router.delete("/delete-documents/{doc_id}")
def delete_document(
    doc_id: UUID = fp(..., description="UUID of the document to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    document = db.query(Document).filter(
        Document.document_id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    try:
        delete_pdf_from_cloudinary(document.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from Cloudinary: {e}")

    try:
        qdrant = get_qdrant_client()
        qdrant.delete(
            collection_name="docs",
            points_selector=Filter(
                must=[FieldCondition(key="metadata.document_id", match=MatchValue(value=str(doc_id)))]
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from Qdrant: {e}")

    try:
        db.delete(document)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from DB: {e}")

    return {"message": "✅ Document and related data deleted successfully."}
