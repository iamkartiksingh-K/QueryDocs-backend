from langchain_community.vectorstores import Qdrant
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from app.core.config import GOOGLE_API_KEY, QDRANT_URL, QDRANT_API_KEY

def get_qdrant_vectorstore():
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GOOGLE_API_KEY
    )

    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY if QDRANT_API_KEY else None
    )

    return Qdrant(
        client=client,
        collection_name="docs",
        embeddings=embeddings
    )
