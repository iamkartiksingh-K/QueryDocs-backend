from app.utils.pdf_loader import load_and_split_pdf
from app.vector_store.qdrant_store import get_qdrant_vectorstore
from concurrent.futures import ThreadPoolExecutor, as_completed
from app.core.config import QDRANT_BATCH_SIZE

def batch(iterable, batch_size):
    """Yield successive batches of specified size."""
    for i in range(0, len(iterable), batch_size):
        yield iterable[i:i + batch_size]

def insert_batch(batch, vectorstore):
    try:
        vectorstore.add_documents(batch)
        print(f"✅ Inserted batch of {len(batch)} chunks")
    except Exception as e:
        print("❌ Batch insert failed:", e)


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

    print("📥 Adding documents to Qdrant vectorstore...")
    batches = list(batch(chunks, QDRANT_BATCH_SIZE))

    try:
        with ThreadPoolExecutor(max_workers=4) as executor:  # You can tune workers
            futures = [executor.submit(insert_batch, b, vectorstore) for b in batches]
            for future in as_completed(futures):
                future.result()  # Raise if any exception occurred

        print("✅ Successfully added all batches to vectorstore.")
    except Exception as e:
        print("❌ Failed during parallel batch insert:", e)
        import traceback; traceback.print_exc()
        raise e

    return f"Ingested {len(chunks)} chunks."



# def ingest_pdf(file_path):
#     chunks = load_and_split_pdf(file_path)
#     vectorstore = get_qdrant_vectorstore()
#     vectorstore.add_documents(chunks)
#     return f"Ingested {len(chunks)} chunks."