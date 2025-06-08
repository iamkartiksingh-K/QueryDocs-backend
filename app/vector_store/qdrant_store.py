from langchain_community.vectorstores import Qdrant  # ✅ use community version for now
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams
from app.core.config import GEMINI_API_KEY, QDRANT_URL, QDRANT_API_KEY

COLLECTION_NAME = "docs"

def get_qdrant_vectorstore():
    print("🔧 Initializing embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="models/embedding-001",
        google_api_key=GEMINI_API_KEY
    )

    print("🌐 Connecting to Qdrant...")
    client = QdrantClient(
        url=QDRANT_URL,
        api_key=QDRANT_API_KEY,
        timeout=30
    )

    print("📦 Checking existing collections...")
    existing_collections = [col.name for col in client.get_collections().collections]
    print("➡️ Collections found:", existing_collections)

    if COLLECTION_NAME not in existing_collections:
        print("🆕 Creating new collection:", COLLECTION_NAME)
        client.recreate_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(size=768, distance=Distance.COSINE)
        )

    print("🔍 Creating metadata indexes for filtering...")
    try:
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="user_id",  # ✅ field names as stored in `Document.metadata`
            field_schema="keyword"
        )
        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name="document_id",
            field_schema="keyword"
        )
    except Exception as e:
        print("⚠️ Index creation warning:", e)

    print("✅ Returning Qdrant vectorstore object")
    return Qdrant(
        client=client,
        collection_name=COLLECTION_NAME,
        embeddings=embeddings
    )
