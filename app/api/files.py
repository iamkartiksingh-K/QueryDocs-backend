from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
import shutil
import os
from app.models.user import User
from app.schemas.document import DocumentOut
from app.models.document import Document
from app.utils.security import get_current_user
from app.services.cloudinary_service import upload_pdf_to_cloudinary, get_cloudinary_signature
from app.services.ingest import ingest_pdf
from app.services.query import query_with_context
from app.database import get_db
from sqlalchemy.orm import Session
from fastapi import Query 
from uuid import UUID
from fastapi import Path
from qdrant_client.models import Filter, FieldCondition, MatchValue
from app.services.cloudinary_service import delete_pdf_from_cloudinary
from app.vector_store.qdrant_store import get_qdrant_client


router = APIRouter()

@router.post("/upload/", response_model=DocumentOut)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Save temporarily
    temp_dir = Path("./temp").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Upload to Cloudinary
    try:
        cloud_url = upload_pdf_to_cloudinary(str(temp_path))
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # Save doc in DB
    new_doc = Document(
        name=file.filename,
        url=cloud_url,
        user_id=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    # Ingest into Qdrant with metadata
    try:
        ingest_pdf(str(temp_path), str(current_user.id), str(new_doc.document_id))
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    os.remove(temp_path)
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
                "url": doc.url
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
        .order_by(Document.document_id)
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
                "url": doc.url
            }
            for doc in documents
        ]
    }

@router.delete("/delete-documents/{doc_id}")
def delete_document(
    doc_id: UUID = Path(..., description="UUID of the document to delete"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # 1. Fetch the document
    document = db.query(Document).filter(
        Document.document_id == doc_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # 2. Delete from Cloudinary
    try:
        delete_pdf_from_cloudinary(document.url)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from Cloudinary: {e}")

    # 3. Delete related chunks from Qdrant
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

    # 4. Delete from database
    try:
        db.delete(document)
        db.commit()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete from DB: {e}")

    return {"message": "✅ Document and related data deleted successfully."}