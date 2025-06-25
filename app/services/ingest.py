from app.utils.pdf_loader import load_and_split_pdf
from app.vector_store.qdrant_store import get_qdrant_vectorstore
from pprint import pprint
from langchain_core.documents import Document  # if not already

def ingest_pdf(file_path: str, user_id: str, document_id: str):
    chunks = load_and_split_pdf(file_path)
    for i, chunk in enumerate(chunks):
        chunk.metadata = {
            "user_id": user_id,
            "document_id": document_id,
            "page": chunk.metadata.get("page", 0)
        }
        print(f"✅ Chunk {i+1} metadata:", chunk.metadata)
        
    # for i, chunk in enumerate(chunks):
        # print(f"Chunk {i+1} Preview:\n", chunk.page_content[:300], "\n---")


    vectorstore = get_qdrant_vectorstore()

    try:
        print("📥 Adding documents to Qdrant vectorstore...")
        vectorstore.add_documents(chunks)
        print("✅ Successfully added to vectorstore.")
    except Exception as e:
        print("❌ Failed to add documents to Qdrant:", e)
        import traceback; traceback.print_exc()
        raise e

    return f"Ingested {len(chunks)} chunks."




# def ingest_pdf(file_path):
#     chunks = load_and_split_pdf(file_path)
#     vectorstore = get_qdrant_vectorstore()
#     vectorstore.add_documents(chunks)
#     return f"Ingested {len(chunks)} chunks."