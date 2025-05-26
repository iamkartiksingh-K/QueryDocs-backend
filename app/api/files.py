from fastapi import APIRouter, UploadFile, File
from app.services.ingest import ingest_pdf
from app.services.query import query_with_context
from app.services.cloudinary_service import get_cloudinary_signature
from pathlib import Path

router = APIRouter()


@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    temp_dir = Path("./temp").resolve()
    temp_dir.mkdir(parents=True, exist_ok=True)  # Ensure the directory exists

    file_path = f"{temp_dir}/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Convert to string with forward slashes (POSIX-style) for PyPDFLoader
    return {"msg": ingest_pdf(Path(file_path).as_posix())}



@router.get("/ask/")
def ask_question(query: str):
    result = query_with_context(query)
    return result


@router.get("/get-signature")
def get_signature():
    return get_cloudinary_signature()

