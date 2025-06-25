from celery_worker import celery_app
from app.services.ingest import ingest_pdf
import os

@celery_app.task(name="app.services.tasks.process_pdf_background")
def process_pdf_background(file_path: str, user_id: str, document_id: str):
    ingest_pdf(file_path, user_id, document_id)
    if os.path.exists(file_path):
        os.remove(file_path)
