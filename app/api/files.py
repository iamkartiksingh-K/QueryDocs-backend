from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from pathlib import Path
import shutil
import os
import requests
from app.models.user import User
from app.schemas.user import UserOut
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

@router.get("/load_document")
def load_user_documents_and_ingest(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_docs = db.query(Document).filter(Document.user_id == current_user.id).all()

    if not user_docs:
        raise HTTPException(status_code=404, detail="No documents found for this user.")

    temp_dir = Path("./temp").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)

    for doc in user_docs:
        file_name = doc.name
        file_url = doc.url
        temp_path = temp_dir / file_name

        # Download the PDF from Cloudinary
        response = requests.get(file_url)
        if response.status_code != 200:
            continue  # optionally log or raise for failures

        with open(temp_path, "wb") as f:
            f.write(response.content)

        # Ingest into vector DB
        try:
            ingest_pdf(temp_path.as_posix())
        except Exception as e:
            print(f"Ingestion failed for {file_name}: {e}")
            continue

    # Clean up all temp files
    try:
        for file in temp_dir.iterdir():
            file.unlink()
        temp_dir.rmdir()
    except Exception as e:
        print(f"Cleanup failed: {e}")

    return {"msg": f"Ingested {len(user_docs)} document(s) successfully."}