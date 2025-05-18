from fastapi import APIRouter, UploadFile, File
from app.services.ingest import ingest_pdf
from app.services.query import query_with_context

router = APIRouter()

@router.post("/upload/")
async def upload_pdf(file: UploadFile = File(...)):
    file_path = f"./temp/{file.filename}"
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"msg": ingest_pdf(file_path)}

@router.get("/ask/")
def ask_question(query: str):
    result = query_with_context(query)
    return result
