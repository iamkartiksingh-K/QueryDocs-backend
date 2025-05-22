from app.utils.pdf_loader import load_and_split_pdf
from app.vector_store.qdrant_store import get_qdrant_vectorstore

def ingest_pdf(file_path):
    chunks = load_and_split_pdf(file_path)
    vectorstore = get_qdrant_vectorstore()
    vectorstore.add_documents(chunks)
    return f"Ingested {len(chunks)} chunks."