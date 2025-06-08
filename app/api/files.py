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
