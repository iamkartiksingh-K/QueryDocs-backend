from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.core.config import GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY

COLLECTION_NAME = "docs"

def get_qdrant_vectorstore():
    # Step 1: Define embeddings
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )

    # Step 2: Connect to Qdrant Cloud
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30
    )

    # Step 3: Create the collection if it doesn't exist
    if COLLECTION_NAME not in [col.name for col in client.get_collections().collections]:
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )

    # Step 4: Return vectorstore
    return Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embeddings
    )
