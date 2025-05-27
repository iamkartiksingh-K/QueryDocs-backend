from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
import shutil
import os

from sqlalchemy.orm import Session
from app.database import get_db
from app.services.ingest import ingest_pdf
from app.services.query import query_with_context
from app.services.cloudinary_service import upload_pdf_to_cloudinary, get_cloudinary_signature
from app.models.document import Document
from app.schemas.document import DocumentOut
from app.utils.security import get_current_user # adjust if different

router = APIRouter()


@router.post("/upload/", response_model=DocumentOut)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user)
):
    # Step 1: Save file temporarily
    temp_dir = Path("./temp").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)
    temp_path = temp_dir / file.filename

    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Step 2: Upload to Cloudinary
    try:
        cloud_url = upload_pdf_to_cloudinary(str(temp_path))
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Cloudinary upload failed: {str(e)}")

    # Step 3: Ingest into vector DB (RAG pipeline)
    try:
        ingest_pdf(temp_path.as_posix())
    except Exception as e:
        os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Ingestion failed: {str(e)}")

    # Step 4: Clean up local file
    os.remove(temp_path)

    # Step 5: Save in DB
    new_doc = Document(
        name=file.filename,
        url=cloud_url,
        user_id=current_user.id
    )
    db.add(new_doc)
    db.commit()
    db.refresh(new_doc)

    return new_doc


@router.get("/ask/")
def ask_question(query: str):
    result = query_with_context(query)
    return result


@router.get("/get-signature")
def get_signature():
    return get_cloudinary_signature()
